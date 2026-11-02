"""Future, in-memory Smart Tagging contract. No files or restricted loaders are opened.

Intervals are fallible phase context, never possession labels or exact restart timestamps.
"""
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class PhaseInterval:
    start: int
    stop: int
    code: str
    team_hint: str | None
    half: int | None
    tags: tuple[tuple[str, str], ...]
    confidence: float | None = None


class PhaseContextProvider(Protocol):
    def intervals(self) -> Sequence[PhaseInterval]: ...


def from_public_loader_records(records, period, fps, team_mapping: Mapping[str, str]):
    """Translate future loader-shaped records supplied in memory; tests use fictional examples.

    Confidence is unknown unless provided separately by a future validated source. Conflicting
    intervals are preserved, not resolved by last-write-wins. This function emits no labels.
    """
    if fps <= 0 or not np.isfinite(fps):
        raise ValueError("positive finite fps required")
    period = np.asarray(period)
    if period.ndim != 1 or not len(period) or not np.issubdtype(period.dtype, np.integer):
        raise ValueError("explicit integer period axis required")
    mapping = {k.strip().casefold(): v for k, v in team_mapping.items()}
    if not set(mapping.values()) <= {"H", "A"}:
        raise ValueError("team mapping must explicitly map source names to H/A")
    output = []
    for record in records:
        begin, end = float(record["start_s"]), float(record["end_s"])
        if not np.isfinite([begin, end]).all() or begin < 0 or end <= begin:
            raise ValueError("invalid phase time interval")
        start, stop = round(begin * fps), round(end * fps)
        if not 0 <= start < stop <= len(period):
            raise ValueError("phase interval falls outside the supplied video timeline")
        tags = {str(k).strip().casefold(): str(v).strip() for k, v in record.get("tags", {}).items()}
        raw_team = tags.get("team", "").casefold()
        team = None if raw_team in ("", "n/a") else mapping.get(raw_team)
        if raw_team not in ("", "n/a") and team is None:
            raise ValueError("unmapped team value; supply an explicit source-to-side mapping")
        half_name = tags.get("half", "").casefold()
        half = {"1st half": 1, "2nd half": 2, "": None}.get(half_name)
        if half_name and half is None:
            raise ValueError("unknown half tag")
        active = period[start:stop]
        if half is not None and np.any((active > 0) & (active != half)):
            raise ValueError("phase half disagrees with supplied period axis")
        confidence = record.get("confidence")
        if confidence is not None and (not np.isfinite(confidence) or not 0 <= confidence <= 1):
            raise ValueError("invalid optional source confidence")
        output.append(PhaseInterval(start, stop, str(record.get("code", "")).strip().casefold(),
                                    team, half, tuple(sorted(tags.items())), confidence))
    return tuple(output)
