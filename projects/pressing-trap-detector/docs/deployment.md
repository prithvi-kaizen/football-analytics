# Website deployment

The repository includes an integrity-checked static release under `web/`. The HTML is the same compiled dashboard used in local verification, with its transient local chat-routing metadata removed. The full reviewed data is stored losslessly as `snapshot.json.gz`. No raw event files, account tokens, local caches or workspace paths are required to deploy it.

## Local build

From the repository root:

```sh
python3 projects/pressing-trap-detector/scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory projects/pressing-trap-detector/dist
```

The build verifies the HTML, compressed archive and decompressed snapshot against SHA-256 hashes before writing the output. It uses only Python 3's standard library; it does not fit a model or download data at build time.

## Vercel

Import `prithvi-kaizen/football-analytics` into your Vercel account with the repository root as the Root Directory. The root `vercel.json` sets:

| Setting | Value |
| --- | --- |
| Framework | Other / none |
| Install command | Empty |
| Build command | `python3 projects/pressing-trap-detector/scripts/build_website.py` |
| Output directory | `projects/pressing-trap-detector/dist` |
| Environment variables | None |

The website is a static, historical snapshot. It requires no server functions, database or live StatsBomb connection. Complete-view query parameters preserve the selected team, match and replay when sharing links. Viewer presentation changes remain in that browser; this Vercel release does not provide shared owner editing or hosted data refresh APIs.

If deploying directly from an authenticated Vercel CLI:

```sh
vercel deploy
```

This creates a preview. Use `vercel deploy --prod` only when you intend to publish to your production project domain. A preview created through the no-login deployment flow must be claimed into your account before you can manage its project. A one-off preview is not automatically linked to GitHub and does not establish automatic deployment on push.

Configuration references: [Vercel static configuration](https://vercel.com/docs/project-configuration/vercel-json), [configuring a build](https://vercel.com/docs/builds/configure-a-build).

## Refreshing the release

The committed bundle is a verified build, not a replacement UI source tree. The authored React/CSS lives under `dashboard/src/`. The original compilation uses the Codex Data app runtime; that optional authoring runtime is not vendored into this public portfolio repository. A fresh clone can reproduce the Python analysis and deploy the bundled website without it, but compiling UI changes requires that runtime.

In the local authoring environment, rerun the extraction and `sync_dashboard.py`, complete the dashboard build following its authoring guide, then run:

```sh
python3 scripts/package_website.py
python3 scripts/build_website.py
```

Commit the updated `web/` artifacts and authored changes together. `package_website.py` refuses an input build whose hashes do not match its manifest. Do not manually edit the compiled HTML or the compressed reviewed snapshot.
