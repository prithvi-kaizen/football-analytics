import csv
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from marking_handoffs.data import load_match


class LoaderTests(unittest.TestCase):
    def fixture(self, root, records):
        m = dict(id=1, pitch_length=105, pitch_width=68, home_team=dict(id=1), away_team=dict(id=2),
                 home_team_side=["left_to_right", "right_to_left"],
                 match_periods=[dict(period=1, start_frame=0, end_frame=20)],
                 players=[dict(id=1, team_id=1, player_role=dict(acronym="CF")),
                          dict(id=2, team_id=2, player_role=dict(acronym="CB"))])
        (root / "1_match.json").write_text(json.dumps(m))
        (root / "1_tracking_extrapolated.jsonl").write_text("\n".join(json.dumps(r) for r in records))
        (root / "1_phases_of_play.csv").write_text("match_id,frame_start,frame_end,period,team_in_possession_id,attacking_side\n1,0,6,1,1,left_to_right\n")

    def records(self):
        return [dict(frame=f, timestamp=f, period=1, possession=dict(group="home team", player_id=1),
                     ball_data=dict(x=0, y=0), player_data=[dict(player_id=1, x=f*.01, y=0, is_detected=True),
                                                        dict(player_id=2, x=2, y=0, is_detected=False)]) for f in range(6)]

    def test_extrapolation_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, self.records())
            d = load_match(root, 1)
            self.assertTrue(d["detected"][:, 0].all())
            self.assertFalse(d["detected"][:, 1].any())
            self.assertTrue(np.isfinite(d["velocity"][3:]).all())
            self.assertEqual(d["audit"]["detection_fraction"], .5)

    def test_duplicate_frame_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.records()
            records[3]["frame"] = 2
            self.fixture(root, records)
            with self.assertRaisesRegex(ValueError, "frame"):
                load_match(root, 1)

    def test_duplicate_player_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.records()
            records[0]["player_data"].append(records[0]["player_data"][0])
            self.fixture(root, records)
            with self.assertRaisesRegex(ValueError, "Duplicate player"):
                load_match(root, 1)

    def test_missing_frame_invalidates_velocity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.records()
            del records[2]
            self.fixture(root, records)
            d = load_match(root, 1)
            self.assertTrue(np.isnan(d["velocity"][3:]).all())
            self.assertEqual(d["audit"]["missing_source_frames"], 1)

    def test_phase_period_conflict_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.records()
            records[3]["period"] = None
            records[3]["player_data"] = []
            self.fixture(root, records)
            d = load_match(root, 1)
            self.assertEqual(d["phase"][3], -1)
            self.assertEqual(d["audit"]["phase_period_mismatch_frames"], 1)

    def test_speed_jump_excludes_both_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.records()
            records[3]["player_data"][0]["x"] = 20
            self.fixture(root, records)
            d = load_match(root, 1)
            self.assertFalse(d["clean"][2:5, 0].any())


if __name__ == "__main__":
    unittest.main()
