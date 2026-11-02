"""Produce publication documents directly from frozen result files."""
from __future__ import annotations
import csv
from importlib import metadata
import json
from pathlib import Path
import platform
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    results=json.loads((ROOT/"outputs/results.json").read_text())
    synthetic=json.loads((ROOT/"outputs/synthetic-results.json").read_text())
    h=results["splits"]["heldout"];b,p=h["nearest"],h["proposed"]
    ci=h["phase_bootstrap"]
    sr=synthetic["proposed"];sb=synthetic["nearest"]
    strict=h["strict_observed_sensitivity"]
    with (ROOT/"outputs/sensitivity.csv").open() as source:
        sensitivity=list(csv.DictReader(source))
    text=f'''# Pilot results

## Main finding

The temporal heuristic yields fewer identity changes, but its lower assignment availability and increased short-run count prevent a claim of better tactical detection. The real-data short-run hypothesis fails. Synthetic geometric robustness passes the pre-specified engineering criteria. Real marking responsibility remains unvalidated.

![Held-out operational comparison](../outputs/heldout-results.png)

## Held-out match: Sydney FC v Adelaide United, 1996435

| Measure | Nearest defender | Proposed |
|---|---:|---:|
| Eligible attacker-frames | {b['eligible_attacker_frames']:,} | {p['eligible_attacker_frames']:,} |
| Eligible attacker-minutes | {b['eligible_attacker_minutes']:.2f} | {p['eligible_attacker_minutes']:.2f} |
| Identity changes, including distinct returns after unassignment | {b['identity_changes_including_unassigned']} | {p['identity_changes_including_unassigned']} |
| Identity changes / attacker-minute | {b['identity_changes_per_attacker_minute']:.3f} | {p['identity_changes_per_attacker_minute']:.3f} |
| Short interior assigned runs (<0.5 s) | {b['short_assignment_runs']} | {p['short_assignment_runs']} |
| Short runs / attacker-minute | {b['short_runs_per_attacker_minute']:.3f} | {p['short_runs_per_attacker_minute']:.3f} |
| Assigned eligible frames | {100*b['assigned_fraction']:.2f}% | {100*p['assigned_fraction']:.2f}% |
| Assigned frames outside entry geometry | {100*b['assigned_without_entry_geometry_fraction']:.2f}% | {100*p['assigned_without_entry_geometry_fraction']:.2f}% |

All rates use the same eligibility population. Nearest always assigns someone; the proposed method abstains and can retain a defender outside the stricter entry radius. Lower switching and higher geometric support are partly consequences of those design choices. Geometry support is not marking accuracy. The methods disagree on {100*h['disagreement_when_proposed_assigned']:.2f}% of frames where the proposed method assigns a defender; abstentions are excluded from that disagreement denominator.

Proposed-minus-nearest identity-change rate difference: {ci['identity_changes_per_attacker_minute']['proposed_minus_nearest']:.3f} per attacker-minute, 95% paired phase-bootstrap interval [{ci['identity_changes_per_attacker_minute']['low']:.3f}, {ci['identity_changes_per_attacker_minute']['high']:.3f}]. Short-run rate difference: {ci['short_runs_per_attacker_minute']['proposed_minus_nearest']:.3f}, interval [{ci['short_runs_per_attacker_minute']['low']:.3f}, {ci['short_runs_per_attacker_minute']['high']:.3f}]. These use {ci['clusters']} within-match phase clusters and {ci['replicates']:,} resamples. They do not estimate between-match uncertainty, and dependence across neighboring phases may persist.

The proposed method retrieves {sum(h['candidate_counts'].values())} held-out candidates: {h['candidate_counts']['continuous']} continuous-cover, {h['candidate_counts']['brief_gap']} brief-gap and {h['candidate_counts']['gap']} gap candidates. {h['all_involved_detected_candidates']} have all three involved players detected throughout the transfer measurement window. This does not establish that every other defender was detected.

## Observation sensitivity

Requiring detected coordinates for the attacker and all ten opposing outfield players at current and previous three frames leaves {strict['nearest']['eligible_attacker_frames']:,} attacker-frames ({strict['nearest']['eligible_attacker_minutes']:.2f} attacker-minutes). On that separately segmented population, the method yields {sum(strict['candidate_counts'].values())} candidates, including {strict['candidate_counts']['gap']} gap candidates. Identity-change rates are {strict['nearest']['identity_changes_per_attacker_minute']:.3f} versus {strict['proposed']['identity_changes_per_attacker_minute']:.3f}; short interior runs are {strict['nearest']['short_assignment_runs']} versus {strict['proposed']['short_assignment_runs']}. Fragmentation changes which transfers remain observable. Do not interpret the count difference as a measured number of false positives.

## Synthetic geometric evaluation

Reserved seeds 1000-1099 yield {synthetic['protocol']['trajectories']} controlled trajectories across stationary ambiguity, smooth crossing, delayed geometric cover and missing intervals. There are 200 known identity changes after missing-data resets. Observation noise SD is 0.15 m. Event matching tolerance is 1.5 s.

| Metric | Nearest | Proposed |
|---|---:|---:|
| Event precision | {sb['precision']:.4f} | {sr['precision']:.4f} |
| Event recall | {sb['recall']:.4f} | {sr['recall']:.4f} |
| Event F1 | {sb['f1']:.4f} | {sr['f1']:.4f} |
| Excess switches above scenario true-change counts | {sb['excess_switches']} | {sr['excess_switches']} |
| Median signed matched-change latency (s) | {sb['median_signed_latency_s']:.2f} | {sr['median_signed_latency_s']:.2f} |
| Median absolute matched-change latency (s) | {sb['median_absolute_latency_s']:.2f} | {sr['median_absolute_latency_s']:.2f} |

All three pre-specified synthetic hypothesis clauses pass. The proposed method still has {sr['fp']} unmatched predicted changes and {sr['fn']} missed changes; zero excess switches does not mean zero event errors. Longest-gap mean absolute error is {synthetic['geometric_gap']['mean_absolute_longest_gap_error_s']:.3f} s on {synthetic['geometric_gap']['scenarios']} gap scenarios. Seed-cluster bootstrap gives a recall-delta interval {synthetic['seed_cluster_bootstrap']['recall_delta_95pct']} and proposed precision interval {synthetic['seed_cluster_bootstrap']['proposed_precision_95pct']}. These intervals concern simulated noise only.

The stationary synthetic scenario is intentionally near an ambiguous Voronoi boundary, making unrestricted nearest defender switch frequently. The large reduction is specific to that stress test; it cannot be generalized to tactical handoffs in professional matches.

## Threshold and component sensitivity

| Setting | Candidates | Gap candidates | Assigned frames | Identity changes / attacker-minute |
|---|---:|---:|---:|---:|
'''
    for r in sensitivity:
        text+=f"| {r['variant']} | {r['candidates']} | {r['gap_candidates']} | {100*float(r['assigned_fraction']):.1f}% | {float(r['identity_changes_per_attacker_minute']):.3f} |\n"
    text+='''
The default was retained. The 8 m setting bundles entry, release, graph and prediction radii; the other rows change one parameter/component at a time. Candidate counts depend substantially on the coverage radius and confirmation interval. Motion and local-structure ablations do not establish either component's tactical value because no real labels exist.

## Verification and evidence

- Baseline: 500 independent scalar distance checks per match, 1,000 total.
- Unit/regression tests cover ties, side changes, geometry, hysteresis, prefix causality, unknown/reset behavior, gap measurement, duplicates, missing frames and speed jumps.
- `verify_exports.py` independently recomputes every candidate gap from the assignment CSV and reconciles all main counts and replay bindings.
- `results.json`, `synthetic-results.json`, `sensitivity.csv`, the audit receipts and frozen configuration are the controlling evidence. `review-queue.csv` leaves tactical labels blank for independent annotation.
- `marking-handoffs-demo.mp4` is a 32-second illustrative tracking replay. Its two examples follow the manifest's deterministic observability/length rule, not a performance or representative-sampling claim.

The methodological conclusion is a feasible candidate-retrieval pipeline with a documented stability/availability tradeoff. Tactical accuracy and communication failures remain open empirical questions.
'''
    (ROOT/"docs/results.md").write_text(text)
    publication=f'''# Publication drafts

These are drafts, not published posts. Attach the 32-second video and a repository link when publishing; no hosted repository URL for this new project is assumed here.

## LinkedIn

When an attacker moves across the defensive block, which defender becomes the plausible cover?

I built a small tracking-data project to retrieve candidate marking handoffs. It combines attacker-defender proximity graphs with relative motion, a local team-structure reference and temporal hysteresis.

On one held-out SkillCorner match, it retrieved {sum(h['candidate_counts'].values())} candidates, including {h['candidate_counts']['gap']} with a geometric coverage gap of at least 0.4 seconds. Identity changes fell from {b['identity_changes_per_attacker_minute']:.2f} to {p['identity_changes_per_attacker_minute']:.2f} per eligible attacker-minute, while the method assigned a defender on only {100*p['assigned_fraction']:.1f}% of eligible frames.

The tradeoff matters. Short assignment runs increased from {b['short_assignment_runs']} to {p['short_assignment_runs']}, so my pre-specified hypothesis of fewer short runs failed. Synthetic tests with known geometric changes passed, but real tactical accuracy still needs independent labels.

The video shows a continuous-cover candidate and a temporary geometric gap. These are candidate handoffs. Tracking positions cannot reveal what either defender was instructed to do, and broadcast extrapolation can create or hide apparent gaps.

Data: SkillCorner Open Data, MIT licence. Python code, reproducible configuration, sensitivity checks and the full candidate catalogue accompany the project.

## X thread

1/ I built a Python tool to retrieve candidate marking handoffs from free SkillCorner tracking. On one held-out match: {sum(h['candidate_counts'].values())} candidates, {h['candidate_counts']['gap']} with geometric gaps >=0.4 s. The animation shows how the covering-defender estimate changes.

2/ Identity changes fell from {b['identity_changes_per_attacker_minute']:.2f} to {p['identity_changes_per_attacker_minute']:.2f} per attacker-minute, with assignment available on {100*p['assigned_fraction']:.1f}% of eligible frames. Short runs increased {b['short_assignment_runs']} to {p['short_assignment_runs']}, so that hypothesis failed. Fewer switches do not prove better tactical accuracy.

3/ These are candidate handoffs, not known coaching assignments. Synthetic geometric tests passed; real tactical labels are still needed. Extrapolated tracking can create or hide gaps. Data: SkillCorner Open Data (MIT).

## Claim checks

Every numeric claim above comes from `outputs/results.json` or `synthetic-results.json`. No improvement in real marking accuracy, prevention of goals, defender intent, communication failure or match outcome is claimed. The user's suggested communication-failure hook is a hypothesis that this dataset cannot verify, so it is not presented as a result.
'''
    (ROOT/"docs/publication.md").write_text(publication)
    env=dict(python=platform.python_version(),packages={name:metadata.version(name) for name in ["numpy","pillow"]},
             optional_packages={}, source_revision=json.loads((ROOT/"data/provenance.json").read_text())["revision"])
    for name in ["matplotlib"]:
        try: env["optional_packages"][name]=metadata.version(name)
        except metadata.PackageNotFoundError: pass
    (ROOT/"outputs/environment.json").write_text(json.dumps(env,indent=2)+"\n")
    shutil.copyfile(ROOT/"docs/source/LICENSE.skillcorner",ROOT/"outputs/LICENSE.skillcorner")
    clips=json.loads((ROOT/"outputs/replays.json").read_text())
    queue=[]
    for split in ["development","heldout"]:
        for category in ["continuous","brief_gap","gap"]:
            pool=sorted([c for c in clips if c["split"]==split and c["category"]==category],key=lambda c:c["id"])
            for condition in [lambda c:c["all_involved_detected"],lambda c:not c["all_involved_detected"],lambda c:c["ambiguous"] or c["shared_incoming"]]:
                eligible=[c for c in pool if condition(c) and c["id"] not in [q["id"] for q in queue]]
                if eligible:
                    c=eligible[0]
                    queue.append({k:c[k] for k in ["id","split","category","clock","attacker","outgoing","incoming","longest_gap_s","involved_detected_fraction","ambiguous","shared_incoming"]}|
                                 dict(reviewer="",tactical_label="",observation_sufficient="",notes=""))
    with (ROOT/"outputs/review-queue.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(queue[0]));writer.writeheader();writer.writerows(queue)
    print("Wrote results, publication drafts, environment and review queue",len(queue))


if __name__=="__main__": main()
