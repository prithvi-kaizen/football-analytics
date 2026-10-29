import argparse
from pathlib import Path
from .experiment import run

parser = argparse.ArgumentParser(description='Passing-lane obstruction research experiment')
parser.add_argument('--config', type=Path, default=Path('configs/pilot.json'))
args = parser.parse_args()
run(Path(__file__).resolve().parents[1], args.config.resolve())
