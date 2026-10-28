# Static deployment

The website contains the validated standalone viewer, real clip data already embedded in its HTML, the 30-second rendered demo, the results plot and the original SkillCorner MIT notice. No analytics runtime or raw match archives are uploaded to the web host.

Build the static package from the project directory:

```bash
python3 scripts/build_website.py --output site
```

`site/index.html` is copied byte for byte from `outputs/viewer.html`. `site/build-manifest.json` records hashes. Re-run `python -m open_body viewer` first only when the analysis or viewer sources have changed.

Deploy `site/` with Vercel. Deployments default to preview. The local Vercel CLI has no stored credentials, so publication uses the installed Vercel deployment skill's claimable-preview fallback. Its ownership claim URL is kept outside the public repository and LinkedIn draft.

The project's source and methodology can be published on the `codex/open-body` branch of the existing football-analytics repository without changing unrelated local work or the production portfolio build. The main branch is not updated by this isolated publication.
