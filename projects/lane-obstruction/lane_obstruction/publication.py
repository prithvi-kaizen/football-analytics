"""Write publication text directly from executed outputs."""
import json


def number(value):
    return 'unavailable' if value is None else f'{value:.3f}'


def write_report(root, results, audits, sensitivity):
    r = results['pooled']
    lo, hi = r['interval_95']
    outcome = 'supported' if results['hypothesis_supported'] else 'not supported'
    lines = ['# Executed pilot results', '',
        'Data: SkillCorner Open Data, with PySport. All scores are model-derived proxies, not validated prevented passes.', '',
        f'The pre-specified hypothesis is **{outcome}** under the recorded criterion. No parameters were selected using the test results.', '',
        '| Match | Eligible / possession starts | All players + ball detected | Missing ease among all starts |',
        '| --- | ---: | ---: | ---: |']
    for a in audits:
        lines.append(f'| {a["match"]} ({a["match_id"]}) | {a["eligible_starts"]} / {a["possession_rows"]} | {a["all_detected_starts"]} | {a["missing_ease"]} |')
    lines += ['', 'Exclusion counts and full tracking coverage are in `data_audit.json`. Categories above are missingness before eligibility filters, not an additional exclusion count.', '',
        '## Held-out associations with provider passing difficulty', '',
        '| Match | Joint labelled n | Geometry rho | Arrival rho | Difference | Paired phase-bootstrap 95% interval |',
        '| --- | ---: | ---: | ---: | ---: | --- |']
    for mid, a in results['per_match'].items():
        interval = a['interval_95']
        lines.append(f'| {mid} | {a["n"]} | {number(a["geometry_rho"])} | {number(a["arrival_rho"])} | {number(a["delta_rho"])} | [{number(interval[0])}, {number(interval[1])}] |')
    lines += [f'| Pooled | {r["n"]} | {number(r["geometry_rho"])} | {number(r["arrival_rho"])} | {number(r["delta_rho"])} | [{lo:.3f}, {hi:.3f}] |', '',
        f'The pooled bootstrap uses {r["clusters"]} provider possession-phase clusters and {r["repetitions"]} paired resamples stratified by match. These intervals condition on only two selected matches. They do not quantify between-match or league uncertainty. The alternate five-minute-block interval is {results["time_block_sensitivity"]["interval_95"]}.', '',
        f'Across {results["held_out_lanes"]} candidate lanes at {results["held_out_starts"]} held-out starts, {results["geometry_open_arrival_ge_half"]} are unblocked by geometry but have arrival obstruction >=0.5. This is model disagreement, not observed missed interceptions.', '',
        f'Mean detected-player fraction at eligible held-out starts: {results["mean_player_detection_fraction"]:.1%}. The all-22-players-and-ball-detected analysis has n={results["all_detected"]["n"]}; ' + ('association is unavailable.' if results['all_detected']['interval_95'] is None else 'see results.json for its conditional interval.'), '',
        '## Pressure and sensitivity', '',
        f'Unadjusted overall-pressure association: geometry rho={number(results["pressure_association"]["geometry_rho"])}, arrival rho={number(results["pressure_association"]["arrival_rho"])} (joint n={results["pressure_association"]["n"]}). Pressure is a separate provider-derived construct and not an obstruction label. No causal interpretation or pass-accuracy claim follows.', '',
        '| Variant | n | Geometry rho | Arrival rho | Difference | Mean obstruction |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for v in sensitivity:
        lines.append(f'| {v["variant"]} | {v["n"]} | {number(v["geometry_rho"])} | {number(v["arrival_rho"])} | {number(v["delta_rho"])} | {v["mean_obstruction"]:.3f} |')
    lines += ['', 'Sensitivity rows are descriptive alternatives, not uncertainty intervals or a parameter search for a publishable winner. The target-range sensitivity changes the target population and may change the eligible denominator. All-detected filtering cannot remove extrapolation bias when it yields no data.', '',
        '## What the pilot establishes', '',
        'The source loader, finite corridor geometry, past-only arrival heuristic, per-defender ablations and temporal replays execute on real open data. The test reports agreement with dependent provider categories. It does not validate perception, intent, pass completion, tackles avoided, prevented passes or a player ranking. DLO remains a mathematical marginal-obstruction indicator.', '',
        'Read `../docs/methodology.md` and `../docs/limitations.md` before reusing any figure. Exact CSV rows and JSON receipts accompany this report.']
    (root/'outputs/results.md').write_text('\n'.join(lines)+'\n')
    post = f'''# Suggested public post (not sent)

What if a defensive midfielder's most important contribution is the pass the opposition never even tries?

I tested two ways to score a passing lane: a 1 m geometric corridor and an approximate defender-arrival model.

The simpler model had stronger agreement with SkillCorner's passing-difficulty categories. Across {r['n']} labelled starts in two pipeline-held-out A-League matches, Spearman rho was {r['geometry_rho']:.3f} for geometry and {r['arrival_rho']:.3f} for arrival time. The paired difference was {r['delta_rho']:+.3f}, with a phase-cluster bootstrap 95% interval of [{lo:.3f}, {hi:.3f}]. The improvement hypothesis was {outcome}.

These categories use the same tracking inputs. Agreement does not validate prevented passes. None of the eligible held-out starts had all players and the ball detected on camera, so the strict observed-only check was unavailable.

The project includes the code, source audit, sensitivity tests and a pitch replay showing the Defensive Lane Obstruction proxy. Data: SkillCorner Open Data, with PySport.

## Short X version

Can a defender obstruct a pass before it is tried? On {r['n']} starts from two held-out matches, geometry agreed more with provider difficulty than arrival times (rho {r['geometry_rho']:.3f} vs {r['arrival_rho']:.3f}). Shared-input proxies, not validated prevented passes. Data: SkillCorner + PySport.
'''
    (root/'outputs/public-post.md').write_text(post)
