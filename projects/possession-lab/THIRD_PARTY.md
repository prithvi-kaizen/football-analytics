# Attribution and boundaries

Original Possession Lab software is released under the MIT licence in LICENSE.

- The unchanged possession scorer, reference baseline and games.py originate from
  https://github.com/metrica-sports/more-than-a-hack-2027 at commit
  f8f2629ff1e0985f81d7e59d8413678514ee1530. Their upstream MIT notice is included
  as UPSTREAM-LICENSE.txt in the browser Python archive. Code licensing does not
  license competition match assets; none are present in the explorer.
- Anonymized public tracking excerpts originate from Metrica Sports' public sample
  repository, https://github.com/metrica-sports/sample-data at commit
  e706dd506b360d69d9d123d5b8026e7294b13996. The source README invites public use with
  attribution. Its dataset is not relicensed under Possession Lab's code licence.
  Only the first 1,000 frames of each public CSV sample match are included in the
  static demonstration. Full source-file hashes and coordinate conventions are
  recorded in provenance.json. No trusted possession truth accompanies these clips.
  The playground additionally carries full-precision adapter outputs for those same
  excerpts so observation corruption is applied before display rounding. Loss and
  noise are simulated interventions, not defects attributed to the source dataset.
- Browser Python runs through Pyodide 0.29.2 and its pinned package distribution,
  https://pyodide.org/en/0.29.2/. Pyodide and its numerical dependencies retain
  their own licences. Runtime files are vendored from the version-pinned jsDelivr
  distribution with a SHA256 manifest. PYODIDE-LICENSE.txt accompanies them and
  wheel archives retain their dependency notices. No API key or paid inference
  service is used.

No competition footage, gated tracking, private evaluation logs or restricted
derived extracts are included. Public sample tracking is not competition ATD.
