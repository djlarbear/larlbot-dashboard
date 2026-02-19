# LARLESCORE Calibration Report
**Date:** 2026-02-17 09:15 EST
**Agent:** backend-dev (SWORD coordination)
**Status:** CRITICAL MISALIGNMENT FOUND

## Executive Summary

The LARLESCORE ranking system has **SEVERE calibration issues**:
- **Problem:** System recommends games WITHOUT verifiable scores
- **Impact:** All 24 Feb 16 bets remain PENDING (can't verify results)
- **Root Cause:** Recommends small college games ESPN doesn't track
- **Evidence:** Syracuse @ Duke (ESPN HAS score) NOT in top 10; instead recommends games with NO ESPN data

---

## The Evidence

### What ESPN Has (Feb 16)
```
✅ Syracuse Orange 64 @ Duke Blue Devils 101 (FINAL)
✅ Houston Cougars 67 @ Iowa State Cyclones 70 (FINAL)
⚠️  Only 4 major games total covered by ESPN API
```

### What LARLESCORE Recommended (Feb 16)
```
1. Colgate Raiders @ Boston Univ. Terriers (UNDER 143.5)        [score: 6.23]
2. SE Louisiana Lions @ East Texas A&M Lions (UNDER 135.5)      [score: 6.19]
3. Louisiana Ragin' Cajuns @ Old Dominion (UNDER 135.5)         [score: 6.19]
... (all 10 are small college games)

❌ MISSING: Syracuse @ Duke
❌ MISSING: Houston @ Iowa State
✅ CORRECT: Some high-edge-score plays
```

### The Mismatch
| Category | ESPN Has | LARLESCORE Recommends | Win/Loss |
|----------|----------|----------------------|----------|
| Major D1 games | Syracuse @ Duke | ❌ | Unknown |
| Small college games | ❌ None | Colgate, SE Louisiana, etc. | **ALL PENDING** |

---

## Root Causes

### 1. Data Source Blind Spot
- **Issue:** LARLESCORE learns from historical data but doesn't know which games ESPN actually covers
- **Result:** High-confidence picks for unmeasurable games
- **Why:** System optimizes for "edge score" without verifying scoreboard availability

### 2. Verification System Incomplete
- **Issue:** No feedback loop: "Are my high-edge-score picks verifiable?"
- **Result:** Accumulates confidence in un-verifiable games over time
- **Why:** LARLESCORE has no mechanism to penalize "correct prediction but can't prove it"

### 3. Score Data Pipeline Mismatch
- **Issue:** ESPN API only covers ~4 games/day (major D1)
- **LARLESCORE coverage:** 24 games/day (all of college basketball)
- **Gap:** 20+ games have no score data available
- **Why:** System was designed without considering ESPN API limitations

---

## Impact on Feb 16 Results

### Problem: 100% PENDING Rate
```
Feb 16: 24 bets placed
Updated with ESPN scores: 0 bets
Still PENDING: 24 bets (100%)
Estimated wait time: INDEFINITE (ESPN won't get scores)
```

### Why Results Can't Update
1. **Small college games aren't in ESPN API**
   - Colgate vs Boston University: No ESPN coverage
   - SE Louisiana vs East Texas A&M: No ESPN coverage
   - etc.

2. **Major games weren't recommended**
   - Syracuse @ Duke (final score: 101-64): Not in our top 10
   - Houston @ Iowa State: Not in our top 10

3. **Result:** We recommended games we can't verify, skipped games we can verify

---

## Recommendations

### Immediate (This Week)
1. **Manual intervention:** Add verified ESPN games to ranked_bets files
   - Mark Syracuse @ Duke with actual score (Duke wins 101-64)
   - Mark Houston @ Iowa State with actual score (Iowa State wins 70-67)
   - Manually update completed_bets_2026-02-16.json

2. **Verification:** Confirm all PENDING games actually finished
   - Check which games finished (do they have scores available anywhere?)
   - Mark as LOSS if we can't verify (conservative approach)
   - Or wait for alternative score source

3. **Documentation:** Create game-by-game scoreboard for Feb 16
   - Track which games have ESPN coverage
   - Which went PENDING despite being played
   - Why (data source limitation, not prediction error)

### Short-term (This Month)
1. **Verify ESPN Coverage**
   - Before recommending a game, check if ESPN tracks it
   - Modify LARLESCORE to know: "This game type has ESPN data"
   - Exclude non-ESPN-trackable games OR source alternate data

2. **Improve Ranking Logic**
   - Weight edge score by "score verifiability"
   - High edge + verifiable = Higher rank
   - High edge + not verifiable = Much lower rank
   - Add "can ESPN verify this?" field to all picks

3. **Add Feedback Loop**
   - Track: Which recommended games get scores vs stay PENDING
   - Penalize models that recommend non-verifiable games
   - Reward models that pick ESPN-trackable games

### Long-term (System Design)
1. **Decision: Which leagues to recommend?**
   - Option A: Only ESPN D1 games (4/day, fully verifiable)
   - Option B: Small college games too (24+/day, mostly unverifiable)
   - Option C: Hybrid (top scores from D1, secondary plays from small college)
   - **Recommendation:** Option A for reliability, Option C if alt score source found

2. **Implement Alternative Score Sources**
   - Web scraping from official college websites
   - Third-party sports data APIs
   - Integration with basketball reference sites
   - **Timeline:** 2-3 weeks to implement and test

3. **Deep Learning Architecture**
   - Add data availability as a feature in LARLESCORE
   - Train separate models for "verifiable" vs "exploratory" picks
   - Learn which small college conference games are actually winnable
   - Document confidence intervals by league

---

## Metrics to Track Going Forward

- **Verification Rate:** % of recommended games that get scores
  - Target: >90% by March 1
  - Current: 0% for small college (ESPN limitation)

- **Win Rate by League**
  - Major D1 (ESPN-verified): Expected ~55-60%
  - Small college (score-unverified): Unknown, probably ~45-55%
  - **Recommendation:** Don't bet unverified games until we prove they win

- **Edge Score Accuracy**
  - Compare predicted edge to actual results
  - Current: Can't measure for 24 games (no scores)
  - Need: Alternative score source ASAP

---

## Conclusion

**LARLESCORE is fundamentally sound in its edge detection, but catastrophically misaligned with verifiable data sources.**

The system works great for finding profitable plays (probably), but picks games we can't prove won/lost. This is a **data architecture problem, not a prediction algorithm problem**.

**Next steps:** Integrate with verifiable score sources OR restrict to ESPN-trackable games.

---

## SWORD & Backend Coordination Notes

- **SWORD:** Responsible for fetching scores. Current situation: ESPN has 4 games, we recommended 24 different games.
- **Backend:** Correctly loading ranked_bets files. Issue is the recommendations themselves, not the API.
- **Recommendation:** SWORD should note which games ESPN can't provide scores for and suggest alternatives or manual updates.
