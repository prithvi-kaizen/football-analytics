# Source audit

The project uses the pinned StatsBomb Open Data revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, the same verified source as TacticAI Lite. The provider's competitions inventory identifies men's UEFA Euro 2024 as competition 55, season 282 (51 matches) and UEFA Women's Euro 2025 as competition 53, season 315 (31 matches). All 82 event files are present in the local verified cache. Event IDs and indexes are unique per match; the audit records no missing clocks, backwards period clocks, or missing possession fields. Each cache file has a receipt containing its source URL, revision and SHA-256 digest; `analyse.py` refuses missing or mismatched receipts.

Actual event samples show `Clearance` by the defending team while `possession_team` still names the attacker. Defensive `Duel`, `Block` and keeper events also appear inside attacking possessions. Some attacking shots have the same timestamp as a defender duel or block. These observations motivate separate contact, controlled possession and unresolved-phase states. `index` orders the feed, but it does not establish a physical before/after relation among events with identical timestamps.

Only provider event data are used. The 360 snapshots in TacticAI Lite are unnecessary for second-ball sequence reconstruction and are not downloaded by `src/fetch.py`. The dataset does not include the Premier League 2026/27. Match examples are derived summaries, not redistributed event rows.

The competitions inventory also advertises men's Euro 2020, Women's Euro 2022, World Cup 2022, Women's World Cup 2023 and Women's Super League 2023/24. These are plausible external validation sets, but their event files were not downloaded or audited for this release, so no outcome claims are made about them.
