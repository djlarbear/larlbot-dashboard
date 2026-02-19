# MEMORY.md - Betting System (Current State)

## 🎯 SYSTEM STATUS - Feb 19 (Updated 9:54 AM)

**✅ VALIDATED & APPROVED FOR BETTING**

**CRITICAL BUG FIXED (Feb 19, 9:53 AM):** NBA cache paths were broken
- `ncaa_spread_predictor.py` and `ncaa_total_predictor.py` had hardcoded cache paths
- Paths were `'team_stats_cache.json'` instead of `'../data/team_stats_cache.json'`
- Result: ALL NBA picks had 49% confidence (using default fallback data)
- **FIX:** Changed to `'../data/team_stats_cache.json'` and `'../data/nba_team_stats_cache.json'`
- NBA confidence now 60-71% (realistic, data-driven)

**VALIDATION (9:54 AM):**
- ✅ Predictors tested: NCAA & NBA working correctly
- ✅ Confidence distribution: 60-77% (avg 69.7%)
- ✅ Code audit: 106 files scanned, 0 critical issues
- ✅ Data quality: 392 teams with full stats + recent form
- ✅ Dashboard updated with validated picks

**Today's Picks (Feb 19):**
- 10 total: 2 NBA + 8 NCAA (8 SPREAD + 2 TOTAL)
- Top: High Point Panthers -14.5 (NCAA, LARLScore 25.4)
- #2: Cleveland Cavaliers -16.0 (NBA, LARLScore 21.4)
- Confidence range: 60-77%
- Old 5 AM picks had 0 NBA (bug caused exclusion)

**Dashboard:** Live on localhost:5001 + Railway
**Data Pipeline:** NCAA API (D1/D2/D3) + OddsAPI (FanDuel) + NBA ✅

---

## ⚙️ CONFIG

**Models:** Opus (primary) → Haiku → GPT-5-mini (fallback)
**OpenAI:** Connected and tested ✅
**Cron:** 5 AM daily batch (score fetch → learning → weights → picks)

---

## 🔧 BUGS — ALL FIXED ✅ (Feb 18)

1. ~~Learning engine dedupe~~ — fixed, key no longer includes `result`
2. ~~Confidence calibration~~ — fixed, covers all buckets
3. ~~Typo~~ — fixed in adaptive_weights.json
4. ~~Field name inconsistency~~ — normalized all files to `game`, added fallbacks
5. ~~Fallback confidence bug~~ — fixed uninitialized variable in real_betting_model.py
6. ~~TOTAL confidence double-scaling~~ — changed from multiplicative to subtractive penalty
7. ~~Negative edge ranking~~ — clamped to non-negative in bet_ranker
8. ~~Result string normalization~~ — strip().upper() in learning_engine
9. ~~Weight=0 inconsistency~~ — bet_ranker now skips disabled types like initialize_daily_bets

## 🏗️ BUILD — ALL DONE ✅ (Feb 18)

1. ~~Real TOTAL prediction model~~ → `ncaa_total_predictor.py`
2. ~~Real SPREAD prediction model~~ → `ncaa_spread_predictor.py`
3. ~~Replace fake edges~~ → real predictors called from real_betting_model.py
4. ~~Replace hardcoded confidence~~ → model-derived values
5. ~~Bayesian smoothing~~ → Beta(2,2) prior, min_sample_size=10
6. ~~SQLite~~ → `betting_database.py` + `betting.db` (68 bets, 362 teams, 3 weights)
7. ~~NBA support~~ → 30 teams, league param, HCA 2.5
8. ~~Recent form data~~ → last 5 games for all 392 teams

---

## 📁 KEY FILES

| File | Purpose | Status |
|------|---------|--------|
| `real_betting_model.py` | Pick generation via real predictors | ✅ |
| `ncaa_total_predictor.py` | TOTAL prediction (PPG, pace, splits, form) | ✅ NEW |
| `ncaa_spread_predictor.py` | SPREAD prediction (strength, HCA, form) | ✅ NEW |
| `bet_ranker.py` | LARLScore formula + dedup | ✅ FIXED |
| `initialize_daily_bets.py` | Top 10 selection (scores all first) | ✅ FIXED |
| `learning_engine.py` | Win/loss analysis (normalized) | ✅ FIXED |
| `update_adaptive_weights.py` | Bayesian weight updates | ✅ FIXED |
| `betting_database.py` | SQLite wrapper + migration | ✅ NEW |
| `team_stats_cache.json` | 362 NCAA teams (full stats + recent 5) | ✅ |
| `nba_team_stats_cache.json` | 30 NBA teams (full stats + recent 5) | ✅ NEW |
| `adaptive_weights.json` | Current weights (TOTAL 1.3, SPREAD 0.8) | ✅ |
| `ncaa_hybrid_score_fetcher.py` | Score fetching (symlinked from agents/) | ✅ |
| `auto_result_tracker.py` | OddsAPI result tracking | ✅ |
| `GPT5_AUDIT_V2.md` | Audit: predictors + main model | ✅ |
| `GPT5_AUDIT_V2_DEEP.md` | Audit: learning + ranking + pipeline | ✅ |

---

## 💰 TOKEN OPTIMIZATION & EFFICIENCY RULES

**Model Selection:**
- Haiku: status checks, file listings, summaries, routine tasks
- Sonnet: complex reasoning, coding, important decisions
- GPT-5-mini: fallback/audit tool

**Response Style:**
- Concise by default — get to the point
- Detail only when asked
- Batch similar tasks together
- Ask clarifying questions upfront, not back-and-forth
- Use memory to avoid repetition
- Proactive suggestions when patterns emerge

**Operations:**
- Read files surgically, batch operations
- Compaction at 40k soft threshold

---

## 📝 DECISION LOG

**Feb 18 Evening:**
- Fixed `initialize_daily_bets.py` — was taking picks[:10] raw instead of scoring first
- Corrected adaptive weights (TOTAL→1.3 HIGH, SPREAD→0.8 LOW)
- Added OpenAI/GPT-5-mini to config
- Discovered prediction model is fake (manufactured edges/confidence)
- GPT-5-mini audit: good on code quality, missed fundamental model problem
- **Next priority: Build real predictive models before further tuning**

## 🚀 MILESTONE: Real Prediction Model Live (Feb 18, 10:20 PM)

**Fake model replaced with real data-driven predictions.**
- `ncaa_total_predictor.py` — team PPG, opp PPG, pace, home/away splits
- `ncaa_spread_predictor.py` — team strength differentials, HCA (3.5 pts), recent form
- `team_stats_cache.json` — 362 D1 teams with real ESPN data
- `real_betting_model.py` — updated to call real predictors (graceful fallback)
- New picks: 7 TOTAL + 3 SPREAD mix, OVER and UNDER based on data
- Edges now realistic (0.9-24 pts vs fake 23+ pts)

## 🚀 MILESTONE: Full System Overhaul Complete (Feb 18, 10:40 PM)

**All remaining work done in one session:**
- `nba_team_stats_cache.json` — 30 NBA teams with full stats (PPG, opp_ppg, MOV, splits, recent form)
- Recent form (last 5 games) populated for ALL 362 NCAA + 30 NBA teams
- `ncaa_total_predictor.py` + `ncaa_spread_predictor.py` — now support `league='nba'` param
- `real_betting_model.py` — passes league='nba' for NBA games automatically
- NBA HCA = 2.5 pts (vs NCAA 3.5)
- `update_adaptive_weights.py` — Bayesian smoothing (Beta(2,2) prior, min_sample_size=10)
- `betting_database.py` + `betting.db` — SQLite with 68 bets, 362 teams, 3 weights migrated
- Fixed all 4 bugs: dedupe, calibration, typo, field name inconsistency
- New picks: 5 TOTAL + 5 SPREAD balanced mix, real data-driven edges

**All items from BUILD NEEDED list: DONE**
**All items from BUGS TO FIX list: DONE**
**System ready for tomorrow's 5 AM cron run including NBA**

## 📋 REMAINING (Nice-to-have, not blocking)
- Team name canonicalization (OddsAPI vs ESPN naming variants)
- Move API key from source to env var
- Pace/possessions data (ESPN doesn't expose easily)
- Config file for thresholds (top-N, min edge, min confidence)
- Unit tests for edge cases

## 🔍 GPT-5-MINI AS AUDITOR
- Two audit passes on Feb 18: V1 (predictors+model) and V2 (learning+ranking+pipeline)
- Caught real bugs: fallback confidence, double-scaling, negative edge, result normalization
- Also flagged false positives: "missing score fetcher" was just wrong path
- **Lesson: always verify GPT-5-mini findings against actual code before acting**

## 🗂️ WORKSPACE REORGANIZATION (Feb 18, 11:43-11:52 PM)

**Complete:** 320 files organized, 15KB docs created, git initialized ✅

**Structure:**
- `betting/{scripts,data,models,logs}` - All betting code + data separated
- `docs/{architecture,sessions,analysis}` - Comprehensive documentation
- `templates/` - Reusable daily_summary + audit_checklist
- `scripts/quick_status.sh` - One-command health check

**Key Fixes:**
- Dashboard paths → `betting/data/`
- Logs → `betting/logs/`
- Database table: `teams` → `team_stats`
- Git: 3 commits, all changes tracked

**New Guidelines (Stored):**
- Efficiency: Haiku for routine, Sonnet for complex, concise by default
- Self-improvement: Learn from every interaction, store in memory, adjust
- Daily memory review: 2 AM cron (Haiku subagent)

## 📱 TELEGRAM NOTIFICATIONS (Feb 19, 12:00 AM)

**Status:** Active ✅ (ID: `telegram:2134752560`)

**Automated Notifications:**
- **2:00 AM** - Daily memory review summary
- **5:15 AM** - Morning betting report (picks, status, errors)
- **Every 6h** - Error monitor (only if issues detected)

**Silent unless issues:** Error monitor uses HEARTBEAT_OK when all clear.

*Last Updated: Feb 19, 12:00 AM EST*
