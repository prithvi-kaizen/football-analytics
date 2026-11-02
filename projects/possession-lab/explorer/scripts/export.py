"""Create a strictly public/synthetic static bundle and a whitelisted open-source archive."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from possession_lab.adapters.metrica_csv import MetricaCSVAdapter
from possession_lab.explorer_api import describe_batch, scenario, observability
from possession_lab.official import DEFAULT_OFFICIAL, sha256, verify
from possession_lab.phase2_experiments import verify_phase1_freeze
from possession_lab import explorer_v2

SITE = ROOT / "explorer"
DIST = SITE / "dist"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, allow_nan=False, separators=(",", ":")) + "\n")


def write_zip(path, entries):
    # Fixed timestamps/order make exported source/code archives byte-reproducible.
    with ZipFile(path, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(entries.items()):
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)


def export():
    verify()
    verify_phase1_freeze()
    DIST.mkdir(parents=True, exist_ok=True)
    data_dir = DIST / "data"
    data_dir.mkdir(exist_ok=True)
    write_json(data_dir / "default.json", scenario())
    presets = {"stationary_live": {"mechanism": "stationary_live", "gap_duration": 0},
               "contested": {"mechanism": "contested", "gap_duration": 0},
               "player_gaps": {"mechanism": "player_gaps", "gap_duration": 0},
               "identity_switches": {"mechanism": "identity_switches", "gap_duration": 0},
               "clean": {"mechanism": "ordinary", "noise": 0, "loss": 0, "gap_duration": 0}}
    for key, settings in presets.items():
        write_json(data_dir / f"{key}.json", scenario(settings))
    for kind in ("static", "invisible"):
        for evidence in ("none", "independent", "null"):
            write_json(data_dir / f"observability_{kind}_{evidence}.json", observability({"kind": kind, "evidence": evidence}))
    motion_presets = {"default": {}, "clean": {"noise": 0, "loss": 0, "gap_duration": 0},
                      "stationary_live": {"mechanism": "stationary_live", "noise": .08, "loss": 0, "gap_duration": 0},
                      "contested": {"mechanism": "contested", "gap_duration": 0},
                      "player_gaps": {"mechanism": "player_gaps", "gap_duration": 0},
                      "identity_switches": {"mechanism": "identity_switches", "gap_duration": 0}}
    for name, settings in motion_presets.items():
        write_json(data_dir / f"motion_{name}.json", explorer_v2.scenario(settings))
    for evidence in ("none", "independent", "null"):
        write_json(data_dir / f"observability_moving_{evidence}.json", explorer_v2.observability({"evidence": evidence}))
    (DIST / "public-inputs").mkdir(exist_ok=True)
    sample_sources = []
    for game in (1, 2):
        folder = ROOT.parent / "public-sample-data" / "data" / f"Sample_Game_{game}"
        home = folder / f"Sample_Game_{game}_RawTrackingData_Home_Team.csv"
        away = folder / f"Sample_Game_{game}_RawTrackingData_Away_Team.csv"
        # Only these known public paths are read. No environment lookup or dataset scan.
        batch = MetricaCSVAdapter(home, away, max_frames=1000).load()
        batch.provenance.update({"attribution": "Metrica Sports", "sample_game": game,
                                 "source_commit": "e706dd506b360d69d9d123d5b8026e7294b13996",
                                 "excerpt": "first 1000 public tracking frames; predictions computed within excerpt",
                                 "licensing": "Public sample use per source README; dataset is not relicensed under the code MIT licence"})
        result = describe_batch(batch, None, f"Metrica public Sample Game {game}")
        write_json(data_dir / f"public{game}.json", result)
        payload = explorer_v2.public_payload(batch, game)
        write_json(DIST / "public-inputs" / f"sample{game}.json", payload)
        write_json(data_dir / f"public{game}_degraded.json", explorer_v2.public_demo(
            {"source": f"public{game}", "noise": 0, "loss": 0}, payload))
        sample_sources.append(batch.provenance)
    entries = {str(p.relative_to(ROOT / "src")): p.read_bytes() for p in (ROOT / "src").rglob("*.py")}
    entries.update({"explorer_metrics.py": (DEFAULT_OFFICIAL / "evaluation/possession_metrics.py").read_bytes(),
                    "explorer_reference.py": (DEFAULT_OFFICIAL / "starter/baseline.py").read_bytes(),
                    "games.py": (DEFAULT_OFFICIAL / "games.py").read_bytes(),
                    "UPSTREAM-LICENSE.txt": (DEFAULT_OFFICIAL / "LICENSE").read_bytes()})
    write_zip(DIST / "research-python.zip", entries)
    (DIST / "research").mkdir(exist_ok=True)
    reports = {"phase0": ROOT / "README.md", "phase1": ROOT / "docs/phase1/REPORT.md",
               "phase2": ROOT / "docs/phase2/REPORT.md"}
    for name, path in reports.items():
        shutil.copyfile(path, DIST / "research" / f"{name}.md")
    manifest = {"scope": "public samples and synthetic observations only; no competition dataset or labels",
                "code_license": "MIT (dataset terms separate)", "pyodide_version": "0.29.2",
                "research_source_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(entries.items())},
                "official_commit": verify()["commit"], "public_samples": sample_sources,
                "frozen_phase1_files": verify_phase1_freeze(),
                "sample_accuracy_status": "No independent trusted possession labels; accuracy metrics are null"}
    write_json(DIST / "provenance.json", manifest)
    public_source = {}
    # No .git, .env, credentials, private logs, local runtimes or downloaded full datasets.
    for directory in ("src", "tests", "configs", "docs", "scripts"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                public_source["possession-lab/" + str(path.relative_to(ROOT))] = path.read_bytes()
    for name in ("README.md", "pyproject.toml", "requirements.lock.txt", ".python-version", "LICENSE", "THIRD_PARTY.md"):
        path = ROOT / name
        if path.exists():
            public_source["possession-lab/" + name] = path.read_bytes()
    # Historical files are all public/synthetic; these exact whitelists support freeze tests.
    frozen = json.loads((ROOT / "docs/phase2/phase1_freeze.json").read_text())
    for name in frozen["files"]:
        if name.startswith("outputs/"):
            public_source["possession-lab/" + name] = (ROOT / name).read_bytes()
    for path in (ROOT / "outputs/synthetic").rglob("*"):
        if path.is_file():
            public_source["possession-lab/" + str(path.relative_to(ROOT))] = path.read_bytes()
    for directory in ("scripts", "tests", "web"):
        for path in (SITE / directory).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                public_source["possession-lab/" + str(path.relative_to(ROOT))] = path.read_bytes()
    for name in ("README.md", "DESIGN.md"):
        if (SITE / name).exists():
            public_source["possession-lab/explorer/" + name] = (SITE / name).read_bytes()
    public_source["possession-lab/vendor/official/LICENSE"] = (DEFAULT_OFFICIAL / "LICENSE").read_bytes()
    write_zip(DIST / "possession-lab-source.zip", public_source)
    print(json.dumps({"exported": str(DIST), "public_source_files": len(public_source),
                      "python_archive_bytes": (DIST / "research-python.zip").stat().st_size,
                      "source_archive_bytes": (DIST / "possession-lab-source.zip").stat().st_size}))


if __name__ == "__main__":
    export()
