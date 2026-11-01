import argparse
import json
from pathlib import Path

from .official import DEFAULT_OFFICIAL, ROOT


def main():
    parser = argparse.ArgumentParser(description="Local possession preparation with public and synthetic data only")
    sub = parser.add_subparsers(dest="command", required=True)
    sanity = sub.add_parser("sanity", help="re-score only the four immutable supplied baseline CSVs")
    sanity.add_argument("--official", type=Path, default=DEFAULT_OFFICIAL)
    sanity.add_argument("--out", type=Path, default=ROOT / "outputs/public_sanity")
    bench = sub.add_parser("benchmark", help="synthetic experiments; no public label input")
    bench.add_argument("--config", type=Path, default=ROOT / "configs/benchmark.json")
    bench.add_argument("--out", type=Path, default=ROOT / "outputs/synthetic")
    phase = sub.add_parser("phase1", help="paired synthetic failure analysis and hierarchical ablations")
    phase.add_argument("--config", type=Path, default=ROOT / "configs/phase1.json")
    phase.add_argument("--out", type=Path, default=ROOT / "outputs/phase1")
    sample = sub.add_parser("sample", help="unscored public CSV adapter smoke test; no events loaded")
    sample.add_argument("--home", required=True, type=Path)
    sample.add_argument("--away", required=True, type=Path)
    sample.add_argument("--max-frames", type=int)
    sample.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "sanity":
        from .official import reproduce
        print(reproduce(args.out, args.official))
    elif args.command == "benchmark":
        from .experiments import benchmark
        result = benchmark(args.config, args.out)
        print(f"Completed {len(result)} synthetic method/scenario/seed runs in {args.out}")
        print(result.groupby("method")[["macro_f1", "spell_f1"]].mean().to_string())
    elif args.command == "phase1":
        from .phase1_experiments import evaluate_phase1
        result = evaluate_phase1(args.config, args.out)
        print(f"Completed {len(result)} paired synthetic method runs in {args.out}")
    else:
        from .experiments import sample_smoke
        if args.max_frames is not None and args.max_frames <= 0:
            parser.error("--max-frames must be positive")
        print(json.dumps(sample_smoke(args.home, args.away, args.out, args.max_frames), indent=2))


if __name__ == "__main__":
    main()
