"""Package aggregate findings and three labelled, derived match examples."""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(dest):
    summary = json.loads((ROOT / "results/summary.json").read_text())
    episodes_path = ROOT / "results/episodes.local.json"
    if not episodes_path.exists():
        release = json.loads((ROOT / "web/data.json").read_text())
        if release["summary"] != summary or len(release["examples"]) != 3:
            raise ValueError("Published aggregate snapshot disagrees with verified analysis")
        dest.mkdir(parents=True, exist_ok=True)
        for filename in ("index.html", "style.css", "app.js", "data.json"):
            shutil.copyfile(ROOT / "web" / filename, dest / filename)
        shutil.copyfile(ROOT.parent / "tacticai-lite/assets/SB - Icon Lockup - Colour positive.png", dest / "statsbomb-logo.png")
        shutil.copyfile(ROOT / "media/demo.mp4", dest / "demo.mp4")
        print(f"Built {dest} from reviewed aggregate release")
        return
    episodes = json.loads(episodes_path.read_text())
    choices = [
        (3930178, 26, "The second ball stayed alive", "A clearance did not end Croatia's attack; the regained ball was carried into the box before a shot."),
        (3930166, 28, "A clearance without a recovery", "Portugal's delivery met a Czech clearance; no attacking recovery is observed before the stoppage."),
        (3938642, 56, "The counterattack risk", "Czechia recovered after a Georgian clearance, shot, then lost control; Georgia shot within 15 seconds of confirmed defensive control."),
    ]
    examples = []
    rows = [value["15"] for value in episodes.values()]
    for mid, minute, title, note in choices:
        matches = [r for r in rows if r["match_id"] == mid and r["minute"] == minute]
        if len(matches) != 1:
            raise ValueError(f"Example match/minute is not unique: {mid}/{minute}")
        r = matches[0]
        if len(examples) == 0 and not (r["second_shots"] and r["second_box_entries"]):
            raise ValueError("First example no longer shows the stated continuation")
        if len(examples) == 1 and (not r["clearance"] or r["recovered"]):
            raise ValueError("Second example no longer shows a harmless clearance")
        if len(examples) == 2 and not r["counter_shots"]:
            raise ValueError("Third example no longer shows an opposition shot")
        # Curated phase milestones, not redistributed provider event rows.
        phases = [{"label": "Delivery", "t": 0}]
        milestones = [("Defensive contact", "Clearance", "Clearance"),
                      ("Second ball", "Ball Recovery", "Second ball"),
                      ("Second ball", "Carry into box", "Box entry"),
                      ("Second ball", "Shot", "Attacking shot"),
                      ("Turnover", "Carry", "Defensive control"),
                      ("Counterattack", "Opposition shot", "Opposition shot")]
        for phase, label, title_text in milestones:
            found = next((e for e in r["events"] if e["phase"] == phase and e["label"] == label), None)
            if found:
                phases.append({"label": title_text, "t": found["t"]})
        if r["state"] == "stoppage":
            phases.append({"label": "Stoppage", "t": None})
        phases.sort(key=lambda e: 999 if e["t"] is None else e["t"])
        examples.append({"title": title, "note": note, "match": r["match"], "date": r["date"],
                         "minute": r["minute"], "phases": phases, "outcome": r["state"].replace("_", " ")})
    flow = {}
    for h in (10, 15, 20, 30):
      flow[str(h)] = {}
      for tournament in ("Combined (descriptive)", "Men's Euro 2024", "Women's Euro 2025"):
        items = [v[str(h)] for v in episodes.values() if tournament.startswith("Combined") or v[str(h)]["tournament"] == tournament]
        flow[str(h)][tournament] = {
            "contact": sum(r["contact"] for r in items),
            "no_contact": sum(not r["contact"] for r in items),
            "contact_recovered": sum(r["contact"] and r["recovered"] for r in items),
            "contact_no_recovery": sum(r["contact"] and not r["recovered"] for r in items),
            "recovered_shot": sum(r["contact"] and r["recovered"] and r["second_shots"] > 0 for r in items),
            "recovered_no_shot": sum(r["contact"] and r["recovered"] and r["second_shots"] == 0 for r in items),
        }
    payload = {"summary": summary, "flow": flow, "examples": examples}
    (ROOT / "web/data.json").write_text(json.dumps(payload, separators=(",", ":")))
    dest.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "style.css", "app.js"):
        shutil.copyfile(ROOT / "web" / filename, dest / filename)
    shutil.copyfile(ROOT.parent / "tacticai-lite/assets/SB - Icon Lockup - Colour positive.png", dest / "statsbomb-logo.png")
    (dest / "data.json").write_text(json.dumps(payload, separators=(",", ":")))
    shutil.copyfile(ROOT / "media/demo.mp4", dest / "demo.mp4")
    print(f"Built {dest}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=ROOT / "web/dist")
    build(p.parse_args().output)
