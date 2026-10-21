import argparse
import json
from pathlib import Path

from .analysis import RunConfig
from .data import DEFAULT_MATCH, RAW, download
from .pipeline import run_project


def main():
    parser = argparse.ArgumentParser(description="SkillCorner off-ball run baseline")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list-matches", help="List matches from the pinned source index")
    listing.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    run = sub.add_parser("run", help="Download, validate, analyze and produce charts/report")
    run.add_argument("--match", type=int, nargs="+", default=[DEFAULT_MATCH])
    scope = run.add_mutually_exclusive_group()
    scope.add_argument("--seconds", type=int, default=300, help="Bounded tracking prefix (default 300)")
    scope.add_argument("--full", action="store_true", help="Download full tracking (~100-200 MB per match)")
    run.add_argument("--speed", type=float, default=5.0)
    run.add_argument("--distance", type=float, default=5.0)
    run.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.command == "list-matches":
        path = args.project / "data/raw/matches.json"
        download(f"{RAW}/data/matches.json", path)
        for match in json.loads(path.read_text()):
            print(f"{match['id']}  {match['date_time'][:10]}  {match['home_team']['short_name']} vs {match['away_team']['short_name']}")
    else:
        for match_id in args.match:
            result = run_project(args.project, match_id, None if args.full else args.seconds,
                                 RunConfig(speed_mps=args.speed, min_distance_m=args.distance))
            print(json.dumps({k: result[k] for k in ["match_id", "scope", "run_count", "metric_valid_count", "audit", "validation"]}, indent=2))


if __name__ == "__main__":
    main()
