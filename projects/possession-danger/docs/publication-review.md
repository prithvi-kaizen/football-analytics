# Publication review, 23 October 2026

The research pipeline and local Streamlit review are recorded in [validation.md](validation.md) and [design-review.md](design-review.md). This receipt covers the additional static Vercel companion.

## Release checks

- All 39 project tests passed with the downloaded real data, including five publication tests.
- An isolated clean checkout passed 35 tests with four cache-dependent tests explicitly skipped. The repository-root standard-library build successfully restored all five published project routes without source downloads.
- The static builder verifies archive, decoded snapshot, asset and download hashes, and rejects unsafe release paths.
- Browser aggregation matches the reviewed Python held-out team statistics. Tests also cover weighted denominators, absent score-state exposure and style boundaries.
- The public field allowlist excludes raw event records, players, event identifiers and event coordinates. Source caches and local analytical CSVs are Git-ignored. Provider terms and logo and the Plotly notice are retained.
- The deployed companion is a static explorer of reviewed results. Recalculation and event-coordinate inspection belong to the local Python/Streamlit application.

## Interface review and limits

The user approved the warm paper, charcoal, teal/rust direction and antislop checks during implementation. The browser companion follows the same analytical hierarchy, with native labelled controls, visible focus, exact evidence tables, explicit loading/error messages and a collapsible narrow-screen filter region.

A local rendered desktop review confirmed the default Barcelona statistics and chart/table display. Browser checks exercised training (192 fixtures), all-match (240 fixtures), held-out (48 fixtures), and Real Madrid focus filters. Subsequent automated browser interaction was stopped by the account usage limit in the automatic approval reviewer. This was a review-availability failure, not an unsafe-action determination. No workaround was used.

The remaining browser match-lab, mobile, keyboard and download walkthroughs are **incomplete** for this static companion. The earlier Streamlit desktop/mobile screenshots do not establish a static-site delivery-gate pass. Source inspection, deterministic builds and numerical tests supplement but do not replace those walkthroughs. Do not claim an exhaustive accessibility audit or a complete static UI gate.

## Published release

Source release: [`53bac3f2864472df0bf30f91d0512b382a9113aa`](https://github.com/prithvi-kaizen/football-analytics/commit/53bac3f2864472df0bf30f91d0512b382a9113aa), pushed to `main` on 23 October 2026. GitHub's combined commit status reports **Vercel: success** for [deployment EdgUwGxTuBqChY7YZyvWNNQppdQy](https://vercel.com/prithvirajs-projects-b40fa6af/football-analytics/EdgUwGxTuBqChY7YZyvWNNQppdQy). Public route: [Possession danger](https://football-analytics-self.vercel.app/possession-danger/).

The source and deployment status were checked through the GitHub connector. No production-page fetch or complete production browser walkthrough is claimed. The GitHub Actions workflow is committed, but no workflow run was returned for this commit at publication time; local test evidence above is separate from CI execution.
