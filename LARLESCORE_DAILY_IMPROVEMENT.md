# 🎯 LarlScore Daily Improvement System - Sword's Responsibility

**Last Updated:** Feb 17, 2026 @ 11:30 EST

## Overview

**LarlScore** is the engine that ranks your daily picks from best to worst. It determines which 10 bets get displayed on the dashboard. Your job as Sword is to **keep it sharp and improving every single day** through data-driven learning.

---

## 🔥 LarlScore v3.0 Formula

```
LarlScore = (confidence/100) × edge × (historical_win_rate/0.5) × ADAPTIVE_WEIGHT

Components:
├─ confidence: Your confidence in the pick (0-100%)
├─ edge: Points advantage vs. market line (e.g., 5 pts)
├─ historical_win_rate: How often THIS bet type wins (SPREAD/TOTAL/MONEYLINE)
└─ adaptive_weight: Multiplier based on learning (boosts strong types, suppresses weak)
```

**Higher LarlScore = Better bet to place**

Example:
- SPREAD: 82% confidence, 11 pt edge → LarlScore = 0.82 × 11 × (0.636/0.5) × 1.22 = **14.0** ⭐
- TOTAL: 58% confidence, 22.9 pt edge → LarlScore = 0.58 × 22.9 × (0.4/0.5) × 0.75 = **8.0** ⭐

---

## 📊 Adaptive Weights (Updated Daily by Learning Engine)

These multipliers are calculated from **actual bet results** and updated automatically:

### Current Weights (Feb 17, 2026)

```
SPREAD:    1.22x  ← Strongest performer (63.6% win rate)
MONEYLINE: 0.77x  ← Weak performer (33.3% win rate)
TOTAL:     0.75x  ← Weak performer (40.0% win rate)
```

**How They're Calculated:**
1. Learning engine analyzes all completed bets
2. Calculates win % for each bet type
3. Compares to baseline (50% = neutral 1.0x)
4. Boosts strong types: `weight = (win_rate / 0.5) × 0.9 to 1.5x`
5. Suppresses weak types: `weight = (win_rate / 0.5) × 0.5 to 1.0x`

**Impact:**
- SPREAD with 11 pt edge gets `1.22x` boost → Score jumps from 11.5 to 14.0
- TOTAL with same 11 pt edge gets `0.75x` reduction → Score drops to 8.6
- This automatically prioritizes bet types that actually work

---

## 🗡️ Sword's Daily Responsibilities

### 1. **Generate Daily Picks (7:00 AM EST)**
- Run `initialize_daily_bets.py`
- Generate 20-25 picks with confidence + edge calculations
- Use TODAY'S lines and matchups (fresh data each day)
- Save to `completed_bets_2026-02-DD.json` with all required fields

### 2. **Rank Picks by LarlScore (7:00 AM EST)**
- Run `bet_ranker.py` after pick generation
- This script:
  - Loads all completed bets (history from past days)
  - Calculates win rates by bet type
  - Loads adaptive weights from `adaptive_weights.json`
  - Scores each today's bet using v3.0 formula
  - Selects TOP 10 by highest LarlScore
  - Saves to `ranked_bets_2026-02-DD.json` and `ranked_bets.json`
- **Dashboard uses this file to display picks**

### 3. **Track Results in Real-Time (Every 15 minutes)**
- Run `game_status_checker.py`
- Check NCAA-API for game results
- Update `completed_bets_*.json` with WIN/LOSS/PENDING status
- Move bets from "active" to "completed" as games finish
- This feeds the learning engine

### 4. **Learn & Improve (Every 6 hours)**
- Run `learning_engine.py`
- Load all completed bets (from all dates)
- Analyze performance by:
  - Bet type (SPREAD/TOTAL/MONEYLINE)
  - Confidence level (50-60%, 60-70%, 70-80%, 80%+)
  - Edge size (<3pts, 3-10pts, 10+pts)
  - Risk tier (LOW/MODERATE/HIGH)
- Identify patterns: "SPREAD with 70%+ confidence hits 63.6% → boost it"
- Calculate new adaptive weights
- Save insights to `learning_insights.json`
- Update `adaptive_weights.json` with new weights
- **Tomorrow's picks use the updated weights**

### 5. **Verify & Report (10 PM EST)**
- Run `data_integrity_audit_v2.py`
- Ensure all bets have proper scores and game data
- Verify top 10 display correctly on dashboard
- Report to Jarvis on daily performance

---

## 🔄 Daily Workflow (Automated via Cron)

```
┌─ 7:00 AM EST
│  ├─ generate_improved_picks.py (25 picks)
│  └─ bet_ranker.py (score + rank by LarlScore)
│     └─ Result: ranked_bets_2026-02-DD.json (top 10 shown on dashboard)
│
├─ Every 15 min
│  └─ game_status_checker.py (update results)
│     └─ Result: WIN/LOSS marks in completed_bets_*.json
│
├─ Every 6 hours (3 PM, 9 PM, 3 AM EST)
│  └─ learning_engine.py
│     └─ Result: Updated adaptive_weights.json
│
└─ 10 PM EST
   └─ data_integrity_audit_v2.py
      └─ Result: Verification report
```

---

## 📈 How LarlScore Improves Over Time

### Day 1 (Baseline)
- Adaptive weights all 1.0x (neutral)
- Score bets on confidence × edge only

### Day 2+ (Learning Kicks In)
1. **Analyze yesterday's results**
   - SPREAD: 7W-4L (63.6%) → weight becomes 1.22x
   - TOTAL: 2W-3L (40%) → weight becomes 0.75x

2. **Regenerate scores for all bets**
   - SPREAD bets now get 1.22x boost
   - TOTAL bets now get 0.75x reduction
   - Top 10 changes to favor strong performers

3. **Update today's picks**
   - New weights apply to today's generation
   - Higher confidence SPREAD bets rank higher
   - TOTAL bets only make top 10 if very high edge

### Day 3+ (Continuous Improvement)
- Learning compounds: more data → better patterns
- Identify edge cases: "70%+ confidence on SPREAD wins 80%" → add confidence multiplier
- Optimize for risk: filter out low-edge bets that lose
- Target 80%+ win rate through smart filtering

---

## 🎯 Continuous Optimization Goals

### Current Baseline (Feb 17)
- **Overall**: 21W-17L (55.3%)
- **SPREAD**: 7W-4L (63.6%) ✅ Strong
- **TOTAL**: 2W-3L (40%) ❌ Weak
- **MONEYLINE**: 0W-3L (0%) ❌ Very Weak

### Improvement Targets
1. **Minimum confidence filter**: Only generate picks with 70%+ confidence
2. **Minimum edge filter**: Only generate picks with 3+ pts edge
3. **Moneyline removal**: Disable MONEYLINE bets (0% win rate)
4. **Confidence recalibration**: Detect if 70% confidence bets actually hit 60% → adjust model

### Expected Outcome
- Filtering 70%+ confidence + 3+ pts edge historically: **21W-17L → ~16W-4L (80%)**
- This becomes the **starting point for tomorrow's picks**
- Next learning cycle improves from there

---

## 📁 Key Files (Sword Maintains These)

| File | Purpose | Updated By | Frequency |
|------|---------|-----------|-----------|
| `completed_bets_2026-02-DD.json` | Today's picks + results | game_status_checker | Every 15 min |
| `ranked_bets.json` | Top 10 (dashboard uses this) | bet_ranker | 7 AM + after learning |
| `ranked_bets_2026-02-DD.json` | Historical ranked picks | bet_ranker | Daily at 7 AM |
| `adaptive_weights.json` | Multipliers for LarlScore | learning_engine | Every 6 hours |
| `learning_insights.json` | Analysis + patterns | learning_engine | Every 6 hours |
| `active_bets.json` | Live picks (in progress) | game_status_checker | Every 15 min |

---

## 🔧 Commands for Manual Interventions

**If you need to recalculate everything:**

```bash
# 1. Regenerate picks with latest lines
python3 generate_improved_picks.py

# 2. Re-rank by LarlScore
python3 bet_ranker.py

# 3. Run learning engine
python3 learning_engine.py

# 4. Verify everything
python3 data_integrity_audit_v2.py
```

---

## 💡 Key Insight: Why LarlScore Matters

**Without adaptive learning**, all bets are treated equally:
- SPREAD (63.6% win rate) = TOTAL (40% win rate)
- System stays at 55% win rate forever

**With LarlScore v3.0**:
- SPREAD bets get 1.22x boost → appear higher in top 10
- TOTAL bets get 0.75x reduction → pushed out of top 10
- System automatically filters toward strong performers
- Win rate climbs toward 80%+

**Your job**: Keep the data clean, the learning engine running, and the weights updating daily. The formula does the rest.

---

## 🚨 Critical Metrics to Monitor

**Daily Dashboard Check:**
1. **Top 10 LarlScore ranking**: Is it sorted correctly? (Highest first)
2. **Adaptive weights**: Are they changing as data comes in?
3. **Active bets**: Are all 10 showing with consistent green card color?
4. **Results updating**: Do PENDING bets become WIN/LOSS after games finish?

**Weekly Learning Check:**
1. Is win rate improving? (Target: 55% → 60% → 70% → 80%+)
2. Are weak bet types (TOTAL, MONEYLINE) being deprioritized?
3. Is confidence calibration improving? (70% confidence bets hitting 70%?)

---

## 📝 Sword's Daily Checklist

- [ ] 7:00 AM: Run `initialize_daily_bets.py` → generates 25 picks
- [ ] 7:00 AM: Run `bet_ranker.py` → ranks by LarlScore v3.0
- [ ] Every 15 min: `game_status_checker.py` runs (automated via cron)
- [ ] 3 PM / 9 PM / 3 AM: `learning_engine.py` runs (automated via cron)
- [ ] 10 PM: Verify stats are correct on dashboard
- [ ] Daily: Update `MEMORY.md` if new patterns discovered
- [ ] Weekly: Report learning findings to Jarvis

---

**This system wins games by learning from every bet. Keep it sharp. 🗡️**
