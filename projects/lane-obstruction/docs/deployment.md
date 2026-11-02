# Public Vercel release

Public URL: [football-analytics-self.vercel.app/lane-obstruction/](https://football-analytics-self.vercel.app/lane-obstruction/). Production tracks `main` through the existing GitHub/Vercel integration. Share this production URL; the original branch preview requires Vercel access.

The project was initially deployed from `codex/lane-obstruction-publication` on 29 October 2026. The public release reconciles that branch with current production and includes the replay in the portfolio build.

- [Public replay](https://football-analytics-self.vercel.app/lane-obstruction/)
- [GitHub source and methodology](https://github.com/prithvi-kaizen/football-analytics/tree/codex/lane-obstruction-publication/projects/lane-obstruction)
- [Draft pull request](https://github.com/prithvi-kaizen/football-analytics/pull/1)
- [Vercel release status](https://vercel.com/prithvirajs-projects-b40fa6af/football-analytics/4BApXKbHs58hyu4R2kBqGfGeUhZ7)

Validation: all 22 analytical tests passed; the full portfolio built from the latest remote main in an isolated temporary checkout; every local viewer documentation destination exists in the static bundle. The Vercel bot supplied the exact preview hostname and Ready status. Per the deployment skill, the deployed site was not fetched for verification.

The installed Vercel CLI had no saved credentials. The skill's older claimable-upload endpoint returned CLI setup guidance instead of a deployment. Publishing through the existing GitHub/Vercel integration succeeded without needing a new token. No credentials, raw tracking cache or unrelated workspace changes were published.

`python3 scripts/build_website.py` packages this project independently to `dist/`. In the repository integration, the root build invokes this script with a `/lane-obstruction/` output directory. The entry redirects to `outputs/viewer.html` so the original relative documentation links remain correct. Static hosting needs no analytics packages, paid API or runtime secrets.
