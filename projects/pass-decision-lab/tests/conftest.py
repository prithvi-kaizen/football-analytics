"""Deliberately synthetic fixtures exercise edge cases, not football findings."""

from copy import deepcopy

import pytest


@pytest.fixture
def match():
    return {"match_id": 1, "tournament": "Synthetic test", "date": "2024-01-01", "label": "Fixture only"}


@pytest.fixture
def events():
    # Player 2 acted two seconds before player 1's pass; never use a future receipt.
    return [
        {
            "id": "prior",
            "index": 1,
            "period": 1,
            "timestamp": "00:00:08.000",
            "minute": 0,
            "second": 8,
            "type": {"name": "Ball Receipt*"},
            "team": {"id": 1, "name": "Fixture"},
            "player": {"id": 2, "name": "Synthetic recipient"},
            "location": [50, 40],
            "possession": 1,
        },
        {
            "id": "pass",
            "index": 2,
            "period": 1,
            "timestamp": "00:00:10.000",
            "minute": 0,
            "second": 10,
            "type": {"name": "Pass"},
            "team": {"id": 1, "name": "Fixture"},
            "player": {"id": 1, "name": "Synthetic passer"},
            "location": [40, 40],
            "possession": 1,
            "pass": {
                "recipient": {"id": 2, "name": "Synthetic recipient"},
                "height": {"name": "Ground Pass"},
                "body_part": {"name": "Right Foot"},
                "end_location": [53, 40],
                "length": 13,
                "angle": 0,
            },
        },
    ]


@pytest.fixture
def frames():
    return deepcopy(
        [
            {
                "event_uuid": "pass",
                "visible_area": [0, 0, 120, 0, 120, 80, 0, 80, 0, 0],
                "freeze_frame": [
                    {"teammate": True, "actor": True, "keeper": False, "location": [40, 40]},
                    {"teammate": True, "actor": False, "keeper": False, "location": [51, 40]},
                    {"teammate": True, "actor": False, "keeper": False, "location": [70, 20]},
                    {"teammate": False, "actor": False, "keeper": False, "location": [45, 42]},
                ],
            }
        ]
    )
