# Public explorer: first end-to-end release

The project now presents possession inference as an inspectable research problem,
with no new model or competition-performance claim. Four core methods, four
unchanged official reference votes and six historical ablations run through one
bounded Python interface. The existing research code and scorer are unchanged.

## Experiences

- Model comparison: six deterministic synthetic examples and two public Metrica
  excerpts; physical pitch playback, frame stepping, model transitions, error
  navigation, aligned state timelines and precisely defined scenario metrics.
- Failure playground: the original Python modules execute in a Web Worker using
  Pyodide. Seed, missing interval, noise, random ball loss and selected mechanisms
  change observations while preserving the hidden schedule. Saved examples appear
  before runtime initialization. No inference server or paid API is required.
- Observability: two exact tracking twins, opposite hidden target states, and
  optional independently informative noisy event cues or shared null tags. Event
  intervals are inspectable. Pair scores are explicitly illustrative, with no
  benchmark uncertainty or real-match generalization claim.

Public samples contain the first 1,000 frames of each CSV game. Their truth and
accuracy metrics are null. Provenance carries source commits, original file
hashes, attribution, coordinate conventions and the excerpt boundary. Predictions
are decoded on the excerpt, so edge behaviour may differ from a complete match.

## Verification

165 Python tests pass, including historical reproduction and the new JSON
interface contracts. The build verifies 408 frozen Phase 1 files and official
source integrity. The public bundle verifier checks all 14 JSON fixtures, identical
observations, the null-evidence ceiling, public accuracy suppression, archive
allowlists and Python source hashes. Both JavaScript files pass Node syntax checks.

Browser testing covered all three experiences, all saved scenarios, both public
samples, model selection, timeline and frame navigation, playback, speed,
keyboard tabs, score disclosure, both themes and a 375 px narrow layout. The
browser successfully ran the default and changed settings using Python 3.13.2 /
NumPy 2.2.5. All 14 default displayed metric rows matched native Python 3.14.2 /
NumPy 2.5.4 to the displayed precision. This is a fixture check, not a claim of
universal cross-runtime numerical identity. A native-matching 3,025-row CSV was
also downloaded; subsequent download completion depends on browser handling.

The initial external CDN runtime load stalled in the preview. The release serves
the pinned runtime and numerical wheels from its own static output, validates
hashes during build, and retains runtime licence notices. This costs about 20 MB
of deployment payload. First use still needs loading time. The site works without
an account, uploads or any restricted data integration.

On the first hosted visit a transient wheel request left pandas uninstalled even
though Pyodide's loadPackage call resolved. Retrying initialization succeeded.
The worker now verifies numerical imports and automatically retries package
loading up to three times before offering the existing manual retry control.

## Reproduction and limits

Follow explorer/README.md and run scripts/reproduce_explorer.sh. The downloadable
source includes research modules, tests, frozen synthetic benchmark files, build
scripts and UI source. Full public datasets and competition assets are excluded.
The static output can be hosted separately; the supplied Sites manifest is not a
requirement of the research package.

The animations show observed coordinates only. The synthetic motion is simplified
and slot numbers are not player identities. HMM/hierarchy are offline decoders.
Browser device cost and accessibility have been smoke-tested, not audited across
all browsers or assistive technologies. No new trusted real possession labels or
new generalization estimates were created in this release.
