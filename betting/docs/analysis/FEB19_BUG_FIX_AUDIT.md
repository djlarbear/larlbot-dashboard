# Feb 19 Bug Fix Audit - NBA Cache Path Issue

## Problem Discovered
- **Time:** 9:50 AM EST, Feb 19, 2026
- **Reporter:** Larry (user)
- **Issue:** Dashboard showed 0 NBA picks at 5:00 AM, despite NBA games being available

## Root Cause Analysis

### Investigation Steps
1. Checked `active_bets.json` - contained 10 NCAA picks, 0 NBA
2. Generated fresh picks - found 30 NBA + 96 NCAA available
3. Noticed all NBA spreads had exactly 49% confidence (suspicious)
4. Tested NBA prediction model directly
5. Found predictor was using default fallback values instead of cached team stats

### Root Cause
**File:** `betting/scripts/ncaa_spread_predictor.py` and `ncaa_total_predictor.py`
**Lines:** 10-11

```python
# BROKEN CODE:
CACHE_PATH = 'team_stats_cache.json'
NBA_CACHE_PATH = 'nba_team_stats_cache.json'
```

**Problem:** Relative paths assumed files were in `/betting/scripts/` but they're actually in `/betting/data/`

**Impact:**
- `load_cache()` couldn't find NBA team stats
- Predictor fell back to defaults: `ppg=110, opp_ppg=110, mov=0.0`
- Confidence calculation: `base_conf = 45 + min(30, int(abs(predicted_margin)*3))`
- With predicted_margin ≈ 2.5 (just HCA), confidence = 49%
- All NBA picks appeared weak/unreliable

## Fix Applied

### Code Changes
**File:** `betting/scripts/ncaa_spread_predictor.py` (Line 10-11)
```python
# FIXED CODE:
CACHE_PATH = '../data/team_stats_cache.json'
NBA_CACHE_PATH = '../data/nba_team_stats_cache.json'
```

**File:** `betting/scripts/ncaa_total_predictor.py` (Line 15-16)
```python
# FIXED CODE:
CACHE_PATH = '../data/team_stats_cache.json'
NBA_CACHE_PATH = '../data/nba_team_stats_cache.json'
```

### Validation
Tested Cleveland Cavaliers vs Brooklyn Nets:
- **Before Fix:** predicted_margin=2.5, confidence=49%
- **After Fix:** predicted_margin=14.2, confidence=71%
- **Market:** Cleveland -16.0
- **Edge:** 30.2 points (model predicts Cleveland wins by 14, market has 16)

## Results

### New Top 10 Picks (Post-Fix)
1. High Point -14.5 (NCAA) - LARLScore: 25.4
2. **Cleveland Cavaliers -16.0 (NBA)** - LARLScore: 21.4
3. Winthrop -13.5 (NCAA) - LARLScore: 20.1
4. Hofstra -11.5 (NCAA) - LARLScore: 17.5
5. Radford -19.5 (NCAA) - LARLScore: 17.0
6. South Alabama OVER 137.5 (NCAA) - LARLScore: 17.0
7. South Florida -8.5 (NCAA) - LARLScore: 15.8
8. Mercer -10.5 (NCAA) - LARLScore: 15.5
9. Liberty -11.5 (NCAA) - LARLScore: 14.6
10. **San Antonio Spurs -7.5 (NBA)** - LARLScore: 13.8

### Mix Change
- **Before:** 0 NBA + 10 NCAA (5 SPREAD + 5 TOTAL)
- **After:** 2 NBA + 8 NCAA (8 SPREAD + 2 TOTAL)

## Files Updated
1. `/betting/scripts/ncaa_spread_predictor.py` - cache path fix
2. `/betting/scripts/ncaa_total_predictor.py` - cache path fix
3. `/betting/data/active_bets.json` - updated with fixed picks
4. `/betting/data/active_bets_OLD_5AM.json` - backup of old picks
5. `/MEMORY.md` - documented bug and fix

## Lessons Learned
1. **Relative paths are fragile** - consider using `__file__` based paths or absolute paths
2. **Silent fallbacks hide bugs** - predictors used defaults without warning
3. **Confidence patterns are diagnostic** - all picks at 49% was a clear signal
4. **Testing with real data catches issues** - manual prediction test revealed the problem
5. **Time-of-day matters** - 5 AM run missed NBA because games hadn't posted yet

## Recommended Improvements
1. Add logging when cache files aren't found (don't fail silently)
2. Use `os.path.join(os.path.dirname(__file__), '../data/cache.json')` for robust paths
3. Add validation that checks if predictions are using real vs default data
4. Consider warning if confidence is suspiciously uniform across many picks
5. Update cron schedule to run NBA-inclusive picks after 9 AM when lines are posted

## Audit Questions for GPT-5-mini
1. Are there any other files with similar relative path issues?
2. Does the confidence formula make sense? (45 + min(30, predicted_margin*3))
3. Are there edge cases where this fix could still fail?
4. Should we add unit tests for the predictor cache loading?
5. Any other potential bugs lurking in the prediction pipeline?
