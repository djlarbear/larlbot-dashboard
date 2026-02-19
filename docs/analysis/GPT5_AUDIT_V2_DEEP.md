# Deep Audit — Learning, Ranking & Pipeline — Feb 18, 2026

## CRITICAL (must fix before tomorrow's 5 AM run)
- [Missing score fetcher]: ncaa_hybrid_score_fetcher.py is absent from workspace; file: N/A (missing)
  - exact problematic code: N/A (file missing)
  - impact: Pipeline step that fetches final scores (NCAA/NBA) will fail; completed_bets won't be updated and learning/weight updates will have no new data. This will break the 5 AM cron flow which expects score-fetching to populate completed bets.
  - fix: Add or restore ncaa_hybrid_score_fetcher.py. If the file was intentionally removed, make daily_recommendations/daily cron skip score-fetching gracefully and alert ops. Include unit tests that simulate "no score fetcher" and report graceful failure.

- [Potential bad picks outrank good ones when edge/confidence zero or negative]: bet_ranker.score_bet, file: bet_ranker.py: function score_bet()
  - exact problematic code:
    confidence = bet.get('confidence', 70) / 100  # Convert to 0-1
    edge = bet.get('edge', 2.0)
    larlescore = confidence * edge * (win_rate / 0.5) * adaptive_weight
  - impact: If edge is 0 or negative (edge==0 yields score 0; negative edge yields negative LARLScore), but other bets may have small positive scores and be ranked below a bet with slightly higher negative adaptive_weight or win_rate manipulations. Negative scores are not normalized/handled. A bet with zero edge but very high adaptive_weight and win_rate could still be zero; a tiny positive edge on a low-confidence pick could outrank. More critically, negative edge can invert ordering and cause the system to prefer contrarian picks.
  - fix: Clamp edge to a sensible non-negative minimum (e.g., edge = max(0.0, float(bet.get('edge', 0.0))) ). Also decide whether negative edge should disqualify a pick. Explicitly handle edge==0 as low-quality and either filter or assign a floor score. Document behavior in code and add tests for negative/zero edge.

- [Adaptive weight 0 -> exclusion logic inconsistent between modules]: initialize_daily_bets.py and bet_ranker.py
  - exact problematic code (initialize_daily_bets.py):
    w = adaptive_weights.get(bt, {}).get('weight', 1.0)
    if w <= 0:
        continue  # Skip disabled bet types (MONEYLINE)
  - exact problematic code (bet_ranker.save_ranked_bets & score path): bet_ranker.score_bet applies weight directly (no explicit skip when weight==0)
  - impact: initialize_daily_bets explicitly removes bet types with weight <= 0 before scoring, but bet_ranker.score_bet does not. If someone runs bet_ranker.py standalone (or the scheduler runs it directly) it will include bet types with weight 0 and produce 0 scores (or 0*something) in ranked_bets.json — causing inconsistency between selection and ranking steps.
  - fix: Centralize the rules: either treat weight==0 as explicit disable everywhere or let bet_ranker skip weight<=0 bets during ranking. Add a unit test where MONEYLINE has weight 0 and verify both initialize_daily_bets and bet_ranker produce the same final active set.

## HIGH (fix soon)
- [Deduplication key in LearningEngine uses recommendation string (fragile)]: learning_engine.py: load_completed_bets() dedupe loop
  - exact problematic code:
    key = (bet.get('game') or bet.get('game_name'), bet.get('bet_type'), bet.get('recommendation'))
  - impact: Using recommendation text as part of the unique key is brittle: minor formatting differences ("UNDER 150" vs "UNDER 150 ") or source-specific phrasing will create duplicate logical bets. This can undercount duplicates or produce duplicates in learning. It also makes dedupe sensitive to casing/spaces.
  - fix: Use normalized fields for dedupe: (normalise(game), bet_type.upper(), normalized_recommendation) or prefer a canonical id (bet_id) when present. Trim/upper recommendation and game strings before using them in keys.

- [Dedupe should not include "result" — verified but worth confirmation]: learning_engine.py
  - note: The previous bug included result in the dedupe key; current code does NOT include result. This is correct and prevents splitting identical bets into separate groups simply because their result differs. Confirmed OK.

- [LearningEngine only accepts exact 'WIN'/'LOSS' uppercase strings]: learning_engine.py: load_completed_bets() and multiple analyses
  - exact problematic code:
    bets = [b for b in tracker.get('bets', []) if b.get('result') in ['WIN', 'LOSS']]
  - impact: If any results are lowercase or have whitespace ("win", "Win "), those entries will be ignored. That will bias sample counts and win rates.
  - fix: Normalize result values using .strip().upper() when filtering and when counting.

- [Adaptive weight smoothing & stability logic is conservative and may never move weights for sample_count < 20]: update_adaptive_weights.py
  - exact problematic code:
    if count < 20:
        stability_factor = 0.0
        confidence_level = 'LIMITED'
    elif count < 30:
        stability_factor = (count - 20) / 10.0
  - impact: counts between min_sample_size (10) and 19 will get skipped at earlier check and return neutral weight already; counts 20-29 are slowly ramped. This is intentionally conservative, but it means bet types with counts in [10,19] are never moved from 1.0 even if smoothed win rate is extreme. That's OK if conservative behavior desired, but it should be documented.
  - fix: If the intention is to allow updates starting at min_sample_size=10 with gentle ramp, change logic to use the min_sample_size variable to compute stability ramp. Otherwise document the conservative threshold.

- [update_adaptive_weights: when count < min_sample_size the smoothing.smoothed_win_rate is set to None]: update_adaptive_weights.py
  - exact code:
    'smoothing': {
      'raw_win_rate': round(raw_wr * 100, 2),
      'smoothed_win_rate': None,
      'alpha': self.alpha,
      'beta': self.beta
    }
  - impact: Downstream consumers may expect smoothed_win_rate to be numeric. Also validate_weights expects win_rate numeric; when migrated into DB migrate_adaptive_weights reads meta.get('weight') etc but not smoothed fields. Still, untyped None values in JSON may surprise other code.
  - fix: Set smoothed_win_rate to round(smoothed_wr*100,2) even when count < min_sample_size by applying prior-only smoothing (wins + alpha)/(count + alpha + beta) OR explicitly set smoothed_win_rate to raw_wr*100 and annotate as 'INSUFFICIENT_SAMPLE'. Document clearly.

## MEDIUM (improve when possible)
- [initialize_daily_bets: scoring order looks correct but scoring excludes disabled types before deduplication]: initialize_daily_bets.py
  - exact code snippet:
    for pick in picks:
        bt = pick.get('bet_type', 'SPREAD')
        w = adaptive_weights.get(bt, {}).get('weight', 1.0)
        if w <= 0:
            continue  # Skip disabled bet types (MONEYLINE)
        s = score_bet(pick, win_rates)
  - impact: This achieves the intended behavior (score all available picks except disabled types) — good. But the comment says "Score ALL picks with LARLScore formula, THEN take top 10"; technically it scores all non-disabled picks, which is correct. Document that disabled types are omitted prior to scoring.
  - fix: None urgent — consider centralizing the "disabled" logic in bet_ranker.score_bet or add a flag to score_bet to skip if adaptive_weight<=0.

- [Deduplication relies on bet['game'] exact match]: bet_ranker.deduplicate_conflicting_bets
  - exact code:
    game = bet.get('game', '')
    key = (game, bet_type)
  - impact: If two sources format game names differently ("Team A @ Team B" vs "Team A @ Team B ") mismatches will allow duplicates. Also some modules use game_name. This will allow accidental conflicting bets to survive deduplication.
  - fix: Normalize 'game' before forming key (strip(), lower() or canonicalize teams order). Also accept game_name fallback: game = bet.get('game') or bet.get('game_name').

- [daily_recommendations: CacheManager.get_cache('daily_picks') may return stale picks for >24h if cache expiry not enforced here]: daily_recommendations.py
  - impact: If CacheManager implements TTL correctly this is fine; otherwise a broken cache can cause stale picks to persist. The code prints "Using cached daily picks (24h cache)" but does not validate generated_at timestamp.
  - fix: Ensure CacheManager.get_cache returns timestamp and that get_todays_value_bets validates age of cache (e.g., check generated_at within 24h). Add a failsafe to ignore cached picks older than 24h.

## LOW (nice to have)
- [bet_ranker: inconsistent docstring/formula text shows (confidence/100) but code uses confidence already divided]: bet_ranker.py print_rankings() vs score_bet()
  - exact code mismatch: docstrings and 'larlescore_formula' string include (confidence/100) but score_bet already divides confidence by 100 at top. This is fine functionally but can confuse future maintainers.
  - fix: Make wording consistent (store whether confidence is 0-1 or 0-100 and name variable accordingly). Update human-facing string to show the normalized formula explicitly.

- [betting_database.migrate_completed_bets: generated id may contain characters causing duplicates]: betting_database.py
  - exact code:
    'id': bet.get('id') or bet.get('bet_id') or None,
    'id' for save_bet uses f"{bet.get('date')}_{bet.get('game')}_{bet.get('bet_type')}"
  - impact: This composite id may contain slashes, commas, or non-ASCII chars and may not be unique if date or formatting differs. Collisions could cause unexpected upserts.
  - fix: Normalize id (slugify game name) or use a hash of the composite string.

## GOOD (things working correctly)
- [LearningEngine: dedupe no longer includes `result`] learning_engine.py: load_completed_bets()
  - code: key = (bet.get('game') or bet.get('game_name'), bet.get('bet_type'), bet.get('recommendation'))
  - reason: This avoids the previous bug that split identical bets into separate records based solely on result. Good.

- [Adaptive weight Bayesian smoothing implemented correctly] update_adaptive_weights.py: calculate_weights()
  - code: smoothed_wr = (wins + self.alpha) / (count + self.alpha + self.beta)
  - reason: Beta(2,2) smoothing implemented per spec. Clamping to [0.3, 2.0] performed in validate_weights/save path. Logging and rounding present.

- [betting_database: uses parameterized queries everywhere] betting_database.py
  - reason: Prevents SQL injection risks in typical usage because queries consistently use ? or named parameters.

- [initialize_daily_bets: explicitly scores then deduplicates then saves TOP 10] initialize_daily_bets.py
  - reason: This corrects past bug where filtering happened before scoring. Code calls score_bet on picks, sorts, dedups, and then saves first 10.

- [adaptive_weights.json structure matches updater expectations] adaptive_weights.json
  - reason: file contains 'weights' mapping and meta fields 'generated_at' and 'source'. update_adaptive_weights.py expects these fields when saving/reading.

## CROSS-FILE ISSUES
- [Field name variations] Several files use either 'game' or 'game_name'. Files affected: learning_engine.py (uses both), bet_ranker.deduplicate_conflicting_bets (uses 'game' only), betting_database.migrate_completed_bets (normalizes using 'game'). Impact: games may not be deduplicated/matched across modules when field name differs.
  - fix: Standardize canonical field names (game, bet_type, recommendation, bet_id) across project. Adopt a small normalization helper used everywhere.

- [Adaptive weight zero-handling inconsistent] initialize_daily_bets filters weight<=0 before scoring whereas bet_ranker does not. See HIGH section. Centralize policy.

- [Result string normalization not enforced] learning_engine expects uppercase 'WIN'/'LOSS', other modules may write lowercase or padded strings. This can cause mismatches. Normalize result strings at ingestion (all readers and writers).

## PIPELINE VERIFICATION
Trace (intended) 5 AM cron flow and failure points:
1) daily_recommendations.get_todays_value_bets()
   - Reads cache via CacheManager.get_cache('daily_picks') (may return cached picks)
   - If cache miss, uses RealBettingModel -> generates picks -> optionally ML & adaptive filter -> writes active_bets.json
   - Failure points: Missing RealBettingModel or network errors; code falls back to get_fallback_bets() and still writes active_bets.json. OK.
2) initialize_daily_bets.initialize_active_bets()
   - Calls daily_recommendations.get_todays_value_bets() (pulls picks)
   - Loads completed_bets via bet_ranker.load_completed_bets() and calculates win_rates
   - Loads adaptive_weights.json and filters out weight<=0 bet types before scoring
   - Scores remaining picks with bet_ranker.score_bet(), sorts, dedups, saves top 10 to active_bets.json
   - Then runs bet_ranker.py (subprocess) to generate ranked_bets.json
   - Failure points: If adaptive_weights.json missing default used; subprocess.run can fail silently — script captures output but doesn't handle returncode beyond printing. If bet_ranker fails, initialize still continues printing success. Suggest checking subprocess.returncode and failing loudly.
3) bet_ranker.main() (standalone or called from daily_recommendations)
   - Loads completed bets from completed_bets_*.json -> calculates win_rates
   - Loads active_bets.json -> ranks all bets using LARLScore -> dedups -> saves ranked_bets.json
   - Failure points: If adaptive_weights differ or weight==0 logic inconsistent, top_10 vs active_bets.json may disagree. Also score_bet allows negative/zero edge.
4) update_adaptive_weights.py (should be run after learning updates)
   - Reads learning_insights.json (produced by learning_engine), applies Beta(2,2) smoothing, writes adaptive_weights.json
   - Failure points: learning_insights.json missing -> script exits early and returns None (handled). If learning_insights exists but includes unexpected types, validate_weights will clamp but log warnings.
5) learning_engine.run_analysis()
   - Loads completed bets (from bet_tracker_input.json and completed_bets_*.json) and de-duplicates
   - Produces learning_insights.json and writes it
   - Failure points: load_completed_bets uses exact 'WIN'/'LOSS' filters — mixed-case results will be ignored; dedupe uses recommendation text (fragile). If completed bets not written by score_fetcher (missing file), no new data triggers early exit if <5 bets.
6) Score fetching (ncaa_hybrid_score_fetcher.py) — MISSING
   - Intended to fetch live game statuses for NCAA and NBA and write completed_bets_*.json or update active/completed bet files
   - Because file is missing, this step will not run. That is the major blocker.

Recommendations to make cron robust:
- Add a top-level orchestration script that runs steps in order and fails fast if critical steps (score fetch) are missing. The script should check return codes and presence of required output files (completed_bets_*.json, learning_insights.json, adaptive_weights.json, ranked_bets.json) and alert on problems.
- Normalize data at ingestion entry points: results, game names, bet_type (uppercased), recommendation trimmed. Provide a small util module (normalize.py) imported by each file.
- Make weight==0 policy explicit and applied consistently in score_bet() as early exit.
- Add tests for zero/negative edges, missing fields, and variant game name formatting.

---

What I accomplished / found (summary):
- Read and audited bet_ranker.py, learning_engine.py, update_adaptive_weights.py, initialize_daily_bets.py, daily_recommendations.py, betting_database.py, adaptive_weights.json. ncaa_hybrid_score_fetcher.py is missing from workspace — critical.
- Verified Beta(2,2) smoothing is implemented correctly and weights clamped in validation.
- Confirmed dedupe in learning_engine no longer includes `result` (good), but dedupe key uses recommendation text which is brittle.
- Identified inconsistent handling of adaptive_weight==0 between initialize_daily_bets (skips before scoring) and bet_ranker (does not skip). This can produce inconsistent ranked outputs.
- Found edge cases where zero/negative edge and non-normalized result strings can silently produce wrong counts or inverted rankings.
- Wrote concrete fixes and prioritized them by severity.

If you want, I can:
- Create small patch edits for the most critical fixes (e.g., normalize result strings in learning_engine, clamp edge in bet_ranker.score_bet, add game normalization in dedup functions, and make bet_ranker skip weight<=0 consistently). Reply with which fixes to apply and I'll modify files and run quick lint checks.

