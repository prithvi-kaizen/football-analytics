# LinkedIn

How often does a corner stay dangerous after the first delivery?

I built The Corner That Never Ended to follow what happens after the first delivery, using StatsBomb Open Data from men's Euro 2024 and Women's Euro 2025.
It separates a defender's touch from a completed turnover, then tracks attacking recoveries, later shots, box entries and opposition breaks. The interactive explorer lets you change the time window and follow three real corners.

Across 817 corners in 82 matches, the attacking team had a recorded action after defensive contact on 389 corners (47.6%) within 15 seconds. A recovered second phase produced a shot on 126 corners (15.4%).

⛳️ My main learnings:
➤ A clearance event does not mean the defending team has possession.
➤ At 15 seconds, 184 classifiable shots came after the first ball, compared with 69 first-ball shots.
➤ Another 75 shots have uncertain phase because attacking and defending events share a timestamp.

These are historical Euro matches. They do not measure the effect of the Premier League's 2026/27 refereeing guidance.

Built with Python and JavaScript, with the interactive explorer deployed on Vercel.

Live project : **https://football-analytics-self.vercel.app/corner-second-phase/**
GitHub and methodology : **https://github.com/prithvi-kaizen/football-analytics/tree/main/projects/corner-second-phase**

I'd welcome feedback on where to draw the line between the first ball and a second phase when event timestamps overlap.

#FootballAnalytics #SportsAnalytics #Python

# X thread

1/ A defender touched the corner. Did the attack actually end? I reconstructed 817 corners across Euro 2024 and Women's Euro 2025 to follow the second ball.

2/ At 15 seconds, 389 corners (47.6%) had an attacking action after defensive contact. A clearance event alone never counts as a completed turnover in this analysis.

3/ Recovered second phases produced shots on 126 corners. There were 69 first-ball shots, 44 unopposed-continuation shots and 140 shots after a contested recovery. Another 75 shots have unknown phase because event timestamps overlap.

4/ Nine confirmed defensive turnovers led to an opposition shot within a further 15 seconds. Rare, and descriptive. The explorer has three real examples plus 10/15/20/30-second windows: https://football-analytics-self.vercel.app/corner-second-phase/

5/ The source is historical StatsBomb Euro data. It cannot measure the effect of the Premier League's 2026/27 refereeing guidance. Methods: https://github.com/prithvi-kaizen/football-analytics/tree/main/projects/corner-second-phase
