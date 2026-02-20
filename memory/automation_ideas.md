# Automation Ideas & Improvements

Captured from Feb 18 session work. Prioritized by impact.

---

## High Priority (Quick Win + High Impact)

### 1. **Team Name Canonicalization**
**Problem:** ESPN uses "North Carolina" | OddsAPI uses "UNC" → mismatches, duplicate teams, stale caches
**Solution:** Build name-mapping service + update ncaa_total_predictor.py and ncaa_spread_predictor.py
**Effort:** 1-2 hours
**Impact:** Eliminates false misses, more reliable bets
**Files:** New `team_name_mapper.py`

### 2. **API Key Management**
**Problem:** OddsAPI key hardcoded in `ncaa_hybrid_score_fetcher.py`
**Solution:** Move to `~/.openclaw/openclaw.json` env vars (already support)
**Effort:** 30 mins
**Impact:** Better security, easy rotation
**Files:** `ncaa_hybrid_score_fetcher.py`, `ncaa_team_stats_fetcher.py`

### 3. **Configuration File**
**Problem:** Thresholds scattered (min edge 1.0, top-N 10, confidence floors) — hard to tune
**Solution:** Create `config/picking_rules.json` with all tunable parameters
**Effort:** 45 mins
**Impact:** Faster iteration, no code changes needed for tuning
**Structure:**
```json
{
  "top_n_picks": 10,
  "min_edge_pts": 1.0,
  "confidence_floor": 52,
  "moneyline_weight": 0.0,
  "nba_hca": 2.5,
  "ncaa_hca": 3.5
}
```

---

## Medium Priority (Worth Doing, Moderate Effort)

### 4. **Unit Tests**
**Problem:** Core functions (score_bet, dedupe, learningEngine) lack coverage → risky refactors
**Solution:** pytest suite for edge cases
**Effort:** 3-4 hours
**Impact:** Confidence in changes, catch regressions early
**Tests needed:**
- score_bet() with all confidence levels (50–100)
- deduplicate_conflicting_bets() edge cases (same game, overlapping picks)
- Learning engine normalization (various result strings, non-English chars)
- Bayesian weight update stability (division by zero, zero samples)

### 5. **Git Auto-Cleanup**
**Problem:** Outstanding files (active_bets.json in root) clutter status
**Solution:** Cron job to commit any outstanding changes nightly
**Effort:** 30 mins
**Impact:** Cleaner workflow, easier audits
**Implementation:** Add 11:55 PM cron job: `git add -A && git commit -m "Auto-cleanup [$(date +%Y-%m-%d)]"`

### 6. **GitHub Issue Auto-Reporter**
**Problem:** Known bugs (Mission Control UI bug #1, known edge cases #2–3) should be tracked
**Solution:** Create Issues on robsannaa/openclaw-mission-control repo with reproducers
**Effort:** 1 hour (first time setup)
**Impact:** Visibility, easier collaboration with maintainers
**Bugs to report:**
- Mission Control: Runtime TypeError when reading `job.delivery.mode` (Job #2)
- Consider: Any OddsAPI/ESPN API reliability patterns

---

## Low Priority (Nice-to-Have, Can Defer)

### 7. **Logging Improvements**
**Problem:** Silent except blocks hide errors; hard to diagnose API timeouts
**Solution:** Replace `except: pass` with structured logging (JSON to `betting/logs/errors.jsonl`)
**Effort:** 2-3 hours
**Impact:** Better post-mortem diagnostics, easier debugging

### 8. **Pandas/NumPy Analysis Dashboards**
**Problem:** Win rate trends and edge calibration only visible in raw JSON
**Solution:** Weekly analysis notebooks (Jupyter or Observable) plotting:
- Win rate by confidence bucket
- Edge vs actual margin distributions
- Adaptive weight convergence
**Effort:** 4-5 hours
**Impact:** Deeper insights, visualization of what's working/not working

### 9. **Pace & Possessions Data**
**Problem:** ESPN doesn't expose easily; correlates with scoring variance
**Solution:** Scrape from team pages or use proxy (Kenpom for NCAA, Cleaning the Glass for NBA)
**Effort:** 3-4 hours (with new data source)
**Impact:** Tighter TOTAL predictions (+2–3% accuracy potentially)

---

## Completed (Feb 18)
✅ Real prediction models (ncaa_total_predictor, ncaa_spread_predictor)
✅ Bayesian smoothing
✅ SQLite persistence
✅ NBA support
✅ Recent form data (all 392 teams)
✅ 9 bug fixes
✅ Workspace reorganization
✅ Telegram notifications
✅ Comprehensive documentation

## Completed (Feb 19)
✅ Full system restore to working state
✅ Railway deployment finalized (Dockerfile, railway.toml, .dockerignore)
✅ Streamlit detection bug permanently fixed
✅ Pick change guard system built
✅ Cron automation confirmed working

---

## NEW: Deployment & Config Learnings (Feb 19, 4:59 PM)

### 10. **Pre-Commit Config Checklist** (High Priority)
**Lesson from Feb 19:** Config files are critical for deployment, but easy to forget
**Solution:** Add pre-commit hook or checklist
- Dockerfile: Always verify paths, ENTRYPOINT
- railway.toml: Must have `builder = "dockerfile"`
- .dockerignore: Must exclude local venvs
- entrypoint.sh: Must verify Flask, reject Streamlit
- Procfile: Remove if using Docker (creates ambiguity)

**Impact:** Prevents recurring deployment failures
**Effort:** 15 mins (add to docs/DEPLOYMENT_CHECKLIST.md)

### 11. **Monitoring Dashboard for Railway Health** (Medium Priority)
**Lesson from Feb 19:** Railway works, but we should track uptime/errors
**Solution:** Weekly cron job polling Railway deployment status → log results
- Check: Is app running? Response time? Error rate?
- Store in `betting/logs/railway_health.jsonl`
- Alert via Telegram if down or slow

**Impact:** Early warning of deployment issues
**Effort:** 2-3 hours (Railway API integration)

---

## Suggested Next Session Focus
1. **Team name canonicalization** (highest ROI: fixes false misses)
2. **Configuration file** (enables easy tuning, unblocks weight experiments)
3. **Unit tests** (foundation for confident refactoring)

**After system stability (1-2 weeks):**
- Pre-commit config checklist
- Railway monitoring dashboard
- Then: UI improvements (only after model hits 55%+ win rate)

**Rest can wait until win rate stabilizes above 55%.**

---

**Last updated:** 2:00 AM EST, Feb 20, 2026
