from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import build


def main():
    parser = argparse.ArgumentParser(description='Pinned StatsBomb corner analysis for local research')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    size = parser.add_mutually_exclusive_group()
    size.add_argument('--sample', type=int, default=1, help='Earliest N matches per tournament; default 1')
    size.add_argument('--all', action='store_true', help='All 82 matches from both tournaments')
    parser.add_argument('--tournament', choices=['euro2024', 'weuro2025'], action='append')
    parser.add_argument('--horizon', type=float, default=15)
    parser.add_argument('--short-threshold', type=float, default=15)
    parser.add_argument('--offline', action='store_true', help='Read only verified cached provider downloads')
    parser.add_argument('--output', default='outputs', help='Research output directory relative to root')
    args = parser.parse_args()
    if args.horizon <= 0 or args.short_threshold <= 0:
        parser.error('Horizon and short threshold must be positive')
    _, info = build(args.root, None if args.all else args.sample, args.tournament or ('euro2024', 'weuro2025'), args.horizon,
                    args.short_threshold, args.offline, args.output)
    print(json.dumps({k: v for k,v in info.items() if k not in ('source_files', 'matches', 'clusters')}, indent=2))
    print(f"Processed {len(info['matches'])} matches. Local artifacts: {args.root / args.output}")


if __name__ == '__main__':
    main()
