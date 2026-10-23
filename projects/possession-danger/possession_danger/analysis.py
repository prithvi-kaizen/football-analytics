from __future__ import annotations

import numpy as np
import pandas as pd


def split_matches(matches: list[dict], test_fraction: float = 0.2) -> dict[int, str]:
    """Latest fixtures per league are held out; all events of a match stay together."""
    groups = {}
    for m in matches:
        groups.setdefault(m["competition"]["competition_id"], []).append(m)
    result = {}
    for group in groups.values():
        ordered = sorted(group, key=lambda m: (m["match_date"], m["match_id"]))
        if len(ordered) < 3:
            raise ValueError("Each league needs at least 3 matches")
        ntest = max(1, int(np.ceil(len(ordered) * test_fraction)))
        for i, m in enumerate(ordered):
            result[m["match_id"]] = "test" if i >= len(ordered) - ntest else "train"
    return result


def classify(frame: pd.DataFrame, long_seconds: float = 30, many_passes: int = 10,
             low_xt: float = 0.01, direct_seconds: float = 15, high_xt: float = 0.05) -> pd.Series:
    high_volume = (frame.elapsed_seconds.ge(long_seconds) | frame.passes.ge(many_passes)) & frame.positive_xt.lt(low_xt) & frame.shots.eq(0)
    direct = frame.elapsed_seconds.le(direct_seconds) & frame.passes.le(4) & frame.positive_xt.ge(high_xt)
    return pd.Series(np.select([high_volume, direct], ["High volume / low threat", "Direct / high threat"], default="Other"), index=frame.index)


def safe_share(values, denominator):
    return values / denominator.replace(0, np.nan) * 100


def team_matches(possessions: pd.DataFrame) -> pd.DataFrame:
    keys = ["match_id", "team_id", "team", "competition", "season", "date", "split"]
    totals = possessions.groupby(keys, as_index=False).agg(
        possessions=("sequence_key", "size"), active_seconds=("active_seconds", "sum"),
        passes=("passes", "sum"), completed_passes=("completed_passes", "sum"),
        final_third_passes=("final_third_passes", "sum"), shots=("shots", "sum"), xg=("xg", "sum"),
        positive_xt=("positive_xt", "sum"), net_xt=("net_xt", "sum"), turnover_xt=("turnover_xt", "sum"))
    for numerator, output in [("active_seconds", "possession_pct"), ("completed_passes", "pass_share"),
                              ("final_third_passes", "field_tilt"), ("positive_xt", "threat_share")]:
        denominator = totals.groupby("match_id")[numerator].transform("sum")
        totals[output] = safe_share(totals[numerator], denominator)
    totals["xt_per_100"] = totals.positive_xt / totals.possessions * 100
    return totals


def team_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (competition, team), g in frame.groupby(["competition", "team"]):
        rows.append({"competition": competition, "team": team, "matches": g.match_id.nunique(),
                     "mean_possession_pct": g.possession_pct.mean(), "mean_field_tilt": g.field_tilt.mean(),
                     "mean_threat_share": g.threat_share.mean(), "positive_xt": g.positive_xt.sum(),
                     "net_xt": g.net_xt.sum(), "shots": int(g.shots.sum()), "xg": g.xg.sum(),
                     "possessions": int(g.possessions.sum()), "xt_per_100": g.positive_xt.sum() / g.possessions.sum() * 100})
    return pd.DataFrame(rows).sort_values("xt_per_100", ascending=False)


def score_states(events: pd.DataFrame, rated: pd.DataFrame) -> pd.DataFrame:
    own = events.loc[events.team_id.eq(events.owner_id)].copy()
    own = own.merge(rated[["event_id", "positive_xt", "xt_delta"]], on="event_id", how="left", validate="one_to_one")
    own[["positive_xt", "xt_delta"]] = own[["positive_xt", "xt_delta"]].fillna(0)
    own["shot_count"] = own.type.eq("Shot").astype(int)
    own["final_third_passes"] = (own.type.eq("Pass") & own.complete & own.x.ge(80)).astype(int)
    grouped = own.groupby(["match_id", "team", "score_state", "competition", "split"], as_index=False).agg(
        active_seconds=("active_seconds", "sum"), positive_xt=("positive_xt", "sum"),
        net_xt=("xt_delta", "sum"), shots=("shot_count", "sum"), xg=("xg", "sum"),
        final_third_passes=("final_third_passes", "sum"))
    # This denominator is the team's active possession time, not minutes at that score state.
    grouped["xt_per_active_minute"] = grouped.positive_xt / grouped.active_seconds.replace(0, np.nan) * 60
    return grouped


def barcelona_comparison(totals: pd.DataFrame) -> dict | None:
    barca = totals.loc[totals.team.str.contains("Barcelona", regex=False)]
    if barca.empty:
        return None
    rivals = totals.loc[totals.match_id.isin(barca.match_id) & ~totals.team.str.contains("Barcelona", regex=False)]
    pairs = barca.merge(rivals, on="match_id", suffixes=("_barca", "_rival"), validate="one_to_one")
    if pairs.empty:
        return None
    def difference(g):
        return float(100 * (g.positive_xt_barca.sum() / g.possessions_barca.sum() - g.positive_xt_rival.sum() / g.possessions_rival.sum()))
    rng = np.random.default_rng(2026)
    boot = [difference(pairs.iloc[rng.integers(0, len(pairs), len(pairs))]) for _ in range(2000)]
    return {"matches": len(pairs), "mean_possession_pct": float(barca.possession_pct.mean()),
            "mean_field_tilt": float(barca.field_tilt.mean()), "mean_threat_share": float(barca.threat_share.mean()),
            "barca_xt_per_100": float(100 * barca.positive_xt.sum() / barca.possessions.sum()),
            "opponent_xt_per_100": float(100 * rivals.positive_xt.sum() / rivals.possessions.sum()),
            "difference_xt_per_100": difference(pairs), "bootstrap_95_interval": np.quantile(boot, [0.025, .975]).tolist(),
            "interval_note": "Seed 2026; 2,000 paired fixture bootstrap resamples. Descriptive interval, limited by fixture count and schedule; no model-refit uncertainty."}
