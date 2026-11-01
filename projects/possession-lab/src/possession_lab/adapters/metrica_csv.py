"""Adapter for public Sample Games 1/2's three-header CSVs, explicitly not challenge ATD."""
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..schema import TrackingBatch, to_metres


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _read(path, side, max_frames=None):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        teams, shirts, header = next(reader), next(reader), next(reader)
    if header[:3] != ["Period", "Frame", "Time [s]"]:
        raise ValueError("not a public Metrica three-header tracking CSV")
    players = [i for i, name in enumerate(header) if name.startswith("Player")]
    if not players or any(teams[i].strip().lower() != side.lower() for i in players):
        raise ValueError("team side/header mismatch")
    if header[-2:] != ["Ball", ""] or any(header[i + 1] != "" for i in players):
        raise ValueError("expected paired x/y player and ball columns")
    table = pd.read_csv(path, skiprows=3, header=None, nrows=max_frames, dtype=float)
    if table.shape[1] != len(header):
        raise ValueError("tracking row width does not match header")
    values = table.to_numpy()
    xyz = np.stack([values[:, i:i + 2] for i in players], axis=1)
    return values[:, :3], xyz, values[:, -2:]


@dataclass(frozen=True)
class MetricaCSVAdapter:
    home_path: Path
    away_path: Path
    max_frames: int | None = None
    pitch: tuple = (105.0, 68.0)
    fps: float = 25.0

    def load(self):
        hm, home, hb = _read(self.home_path, "Home", self.max_frames)
        am, away, ab = _read(self.away_path, "Away", self.max_frames)
        if hm.shape != am.shape or not np.array_equal(hm, am):
            raise ValueError("home/away frame, timestamp or period axes do not agree")
        if not len(hm) or not np.isfinite(hm).all() or not np.equal(hm[:, :2], np.floor(hm[:, :2])).all():
            raise ValueError("finite integer source periods/frames required")
        frames = hm[:, 1].astype(int)
        if not np.array_equal(frames, np.arange(frames[0], frames[0] + len(frames))):
            raise ValueError("source frames are not contiguous; explicit reindexing is required")
        if len(hm) > 1 and not np.allclose(np.diff(hm[:, 2]), 1 / self.fps, atol=1e-5):
            raise ValueError("sample timestamps disagree with configured fps")
        both = np.isfinite(hb).all(axis=1) & np.isfinite(ab).all(axis=1)
        if not np.allclose(hb[both], ab[both], atol=1e-6):
            raise ValueError("home/away ball observations conflict")
        # Use complete pairs only; never synthesize one xy pair from unrelated partial observations.
        ball = hb.copy()
        missing = ~np.isfinite(ball).all(axis=1)
        ball[missing] = ab[missing]
        ball[~np.isfinite(ball).all(axis=1)] = np.nan
        provenance = {"kind": "public_sample", "source_frame_start": int(frames[0]),
                      "source": "https://github.com/metrica-sports/sample-data",
                      "home_sha256": digest(self.home_path), "away_sha256": digest(self.away_path),
                      "label_status": "unlabelled; no event-derived ground truth"}
        return TrackingBatch(np.arange(len(hm)), hm[:, 2], hm[:, 0].astype(int),
                             to_metres(ball, self.pitch), to_metres(home, self.pitch),
                             to_metres(away, self.pitch), self.pitch, self.fps, provenance)
