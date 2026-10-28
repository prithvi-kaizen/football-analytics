---
license: mit
pretty_name: SkillCorner Open Data — Body Pose
language:
  - en
tags:
  - football
  - soccer
  - sports-analytics
  - tracking-data
  - body-pose
  - biomechanics
size_categories:
  - 1M<n<10M
---

# SkillCorner Open Data — Body Pose

3D body-pose data derived from broadcast video, released alongside the
[SkillCorner Open Data](https://github.com/SkillCorner/opendata) repository as a
joint initiative between [SkillCorner](https://skillcorner.com) and
[PySport](https://pysport.org/).

> **Initial testing release.** Two matches, published so the community can work
> with the format and tell us what is useful before we consider a wider release.
> Feedback is genuinely wanted — open an issue on the
> [opendata repo](https://github.com/SkillCorner/opendata/issues) or reply in the
> Community tab here.

## What is in here

| File | Match | Size |
|---|---|---|
| `raw/1925299.jsonl.zip` | Brisbane Roar v Perth Glory, 2024-12-21 | 595 MB |
| `raw/1996435.jsonl.zip` | Sydney FC v Adelaide United, 2025-02-01 | 614 MB |

Each archive contains one `.jsonl` file — one JSON object per video frame,
about 3.3 GB uncompressed. Both matches are from the Australian A-League
2024/2025 season (competition edition 870), and **both already have tracking,
dynamic events and phases of play published** in the opendata repo, so pose can
be joined to the rest of the data for the same games.

## Record structure

One object per frame:

```json
{
  "frame": 2438,
  "timestamp": "00:01:36.52",
  "period": 1,
  "ball_data": {"x": 0.35, "y": -22.22, "z": 7.074, "is_detected": true},
  "possession": {"player_id": null, "group": "away team"},
  "image_corners_projection": {"x_top_left": -44.26, "y_top_left": 39.0, "...": "..."},
  "player_data": [
    {
      "player_id": 809166,
      "x": -17.36,
      "y": -22.06,
      "is_detected": true,
      "joints": {
        "lAnkle": {"xyz": [-25.042, 0.86, 0.204], "p90_mae_cm": 12.39},
        "lEar":   {"xyz": [-25.016, 0.815, 1.809], "p90_mae_cm": 9.29},
        "...": "..."
      }
    }
  ]
}
```

Coordinates are in **metres**, origin at the centre of the pitch, x along the
long axis and y along the short axis — the same convention as the tracking data
in the opendata repo.

> **`z` is not a height above the pitch.** It is accurate *relative to the
> player's centroid*, but not necessarily in the pitch coordinate system, so it
> can be negative. Treat it as pose geometry rather than elevation. This will
> improve with future Body Pose enhancements.

Note that `ball_data` also carries `z`, which the 10 fps tracking files do not.

The 2D `x`/`y` positions in this file are the standard tracking positions
**interpolated** up to 25 fps, not native 25 fps measurements.

### The 29 joints

`nose`, `neck`, `lEye`, `rEye`, `lEar`, `rEar`, `lShoulder`, `rShoulder`,
`lElbow`, `rElbow`, `lWrist`, `rWrist`, `lThumb`, `rThumb`, `lPinky`, `rPinky`,
`midHip`, `lHip`, `rHip`, `lKnee`, `rKnee`, `lAnkle`, `rAnkle`, `lHeel`,
`rHeel`, `lBigToe`, `rBigToe`, `lSmallToe`, `rSmallToe`

### `p90_mae_cm`

Every joint carries its own accuracy estimate: the 90th-percentile mean absolute
error in centimetres. Typical values run **7–15 cm**, varying by joint — torso
and head landmarks are more reliable than extremities. Use it to filter: joints
with a high `p90_mae_cm` should not be trusted for fine-grained biomechanics.

This also means positions are reported to millimetre precision but are only
accurate to a handful of centimetres. Do not read more into the decimals than
the error estimate supports.

## Frame rate — read this before joining to tracking

**Pose is 25 fps. The tracking data in the opendata repo is 10 fps.** The frame
numbering differs accordingly: this file runs to frame 153,252 for a match whose
tracking file ends at frame 61,300.

Both cover the same wall-clock time, so:

```
pose_frame = 2.5 * tracking_frame
```

Every **5th pose frame** (a multiple of 5) lands exactly on an **even-numbered
tracking frame**. Those are the frames where pose and tracking align without
interpolation.

## Coverage

Pose is not available for every player in every frame — it requires the player
to be visible and resolvable in the broadcast image. For match 1925299:

| | |
|---|---|
| Frames in file | 153,252 |
| Frames with at least one pose | 106,757 (69.7%) |
| Player-frames total | 4,902,560 |
| Player-frames with pose | 1,540,715 (31.4%) |
| Average players with pose, per frame that has any | 14.4 |
| Total joint observations | 44,680,735 |

A player's `joints` field is `null` when pose could not be resolved for them in
that frame, while their `x`/`y` position may still be present. Expect gaps when
players are off-camera, occluded, or in a crowd.

## Limitations

* Body Pose is only provided for detected players.
* Position on the z-axis is accurate relatively to the player's centroid, but
  not necessarily in the pitch coordinate system. This will come with future
  Body Pose enhancements.
* XY Tracking data and Body Pose are generated separately. This can cause minor
  misalignments between the XY attributes (positions, `is_detected` flag) and
  the Body Pose joints.

## Loading

The archives are large, so download rather than stream:

```python
import json
import zipfile

from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="SkillCorner/opendata-bodypose",
    filename="raw/1925299.jsonl.zip",
    repo_type="dataset",
)

with zipfile.ZipFile(path) as z:
    with z.open("1925299.jsonl") as fh:
        for line in fh:
            frame = json.loads(line)
            for player in frame["player_data"]:
                if player["joints"]:
                    ...  # 29 joints, each with xyz and p90_mae_cm
```

Reading the whole match into memory as JSON is not advisable — process it frame
by frame, or convert the parts you need into a columnar format first.

## Related data

The rest of the open dataset — broadcast tracking, dynamic events, phases of
play and season aggregates for 20 A-League matches — lives at
[github.com/SkillCorner/opendata](https://github.com/SkillCorner/opendata),
along with tutorials.

## Licence and credit

MIT, matching the opendata repository.

If you use this data we kindly ask that you credit SkillCorner, and we would
love to hear what you build — tell us on [X/Twitter](https://twitter.com/skillcorner).
