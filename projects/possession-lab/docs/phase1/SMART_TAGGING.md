# Future Smart Tagging contract

Design source: the pinned official `DATA.md`, read during this phase. No restricted XML was
available, requested, ingested or reconstructed. No tags were generated for actual match frames.

The public specification describes automatic SportsCode intervals, not corrected possession
labels. Start/end times are seconds from tactical video zero, converted with `round(seconds *
fps)` to half-open frame intervals. ATD uses a separate one-based frame ID; do not apply its
minus-one adjustment to tagging times. Broadcast is on another timeline and is unsupported here.

`tagging_interface.py` defines `PhaseContextProvider.intervals() -> Sequence[PhaseInterval]` and
an in-memory validator for records shaped like the official standard-library loader output.
The future human-run adapter outside Codex can supply those records, but no loader/path access
is implemented here. Tests contain fictional source-side names and short fabricated timelines.

Each interval preserves start/stop, normalized code, optional H/A team hint, optional half,
all normalized tag pairs, and optional confidence. Key handling is case-insensitive: the public
schema uses `Team`, `Half`, `Type`, upper-case codes and title-case values. Team mapping must
be supplied explicitly. N/A and absent Team become None; unmapped names raise an error. Half
tags are strings and are validated against a supplied period axis. Out-of-range times raise
an error rather than being silently clamped. No match-specific frame constants are introduced.

Confidence is None by default: the published export provides no calibrated probability.
Overlapping and conflicting intervals are retained separately. No last-write-wins rule produces
a hidden pseudo-label. A set-piece phase can include time before/after a restart; the interval
does not identify the exact live/dead transition. A team tag is phase context, and defensive
codes may refer to the team without the ball. Neither the absence nor presence of a phase is
direct live/dead truth. No interval is copied into a possession-label array by this interface.

Future fusion should first define code-specific meanings and conflict/coverage masks on new
synthetic event channels, then calibrate reliability only using legitimate other-match labels.
Treat code, team, half, timing uncertainty and source quality separately. Do not add a conditional
team hint to dead-ball ownership. Missing tags provide no evidence, not D. Suggested integration
is a bounded optional additive evidence term in the two hierarchy heads; its weight must remain
zero until validated. No tag channel or tag weights were used in this phase's evaluation.

Restricted integration remains prohibited in this Codex-accessible lab. Implement and run it only
in the separate human-controlled environment described in `../SECURITY.md`; do not bring private
inputs, derived extracts or logs back into this workspace or any hosted model.
