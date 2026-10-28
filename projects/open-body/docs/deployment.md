# Static deployment

The website contains the validated standalone viewer, real clip data already embedded in its HTML, the 30-second rendered demo, the results plot and the original SkillCorner MIT notice. No analytics runtime or raw match archives are uploaded to the web host.

Build the static package from the project directory:

```bash
python3 scripts/build_website.py --output site
```

`site/index.html` is copied byte for byte from `outputs/viewer.html`. `site/build-manifest.json` records hashes. Re-run `python -m open_body viewer` first only when the analysis or viewer sources have changed.

Deploy `site/` with the authenticated Vercel CLI. Deployments default to preview. The installed skill's former unauthenticated endpoint now returns CLI sign-in guidance instead of deploying, so a normal Vercel sign-in is required. CLI authentication files stay outside the project and public repository.

The project's source and methodology can be published on the `codex/open-body` branch of the existing football-analytics repository without changing unrelated local work or the production portfolio build. The main branch is not updated by this isolated publication.

## Published deployment, 28 October 2026

Live viewer: https://open-body-seven.vercel.app

Source and methodology: https://github.com/prithvi-kaizen/football-analytics/tree/codex/open-body/projects/open-body

After normal CLI sign-in, `vercel deploy /private/tmp/open-body --yes` successfully uploaded the six-file static package. No `--prod` flag was passed; Vercel treated the new project's first deployment as production and assigned the public alias above. No existing portfolio deployment was overwritten.

The Vercel CLI returned a completed build and alias. Deployment readiness is checked through Vercel's metadata; the deployment skill prohibits fetching the deployed URL for an additional smoke check. The identical standalone HTML and real-data visualization were tested locally before upload.
