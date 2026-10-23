from __future__ import annotations

import argparse
from pathlib import Path

from .data import Cache, LEAGUES, catalog, download, select_matches


def main():
    parser = argparse.ArgumentParser(description="Free StatsBomb women's possession analysis")
    parser.add_argument("command", choices=["download", "run", "render"])
    parser.add_argument("--league", choices=[*LEAGUES, "all"], default="liga-f")
    parser.add_argument("--sample", type=int, default=6, help="Matches per league; default 6")
    parser.add_argument("--full", action="store_true", help="Select entire league(s)")
    parser.add_argument("--cache", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("outputs/sample"))
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.command == "render":
        from .report import render_existing
        render_existing(args.output)
        return
    cache = Cache(args.cache, args.offline)
    leagues = list(LEAGUES) if args.league == "all" else [args.league]
    sample = None if args.full else args.sample
    if args.command == "download":
        download(cache, leagues, sample, workers=max(1, min(args.workers, 8)))
    else:
        from .pipeline import run
        matches = [m for league in leagues for m in select_matches(catalog(cache, league), sample)]
        run(cache, matches, args.output, sample=sample is not None)


if __name__ == "__main__":
    main()
