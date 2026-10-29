# Vercel preview release

The existing repository's Vercel integration deployed branch `codex/lane-obstruction-publication`. Vercel reported Ready for release commit `0d81e86507a9fd1ab6bc3b0864185eb31e9cedb5` on 29 October 2026. No production merge was made.

- [Replay preview](https://football-analytics-git-cod-ae6a65-prithvirajs-projects-b40fa6af.vercel.app/lane-obstruction/)
- [GitHub source and methodology](https://github.com/prithvi-kaizen/football-analytics/tree/codex/lane-obstruction-publication/projects/lane-obstruction)
- [Draft pull request](https://github.com/prithvi-kaizen/football-analytics/pull/1)
- [Vercel release status](https://vercel.com/prithvirajs-projects-b40fa6af/football-analytics/4BApXKbHs58hyu4R2kBqGfGeUhZ7)

Validation: all 22 analytical tests passed; the full portfolio built from the latest remote main in an isolated temporary checkout; every local viewer documentation destination exists in the static bundle. The Vercel bot supplied the exact preview hostname and Ready status. Per the deployment skill, the deployed site was not fetched for verification.

The installed Vercel CLI had no saved credentials. The skill's older claimable-upload endpoint returned CLI setup guidance instead of a deployment. Publishing through the existing GitHub/Vercel integration succeeded without needing a new token. No credentials, raw tracking cache or unrelated workspace changes were published.

`python3 scripts/build_website.py` packages this project independently to `dist/`. In the repository integration, the root build invokes this script with a `/lane-obstruction/` output directory. The entry redirects to `outputs/viewer.html` so the original relative documentation links remain correct. Static hosting needs no analytics packages, paid API or runtime secrets.
