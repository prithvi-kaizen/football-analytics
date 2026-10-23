"""Pinned downloads, source validation and streaming DFL XML parsing."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/source/figshare-v1.json"
FPS = 25
PARSER_VERSION = 1


def analysis_fingerprint() -> str:
    h = hashlib.sha256()
    for name in ["data.py", "baseline.py", "geometry.py", "pipeline.py"]:
        h.update(name.encode())
        h.update((ROOT / "rest_defence" / name).read_bytes())
    return h.hexdigest()


def digest(path: Path, algorithm="sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_files(match: str) -> dict:
    entries = json.loads(MANIFEST.read_text())["files"]
    result = {}
    for key, token in [("meta", "matchinformation"), ("events", "events_raw"), ("tracking", "positions_raw")]:
        matches = [f for f in entries if token in f["name"] and f"DFL-MAT-{match}.xml" in f["name"]]
        if len(matches) != 1:
            raise ValueError(f"Unknown or ambiguous source match: {match}")
        result[key] = matches[0]
    return result


def fetch_file(entry: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and digest(path, "md5") == entry["computed_md5"]:
        return path
    part = path.with_suffix(".part")
    try:
        with requests.get(entry["download_url"], stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            with part.open("wb") as out:
                for chunk in response.iter_content(1024 * 1024):
                    out.write(chunk)
        if part.stat().st_size != entry["size"] or digest(part, "md5") != entry["computed_md5"]:
            raise ValueError(f"Source size/checksum mismatch: {entry['name']}")
        os.replace(part, path)
    finally:
        part.unlink(missing_ok=True)
    return path


def download_sample(path: Path) -> Path:
    """Fetch exact original byte ranges for ALL entities, not a file prefix."""
    index = json.loads((ROOT / "docs/source/sample-ranges.json").read_text())
    if path.exists() and digest(path) == index["sample_sha256"]:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".part")
    try:
        with part.open("wb") as out:
            out.write(index["prefix"].encode())
            for span in index["ranges"]:
                start, end = span["start"], span["end"]
                response = requests.get(index["url"] + f"?range_start={start}",
                                        headers={"Range": f"bytes={start}-{end}"}, timeout=(20, 120))
                response.raise_for_status()
                if response.status_code != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{index['source_size']}":
                    raise ValueError("Server did not honor exact byte range; refusing a full download in sample mode")
                payload = response.content
                if hashlib.sha256(payload).hexdigest() != span["sha256"]:
                    raise ValueError("Sample byte-range checksum mismatch")
                out.write(span["header"].encode())
                out.write(payload)
                out.write(b"</FrameSet>\n")
            out.write(index["suffix"].encode())
        if digest(part) != index["sample_sha256"]:
            raise ValueError("Reconstructed sample checksum mismatch")
        os.replace(part, path)
    finally:
        part.unlink(missing_ok=True)
    return path


def acquire(match="J03WPY", sample=False, bundled=False, cache: Path | None = None) -> dict:
    cache = Path(cache or ROOT / "data/raw")
    entries = source_files(match)
    if (sample or bundled) and match != "J03WPY":
        raise ValueError("The verified three-minute sample is available for J03WPY only")
    paths = {}
    for key, entry in entries.items():
        path = cache / f"{match}_{key}{'_sample' if key == 'tracking' and (sample or bundled) else ''}.xml"
        if bundled:
            sample_dir = ROOT / "data/sample"
            source = sample_dir / f"{key}.xml.gz"
            expected = json.loads((sample_dir / "manifest.json").read_text())["files"][key]
            if digest(source) != expected["gzip_sha256"]:
                raise ValueError("Bundled sample integrity failure")
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or digest(path) != expected["xml_sha256"]:
                path.write_bytes(gzip.decompress(source.read_bytes()))
        elif key == "tracking" and sample:
            download_sample(path)
        else:
            fetch_file(entry, path)
        paths[key] = path
    return paths


def metadata(path: Path) -> dict:
    root = ET.parse(path).getroot()
    general = root.find(".//General").attrib
    env = root.find(".//Environment").attrib
    teams, players = {}, {}
    for team in root.findall(".//Teams/Team"):
        a = team.attrib
        teams[a["TeamId"]] = dict(name=a["TeamName"], role=a["Role"])
        for p in team.findall("Players/Player"):
            a = p.attrib
            players[a["PersonId"]] = dict(team=team.attrib["TeamId"], name=a["Shortname"],
                                          number=a["ShirtNumber"], is_gk=a.get("PlayingPosition") == "TW")
    if len(teams) != 2:
        raise ValueError("Expected two teams")
    return dict(match_id=general["MatchId"].split("-")[-1], title=general["MatchTitle"],
                length=float(env["PitchX"]), width=float(env["PitchY"]), teams=teams, players=players,
                possession_map={1: general["HomeTeamId"], 2: general["GuestTeamId"]})


def utc_seconds(value: str) -> float:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("Timestamp must include UTC offset")
    return stamp.timestamp()


def parse_events(path: Path, meta: dict) -> tuple[pd.DataFrame, dict]:
    root = ET.parse(path).getroot()
    records, halves = [], {}
    for event in root.findall("Event"):
        if event.attrib.get("MatchId", "").split("-")[-1] != meta["match_id"]:
            raise ValueError("Event match ID mismatch")
        if not len(event) or event[0].tag == "Delete":
            continue
        action = event[0]
        a = action.attrib
        t = utc_seconds(event.attrib["EventTime"])
        if action.tag == "KickOff" and a.get("GameSection"):
            halves.setdefault(a["GameSection"], {}).update(start=t, left=a["TeamLeft"], right=a["TeamRight"])
        if action.tag == "FinalWhistle":
            halves.setdefault(a["GameSection"], {})["end"] = t
        records.append(dict(event_id=event.attrib["EventId"], time=t, kind=action.tag,
                            team=a.get("Team", a.get("WinnerTeam")), player=a.get("Player", a.get("Winner")),
                            xg=float(a["xG"]) if a.get("xG") else np.nan,
                            corrected_frame=int(event.attrib["CalculatedFrame"]) if event.attrib.get("CalculatedFrame") else np.nan))
    for period in ["firstHalf", "secondHalf"]:
        h = halves.get(period, {})
        if not {"start", "end", "left", "right"} <= h.keys() or h["end"] <= h["start"]:
            raise ValueError(f"Missing/invalid half boundary: {period}")
        if {h["left"], h["right"]} != set(meta["teams"]):
            raise ValueError("Invalid attacking directions")
    df = pd.DataFrame(records).sort_values(["time", "event_id"]).reset_index(drop=True)
    if df.event_id.duplicated().any():
        raise ValueError("Duplicate event IDs")
    df["period"] = None
    for period, half in halves.items():
        df.loc[df.time.between(half["start"], half["end"]), "period"] = period
    return df, halves


def attack_sign(meta: dict, halves: dict, team: str, period: str) -> int:
    if team not in meta["teams"] or period not in halves:
        raise ValueError("Unknown team/half")
    return 1 if halves[period]["left"] == team else -1


def orient(xy, sign: int):
    if sign not in (-1, 1):
        raise ValueError("Direction must be +1 or -1")
    return np.asarray(xy, dtype=float) * sign


def parse_tracking(path: Path, meta: dict, stride=5) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if stride < 1 or FPS % stride:
        raise ValueError("Stride must divide 25 Hz")
    players, balls = [], []
    audit = dict(source_rows=0, invalid_coordinates=0, unknown_entities=0, inactive_ball_rows=0)
    context, frame_set = None, None
    for event, elem in ET.iterparse(path, events=("start", "end")):
        if event == "start" and elem.tag == "FrameSet":
            context = elem.attrib.copy()
            frame_set = elem
            if context["MatchId"].split("-")[-1] != meta["match_id"]:
                raise ValueError("Tracking match ID mismatch")
        elif event == "end" and elem.tag == "Frame":
            a = elem.attrib
            audit["source_rows"] += 1
            pid = context.get("PersonId", "")
            # DFL uses TeamId=BALL and PersonId=BALL for ball FrameSets.
            is_ball = context.get("TeamId", "").upper() == "BALL" or pid.upper() == "BALL" or "BallPossession" in a
            n = int(a["N"])
            if is_ball or n % stride == 0:
                x, y = float(a["X"]), float(a["Y"])
                valid = np.isfinite([x, y]).all() and abs(x) <= meta["length"] / 2 + 5 and abs(y) <= meta["width"] / 2 + 5
                t = utc_seconds(a["T"])
                period = context["GameSection"]
                if is_ball:
                    status = int(a.get("BallStatus", 0))
                    audit["inactive_ball_rows"] += status != 1
                    balls.append((period, n, t, x if valid else np.nan, y if valid else np.nan,
                                  int(a.get("BallPossession", 0)), status, valid))
                elif pid in meta["players"]:
                    p = meta["players"][pid]
                    if p["team"] != context["TeamId"]:
                        raise ValueError("Roster/tracking team mismatch")
                    if valid:
                        players.append((period, n, t, pid, p["team"], x, y, p["is_gk"], p["number"]))
                else:
                    audit["unknown_entities"] += 1
                audit["invalid_coordinates"] += not valid
            elem.clear()
            frame_set.clear()
        elif event == "end" and elem.tag == "FrameSet":
            elem.clear()
    p = pd.DataFrame(players, columns=["period", "frame", "time", "player", "team", "x", "y", "is_gk", "number"])
    b = pd.DataFrame(balls, columns=["period", "frame", "time", "x", "y", "possession", "live", "valid"])
    if p.empty or b.empty:
        raise ValueError("Tracking requires players and ball; a source-file prefix is not a match sample")
    for df, keys in [(p, ["period", "frame", "player"]), (b, ["period", "frame"])]:
        if df.duplicated(keys).any():
            raise ValueError(f"Duplicate tracking keys: {keys}")
    b = b.sort_values(["period", "frame"]).reset_index(drop=True)
    for _, group in b.groupby("period"):
        if (np.diff(group.time) <= 0).any() or not np.allclose(np.diff(group.time), np.diff(group.frame) / FPS, atol=.002):
            raise ValueError("Tracking frame/time inconsistency")
    audit.update(player_rows=len(p), ball_rows=len(b), stride=stride)
    return p, b, audit
