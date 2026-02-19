Audit Report: LarlBot NCAA Betting System
Date: 2026-02-18

Summary
-------
I audited the ranking, generation, learning, and weight-update code and the recent completed bets/weights data. I found multiple issues across formula correctness, data handling, learning assumptions, hardcoded values, and potential overfitting. Below is a prioritized, actionable list with root causes and concrete fixes (including code snippets where helpful).

Findings (prioritized)
----------------------
1) CRITICAL — Inconsistent/incorrect formula documentation vs implementation
   - Symptom: bet_ranker.py header and some prints show multiple formula variants; comments show (confidence * win_rate * edge) + historical_boost, prints show (confidence/100) × edge × (historical_win_rate / 0.5) and code uses confidence already divided by 100 in some places and not in others. initialize_daily_bets.py calls score_bet which divides confidence by 100; save_ranked_bets claims formula uses (confidence/100) × edge × (historical_win_rate / 0.5) but print_rankings shows (confidence/100) × edge × (historical_win_rate / 0.5) but earlier comments mismatch. Inconsistent units increase risk of scaling bugs and incorrect ranking.
   - Root cause: Multiple iterative edits left stale comments and inconsistent application of confidence scaling (some docs treat confidence as 0-100, code sometimes uses 0-1). Risk: score scaling errors and wrong top-10 selection.
   - Fix:
     - Standardize on explicit units: confidence stored as integer percent (0-100) throughout; score_bet should explicitly convert and document. Replace ambiguous comments.
     - Update score_bet to defensively coerce and validate input ranges.
   - Suggested code change (replace score_bet body with):
     ```python
     def score_bet(bet, win_rates):
         bet_type = bet.get('bet_type', 'SPREAD').upper()
         # Ensure numeric confidence in 0-100
         raw_conf = bet.get('confidence', 70)
         try:
             conf_pct = float(raw_conf)
         except Exception:
             conf_pct = 70.0
         conf_pct = max(0.0, min(100.0, conf_pct))
         confidence = conf_pct / 100.0

         # Edge must be numeric and non-negative
         try:
             edge = float(bet.get('edge', 0.0))
         except Exception:
             edge = 0.0

         win_rate = win_rates.get(bet_type, 0.5)
         adaptive_weights = load_adaptive_weights()
         adaptive_weight = adaptive_weights.get(bet_type, {}).get('weight', 1.0)

         larlescore = confidence * edge * (win_rate / 0.5) * adaptive_weight
         return larlescore
     ```
   - Rationale: defensive parsing prevents inconsistent scales and NaNs.

2) HIGH — Adaptive weights file inconsistent with update logic and contains incorrect rationales
   - Symptom: adaptive_weights.json contains textual analysis and inconsistent numeric claims (e.g., sample_count=15 marked HIGH confidence despite update_adaptive_weights requiring >=20 samples to adjust). Also MONEYLINE marked weight 0.0 but explanation says "0% historical win rate for TOTAL - keep disabled" mixing bet types (typo). This can cause logical mismatches (TOTAL vs MONEYLINE muddled).
   - Root cause: Manual edits and corrections created mismatch between learning thresholds and produced weights; typos conflating TOTAL vs MONEYLINE.
   - Fix:
     - Remove narrative fields from the weights file used by code or ensure parser ignores them. Ensure update_adaptive_weights is the single source of truth; if manual overrides are needed, add explicit "override": true and validation.
     - Correct typos: ensure MONEYLINE weight rationale references MONEYLINE not TOTAL.
   - Quick fix snippet to make load_adaptive_weights resilient:
     ```python
     def load_adaptive_weights():
         try:
             with open(WORKSPACE / 'adaptive_weights.json') as f:
                 data = json.load(f)
                 raw = data.get('weights', {})
                 # Extract numeric weights only
                 return {k: {'weight': float(v.get('weight', 1.0))} for k, v in raw.items()}
         except Exception:
             return {'SPREAD':{'weight':1.0}, 'MONEYLINE':{'weight':1.0}, 'TOTAL':{'weight':1.0}}
     ```

3) HIGH — Learning engine uses different data sources and duplicate-detection keys that cause undercount/overcount
   - Symptom: learning_engine.load_completed_bets pulls from bet_tracker_input.json and completed_bets_*.json and dedupes on (game, bet_type, recommendation, result). That dedupe key includes result, meaning if a bet was updated from LOSS to WIN later, it may be treated as a distinct entry rather than deduplicated. Also some files use 'game_name' or 'game' fields inconsistently (completed_bets_2026-02-17 has "game_name" in places).
   - Root cause: inconsistent field naming and dedupe key includes mutable field 'result'. This corrupts sample counts and biases learning.
   - Fix:
     - Use stable unique identifiers for bets (if available) like prediction_timestamp or a generated bet_id. If none, dedupe on (game, bet_type, recommendation, prediction_timestamp) or prefer latest timestamp when multiple entries share keys.
     - Don't include 'result' in the dedupe key; instead, keep the latest entry for a bet and use its result.
   - Suggested change (in load_completed_bets):
     ```python
     key = (bet.get('game') or bet.get('game_name'), bet.get('bet_type'), bet.get('recommendation'))
     # If multiple entries for same key, keep the one with newest result_updated_at/prediction_timestamp
     ```

4) MEDIUM — Confidence buckets and calibration assume confidence distribution boundaries that don't match generated values
   - Symptom: learning_engine buckets only include 50-59 up to 90-100; but generate picks use confidences like 58, 61, 82, 92. Some code clamps calibration only for 90-100 and 80-89, skipping 60-79 ranges; update_adaptive_weights uses target_conf 95/85 only. This yields poor calibration coverage and odd adjustments.
   - Root cause: mismatched bucket definitions and selective calibration.
   - Fix:
     - Expand calibration to cover all buckets present in analyze_confidence_buckets. Use bucket midpoints as targets. Apply smoothing for buckets with small samples.
   - Snippet for calibration midpoint mapping:
     ```python
     bucket_mid = {
         '90-100%': 95,
         '80-89%': 84.5,
         '70-79%': 74.5,
         '60-69%': 64.5,
         '50-59%': 54.5
     }
     ```

5) MEDIUM — Edge field units inconsistent and inflated
   - Symptom: completed_bets show TOTAL edges around 20+ pts which is implausible for totals (suggests model predicting total off by 20 points vs market). SPREAD edges are single-digit. If edge equals (market_line - model_estimate) in absolute points, totals showing 20+ indicates model uses different units or miscomputes (e.g., percent vs points). Also generate_daily_picks rounds edge to 1 decimal but other places use integers.
   - Root cause: inconsistent edge calculation across SmartEdge, RealModel, and fallback; unclear whether edge is absolute points or expected value in points or implied probability.
   - Fix:
     - Standardize 'edge' semantics project-wide: document whether it's absolute points (pts), expected value in points, or implied EV. Treat totals and spreads comparably. Add unit field: edge_units: 'points' or 'expected_pts'. Clamp unrealistic edges and log anomalies for review.
   - Example: add validation when writing picks:
     ```python
     if abs(pick['edge']) > 12 and pick['bet_type']=='TOTAL':
         logger.warning(f"Large TOTAL edge: {pick['edge']} for {pick['game']}")
     ```

6) MEDIUM — Deduplication logic in bet_ranker deduplicate_conflicting_bets keeps first occurrence; ordering dependency can keep lower-quality side
   - Symptom: deduplicate_conflicting_bets simply keeps the first seen (highest scored due to prior sort), but after deduplication code re-sorts; also initialize_daily_bets deduplicates before saving top 10 but uses scored list with items {'score','bet'} only; dedup function expects item['bet'] key in bet_ranker. Potential mismatch works now but fragile.
   - Root cause: dedup relies on sort order and identical key composition; if two opposing bets have identical game+type but added with slightly different keys, duplicates can slip.
   - Fix:
     - Make dedup deterministic by grouping by key and selecting max score per (game, bet_type) explicitly.
   - Snippet:
     ```python
     def dedupe_keep_best(scored):
         best = {}
         for item in scored:
             bet = item['bet']
             key = (bet.get('game'), bet.get('bet_type'))
             if key not in best or item['score']>best[key]['score']:
                 best[key] = item
         return list(best.values())
     ```

7) LOW — Hardcoded thresholds and magic numbers (top-10 rule, edge >=2.0, confidence thresholds)
   - Symptom: generate_daily_picks filters edge>=2.0 and confidence>=45 and top-10 enforced in multiple places. These values are in code and printed text (e.g., always top 10 strategy), making tuning slower.
   - Root cause: experimentation left constants in code instead of config.
   - Fix: move thresholds and top-N to a single configuration (JSON/YAML) used by generate, initialize, and ranker. Example file: config/picking_rules.json with min_edge, min_confidence, top_n.

8) LOW — Incomplete error handling for file reads/writes and missing keys
   - Symptom: many try/except blocks swallow exceptions, making silent failures. For example load_adaptive_weights catches all exceptions and returns default weights but doesn't log the reason.
   - Root cause: overly broad excepts for robustness, but hide real errors.
   - Fix: Log exceptions and re-raise if appropriate, or at least include logging.debug of stack trace.
   - Example change:
     ```python
     except Exception as e:
         logger.exception('Failed to load adaptive weights')
         return defaults
     ```

9) LOW — Overfitting risk: learning engine applies aggressive thresholds with small samples
   - Symptom: adaptive_weights.json claims TOTAL sample_count=15 but labeled HIGH; update_adaptive_weights enforces minimum 20 samples. The system appears to manually override weights to favor TOTAL based on small-sample Feb 15 result. This risks overfitting to a lucky day.
   - Root cause: human/manual overrides in adaptive_weights.json bypass statistical safeguards.
   - Fix: Require explicit "manual_override": true flag to accept weights that violate thresholds, and surface a prominent warning during initialization. Prefer Bayesian shrinkage: combine prior (baseline 0.5) with observed wins using Beta posterior to compute weight adjustments rather than raw win rates.
   - Short snippet (Bayesian smoothing):
     ```python
     alpha, beta = 2, 2  # weak prior centered at 50%
     wins = stats['wins']; losses = stats['losses']
     posterior_mean = (alpha + wins) / (alpha + beta + wins + losses)
     win_rate = posterior_mean
     ```

Other observations & recommendations
-----------------------------------
- Completed bets JSON files contain emoji and inconsistent field names (game vs game_name). Normalize fields at ingestion and strip emoji for keys.
- Ensure all results use consistent casing 'WIN'/'LOSS' (code uses uppercase checks but some files might have 'Win'). Use .upper() when reading.
- Consider storing bets in a single canonical database/table (sqlite) with indexes to avoid inconsistent JSON merging.
- Add unit tests: for score_bet, deduplication, and load_adaptive_weights behaviour under malformed JSON.
- Add logging for top-10 composition changes between runs and reason (which weights or thresholds caused difference).

What I accomplished
-------------------
- Read and analyzed the requested code files and data artifacts.
- Identified 9 issues prioritized by severity with root causes and concrete fixes, including code snippets to apply.
- Wrote this audit to /Users/macmini/.openclaw/workspace/GPT5_AUDIT_REPORT.md

Relevant details for the main agent
----------------------------------
- Immediate critical actions: standardize score_bet's confidence scaling and harden load_adaptive_weights parsing.
- Medium-term: fix dedupe logic to always pick best-scored side, canonicalize bet identity keys, and adopt Bayesian smoothing for weight updates to reduce overfitting.
- Data/ops: Remove manual edits that bypass update_adaptive_weights or add explicit manual_override flags.

If you want, I can now:
- Apply the simple code fixes (score_bet standardization + load_adaptive_weights parsing + dedupe_keep_best) directly in-place and run unit checks.
- Implement a Bayesian smoothing example in update_adaptive_weights to replace raw win-rate adjustments.

End of report.
