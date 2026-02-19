# System Audit V2 — Feb 18, 2026

## CRITICAL (must fix before tomorrow)
- [Finding]: build_pick_from_manual_odds uses an except branch that references/confuses variables and may produce an invalid confidence. File: real_betting_model.py: around "except Exception:" in build_pick_from_manual_odds. Impact: confidence can be set using an uninitialized variable path and the computed edge/confidence can be nonsensical, leading to wrong risk tiers and selection. Fix: simplify fallback and make explicit defaults. Example problematic code:

    except Exception:
        edge = abs(spread) * 0.4
        confidence = min(confidence if 'confidence' in locals() else 82, int(65 + (abs(spread) * 1.5)))
        details = {}

Replace with a safe, explicit fallback (e.g. confidence = int(min(82, 65 + abs(spread)*1.5))) and log the exception.

- [Finding]: Spread sign/normalization inconsistency between OddsAPI parsing and model prediction. File: real_betting_model.py: parse_spreads_market / build_pick_from_odds (SPREAD path). Impact: market_spread and predicted_margin use different sign conventions (home_spread negative when home favored), but edge is computed with abs() and no normalization; this can flip which side is considered edge. Fix: normalize market spread to a single convention (e.g. predicted_margin is home - away; market_spread should be parsed to same sign). Show sample code: in parse_spreads_market it returns 'home_spread': home_outcome.get('point', 0) which then used directly. Enforce: market_spread = -home_spread if home_outcome is favorite convention mismatch, or better: explicit comment and unit tests.

## HIGH (fix soon)
- [Finding]: TOTALS confidence scaling double-applies uncertainty inconsistently. File: real_betting_model.py: build_pick_from_odds (TOTALS path) lines where confidence = int(conf * (1 - uncertainty)). Impact: evaluate_against_market already returns a confidence in 20..90 range independent of uncertainty; multiplying by (1-uncertainty) without re-scaling may push confidence too low unpredictably. Fix: compute a single calibrated confidence formula in the predictor (ncaa_total_predictor) and pass it through; don't mix two independent confidence heuristics.

- [Finding]: _get_cache() and load_cache()/get_team functions assume two different cache shapes. Files: ncaa_total_predictor.py:_get_cache (returns raw.get('teams', raw)), ncaa_spread_predictor.py:_get_cache (same), but other callers sometimes call get_team(team_name) expecting entry presence; real_betting_model builds game_string like "Away @ Home" and manual odds keys may not match team naming. Impact: mismatches will trigger fallback stubs frequently (higher uncertainty) or miss manual overrides. Fix: add a canonicalize_team_name helper and document expected keys (strip punctuation, handle "St.", abbreviations) and use consistent cache shape. Also make manual odds keys tolerant (try short name and full name). 

## MEDIUM (improve when possible)
- [Finding]: ncaa_total_predictor.predict_total determines stub_count by checking t.get('poss', None) == 70.0 but the cache uses null for poss when unknown, and fallback entries exist later with poss=70.0 under different keys. File: ncaa_total_predictor.py: predict_total. Impact: uncertainty underestimation (stub_count stays 0) when many teams have poss=None; model will appear more confident than it should. Fix: treat None as missing and count those as stubs: if t.get('poss') is None: stub_count+=1.

- [Finding]: fetch_team_stats_stub() duplicated and contains unreachable code (two identical blocks, repeated docstring). File: ncaa_total_predictor.py top area. Impact: messy but not critical; remove duplicate definitions to avoid confusion.

- [Finding]: predict_spread baseline formula is unusual and lacks comments to justify weights. File: ncaa_spread_predictor.py baseline calculation. Impact: may bias margins; at minimum add comments and tests. Fix: either use standard (offense - opponent_defense) or document experiments.

- [Finding]: parse_moneyline_market and parse_spreads_market use substring matching of team names lowercased; this can fail on name variants (e.g. "LA Clippers" vs "Los Angeles Clippers"). File: real_betting_model.py parse_* functions. Impact: odds not found -> missing bets. Fix: implement fuzzy or canonical mapping (alias map).

## LOW (nice to have)
- [Finding]: Many try/except blocks swallow exceptions silently (e.g. parse_* and extract_fanduel_only). File: real_betting_model.py. Impact: debugging is harder. Fix: log exceptions at DEBUG level with context.

- [Finding]: team_stats_cache.json contains many null 'poss'/'fga' values. File: team_stats_cache.json. Impact: pace proxy is weak; consider computing possessions from play-by-play or using league averages at team-level fill. Fix: fill missing pace values during cache build or a preprocessing step.

- [Finding]: real_betting_model uses hard-coded OddsAPI key in source. File: real_betting_model.py top-level. Impact: secrets in repo. Fix: move to env var / secrets store.

## GOOD (things working well)
- The team caches (team_stats_cache.json and nba_team_stats_cache.json) contain realistic-looking PPG/margins and recent_ppg arrays of length 5 in most entries — matches expected ranges (NCAA 60–95, NBA 100–125).
- real_betting_model.get_games_for_sport implements robust retry logic and constrains picks to TODAY (good safety).
- generate_all_picks organizes and filters bets by confidence and prints clear summaries; separation by bet_type supports balanced selection and learning-phase behaviour.
- ncaa_spread_predictor and ncaa_total_predictor return uncertainty estimates (good concept) — just inconsistent application.

## RECOMMENDATIONS
- Normalize team naming across all components (OddsAPI parsing, caches, manual overrides). Implement a canonicalize_team_name() used everywhere; include an alias mapping for common variants (LA/Los Angeles, St./Saint, abbreviations).
- Centralize confidence calculation inside predictors. Predictors should return (predicted, confidence, uncertainty) and the top-level model should pass these through without ad-hoc multipliers.
- Add unit tests for sign conventions: spreads (home - away) and totals edge direction. Add a small test harness that runs predictor outputs against mocked bookmaker lines to verify edge sign and confidence ranges.
- Treat missing pace/poss values as missing (None) and count them in uncertainty. Prefer explicit detection (is None) rather than equality to default value.
- Replace silent except: blocks with logging.exception(...) and fail open/closed explicitly depending on severity.
- Move API keys out of source and into environment variables.
- Add sampling minimums and deterministic tie-breakers when selecting top picks to avoid flaky top-10 selection.

---

What I accomplished: read predictors (ncaa_total_predictor.py, ncaa_spread_predictor.py), main model (real_betting_model.py), and both caches (team_stats_cache.json, nba_team_stats_cache.json). I identified critical logic bugs (confidence fallback, spread sign/normalization) and several high/medium issues that affect predictions and data handling. I wrote actionable fixes with file pointers and code examples.

Notes for main agent: I did not audit the DB migration, learning_engine, update_adaptive_weights, bet_ranker, initialize_daily_bets, daily_recommendations, or ncaa_hybrid_score_fetcher files in depth due to time — they should be reviewed next (priority: ensure adaptive weight update uses correct Beta(2,2) prior and minimum sample size enforcement). If you want, I can run a focused pass on those files now.
