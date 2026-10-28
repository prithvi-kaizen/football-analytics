Can body orientation help explain what happens after a player receives the ball?

I built Open Body to explore this using SkillCorner’s open body-pose and tracking data, released with PySport.
It tests whether shoulder direction helps predict a successful forward pass within two seconds, beyond what position and pressure tell us. The interactive pitch and 3D skeleton let you replay real receptions and inspect the measurements.

I analysed 1,312 receptions across two matches. Adding orientation improved prediction scores, but the results remain inconclusive and mixed for midfielders.

⛳️ My main learnings:
➤ Matching timestamps doesn’t guarantee that pose and tracking positions agree.
➤ Shoulder direction is an estimate, not a measure of where a player is looking.
➤ Better prediction scores across two matches don’t prove a wider or causal benefit.

Built with Python, pandas, NumPy and scikit-learn, with a browser version deployed on Vercel.

Live project : https://open-body-seven.vercel.app
GitHub and methodology : https://github.com/prithvi-kaizen/football-analytics/tree/codex/open-body/projects/open-body

I’d welcome feedback on how to improve the reception-outcome measure.

#FootballAnalytics #SportsAnalytics #Python
