import csv
from pathlib import Path

import numpy as np

from .schema import LABELS


def write_submission(path, labels, expected_rows=None):
    values = np.asarray(labels)
    if values.ndim != 1 or not len(values) or not set(values) <= set(LABELS):
        raise ValueError("labels must be a nonempty vector using only H/A/D/X")
    if expected_rows is not None and len(values) != expected_rows:
        raise ValueError("row count mismatch; do not pad or trim a submission")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["frame", "label"])
        writer.writerows(enumerate(values))
    return path
