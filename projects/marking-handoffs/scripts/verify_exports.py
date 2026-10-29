"""Independent CSV reconciliation of every candidate gap and operational count."""
from collections import defaultdict, Counter
import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = json.loads((ROOT / "outputs/results.json").read_text())
    data, groups, exposure = {}, defaultdict(list), Counter()
    with gzip.open(ROOT / "outputs/assignments.csv.gz", "rt") as f:
        for row in csv.DictReader(f):
            key = tuple(int(row[k]) for k in ["match_id", "frame", "attacker_id"])
            assert key not in data, f"Duplicate observation: {key}"
            data[key] = row
            groups[(key[0], int(row["segment_id"]))].append(row)
            exposure[key[0]] += 1
    replays = json.loads((ROOT / "outputs/replays.json").read_text())
    replay_map = {r["id"]: r for r in replays}
    with (ROOT / "outputs/candidates.csv").open() as f:
        candidates = list(csv.DictReader(f))
    assert len(replay_map) == len(candidates), "Candidate/replay count mismatch"
    for event in candidates:
        mid, aid = int(event["match_id"]), int(event["attacker_id"])
        lo, hi = int(event["window_start_frame"]), int(event["window_end_frame_exclusive"])
        sequence = [data[(mid, frame, aid)] for frame in range(lo, hi)]
        assert all(int(r["segment_id"]) == int(event["segment_id"]) for r in sequence)
        longest = run = total = 0
        for row in sequence:
            if int(row["plausible_defenders"]) == 0:
                run += 1
                total += 1
                longest = max(run, longest)
            else:
                run = 0
        assert abs(total / 10 - float(event["gap_s"])) < 1e-9
        assert abs(longest / 10 - float(event["longest_gap_s"])) < 1e-9
        category = "gap" if longest >= 4 else "brief_gap" if total else "continuous"
        assert category == event["category"]
        incoming = data[(mid, int(event["frame"]), aid)]
        outgoing = data[(mid, int(event["outgoing_last_frame"]), aid)]
        assert int(incoming["proposed_id"]) == int(event["incoming_id"])
        assert int(outgoing["proposed_id"]) == int(event["outgoing_id"])
        assert event["incoming_id"] != event["outgoing_id"]
        for replay in replay_map[event["id"]]["replay"]:
            r = data[(mid, replay["frame"], aid)]
            assert int(r["plausible_defenders"]) == replay["cover"]
            assert (int(r["proposed_id"]) if r["proposed_id"] else None) == replay["assignment"]
    # Compute run and identity counts using a separate scalar implementation.
    for split, result in results["splits"].items():
        mid = result["match_id"]
        assert exposure[mid] == result["nearest"]["eligible_attacker_frames"]
        for method, col in [("nearest", "nearest_id"), ("proposed", "proposed_id")]:
            switches = short = assigned = 0
            for (match, _), rows in groups.items():
                if match != mid:
                    continue
                labels = [r[col] for r in rows]
                assigned += sum(bool(v) for v in labels)
                old = ""
                chunks = []
                for value in labels:
                    if value:
                        if old and value != old:
                            switches += 1
                        old = value
                    if chunks and chunks[-1][0] == value:
                        chunks[-1][1] += 1
                    else:
                        chunks.append([value, 1])
                short += sum(bool(v) and count < 5 for v, count in chunks[1:-1])
            assert switches == result[method]["identity_changes_including_unassigned"]
            assert short == result[method]["short_assignment_runs"]
            assert abs(assigned / exposure[mid] - result[method]["assigned_fraction"]) < 1e-12
        counts = Counter(e["category"] for e in candidates if int(e["match_id"]) == mid)
        assert dict(counts) == result["candidate_counts"]
    summary = dict(assignment_rows=len(data), candidates_checked=len(candidates),
                   replay_frames_checked=sum(len(c["replay"]) for c in replays),
                   all_gap_durations_recomputed=True, all_counts_reconciled=True,
                   reference="Independent scalar CSV calculations; no analytics-module imports")
    (ROOT / "outputs/export-verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
