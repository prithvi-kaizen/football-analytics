import argparse
import json

from .pipeline import run


def main():
    parser=argparse.ArgumentParser(description="Reproduce a DFL rest-defence analysis")
    parser.add_argument("--match",default="J03WPY")
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument("--sample",action="store_true",help="Download 23 verified entity ranges, about 12 MB total")
    scope.add_argument("--bundled",action="store_true",help="Use bundled genuine three-minute extract, no network")
    parser.add_argument("--output",type=str)
    parser.add_argument("--persistence",type=float,default=.4)
    args=parser.parse_args()
    _,audit=run(args.match,args.sample,args.bundled,args.output,args.persistence)
    print(json.dumps(audit,indent=2))


if __name__ == "__main__":
    main()
