"""Public release guards: bounded analytical cases, no raw-coordinate payload."""

import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_static_release_is_bounded_derived_analysis():
    data = json.loads((ROOT / "web/analysis.json").read_text())
    assert len(data["cases"]) == 12
    assert len({c["matchId"] for c in data["cases"]}) == 12
    for tournament in {c["tournament"] for c in data["cases"]}:
        assert sum(c["tournament"] == tournament for c in data["cases"]) == 6
    forbidden = {
        "origin",
        "actual_end",
        "location",
        "freeze_frame",
        "visible_area",
        "opponents",
        "target_x",
        "target_y",
        "start_x",
        "start_y",
        "coef",
        "imputer",
    }

    def inspect(value):
        if isinstance(value, dict):
            assert forbidden.isdisjoint(value)
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    inspect(data)
    for case in data["cases"]:
        assert case["proxyTarget"] in {t["id"] for t in case["targets"]}
        assert any(t["flagged"] for t in case["targets"])
        for target in case["targets"]:
            assert (ROOT / "web" / target["figure"]).is_file()
            assert target["figure"].endswith(".png")
            assert target["probability"] is None or 0 <= target["probability"] <= 1


def test_static_build_matches_every_reviewed_asset(tmp_path):
    spec = importlib.util.spec_from_file_location("passlab_build_website", ROOT / "scripts/build_website.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.build(tmp_path)
    manifest = json.loads((ROOT / "web/bundle.json").read_text())
    for name, expected in manifest["assets"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == expected
    assert not (tmp_path / "passes.csv").exists()
    assert not (tmp_path / "scenes.json").exists()
    assert not (tmp_path / "model-bundles.json").exists()
    html = (tmp_path / "index.html").read_text()
    for target in re.findall(r'(?:src|href)="([^"#]+)"', html):
        if "://" not in target:
            assert (tmp_path / target).exists(), target
