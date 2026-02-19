NCAA Prediction Modules - README

What I added

1) ncaa_total_predictor.py
   - Simple, transparent total predictor that:
     - Loads cached team stats from team_stats_cache.json when present
     - Falls back to league-average proxies if no data
     - Combines team offensive PPG, opponent PPG, pace (possessions), home/away boost, and recent form
     - Returns predicted_total, component breakdown, and an uncertainty score (0-1)
   - evaluate_against_market(predicted_total, market_total) returns edge, confidence (20-90), and side (OVER/UNDER)

2) ncaa_spread_predictor.py
   - Simple spread predictor that:
     - Loads cached team stats when available
     - Uses offensive/defensive PPG, recent margin, and a home-court advantage (~3.5 pts)
     - Applies simple injury adjustments if provided
     - Returns predicted_margin (positive -> home by X), confidence (20-92), suggested side, and details dict

3) Updates to real_betting_model.py
   - Replaced heuristic spread/total edge/confidence calculations with calls to the new predictors
   - For robustness, the code falls back to previous heuristics if the predictors fail

Design notes / data sources

- Primary data source: local cache file team_stats_cache.json (not included). If you have a separate fetcher (sports-reference scraper or NCAA API fetcher), populate that cache with the following per-team shape:
  {
    "Team Name": {
      "ppg": 75.2,
      "opp_ppg": 70.1,
      "poss": 70.5,
      "home_ppg":78.1,
      "away_ppg":72.0,
      "recent_ppg": [76,74,80,70,72],
      "recent_margin": [5,-2,8,3,1],
      "mov": 5.2
    }
  }

- If you don't have that cache yet, the predictors use league-average fallbacks so the system runs without crashing; confidence will reflect higher uncertainty.

Caching strategy

- team_stats_cache.json should be updated once per day at most. The predictors read this file and write a cache when using stubs.
- If you build a separate fetcher (recommended), make it update team_stats_cache.json and include a timestamp to allow selective refresh.

Expected accuracy & next steps

- These are lightweight linear heuristic models meant to replace clearly bogus heuristics. Expect modest real-world predictive power (~break-even to slightly positive) until:
  - You populate the team stats cache with real data
  - Add a simple regression calibrated on historical lines vs outcomes
  - Include injuries and lineup changes programmatically

- Next practical improvements:
  - Implement a daily fetcher using sports-reference (free) to populate team_stats_cache.json
  - Add simple Elo or RAPM-style ratings for spread predictions
  - Track historical predictions vs outcomes to calibrate confidence and thresholds

Testing

- Run real_betting_model.py; it will import the new predictors and use them when building picks. If the cache is empty, the predictors will use fallbacks and set lower confidence.

Contact

- This was built as the subagent task to replace the fake heuristics. If you want, I can next implement a sports-reference fetcher to populate the cache and run a quick calibration sweep on historical games.