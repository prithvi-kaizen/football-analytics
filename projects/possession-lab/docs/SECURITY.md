# Scope and restricted-data boundary

This repository is a preparation environment for synthetic inputs and Metrica's public
anonymized samples. Its Python code has no network client, telemetry, model API, dataset
discovery or recursive asset scanner. The only public labels ever evaluated are the supplied
five-minute labels against the four *unchanged official baseline files*. New inference code
takes arrays only, never truth paths. No event-derived possession truth is constructed.

Do not place competition assets, extracts, clipped footage, derived tracking, private evaluation
results or private logs anywhere in this workspace, its children, or another directory accessible
to Codex. `.gitignore` is not an access-control boundary. Do not set MTAH_DATA_DIR in this chat
or ask Codex to run the official loaders once restricted assets exist. No restricted input was
accessed or requested during this preparation.

When access arrives, a human should use a separate machine/environment that Codex cannot access,
copy only reviewed source code there, and implement `TrackingAdapter.load()` locally. The
`OfficialAdapter` here intentionally raises an error; the canonical batch also only accepts
synthetic/public provenance. Enabling restricted provenance belongs in that separate environment,
not in this chat. Do not bring private logs, predictions or debug outputs back into this workspace.

The future adapter should use the organisers' ATD loader and explicit metadata mapping of teams,
translate ATD frame_id minus one, preserve all tactical rows and NaNs, record pitch dimensions,
and assign period IDs from published half ranges. Optional Smart Tagging should arrive through
a separate evidence channel with confidence/ambiguity masks and explicit Team mapping, not as
labels and not by copying whole phase intervals. Validate with fabricated fixtures first.
If optional kloppy is introduced then, resolve/pin it in that human-run environment; it is not
installed or required by this lab. The public sample CSV adapter is not reusable as an ATD parser.

Only public/synthetic validation receipts are safe to share here. This document does not grant
permission to upload anything restricted to any hosted service. No paid API is used.
