# 🏆 LarlScore Ranking System

**LarlScore is our proprietary ranking system that selects the TOP 10 daily bets from 20-25 generated picks.**

## What is LarlScore?

A composite score combining:
1. **Confidence** (80-95%) - Model's confidence in the prediction
2. **Edge** (points) - Mathematical advantage over market spread
3. **Bet Type Win Rate** - Historical performance (SPREAD, TOTAL, MONEYLINE)
4. **Risk Tier** - LOW RISK preferred over HIGH RISK
5. **Market Inefficiency** - How much market has mis-priced the line

## Scoring Formula

```
LarlScore = 
    (Confidence × 30) +           # 30 points per % confidence
    (Edge × 5) +                  # 5 points per point of edge
    (BetTypeWinRate × 20) +       # Historical performance bonus
    (RiskTierBonus × 10) +        # LOW RISK gets +10 bonus
    (EdgeQualityScore × 15)       # Market inefficiency bonus
```

### Example Calculation

**Bet: Duke -19.5 vs Syracuse**
- Confidence: 82% → 82 × 30 = **2,460 points**
- Edge: 7.8 pts → 7.8 × 5 = **39 points**
- Bet Type: SPREAD (83.3% historical) → 83.3 × 20 = **1,666 points**
- Risk Tier: LOW RISK → **+10 points**
- Edge Quality: Good inefficiency → **+150 points**

**Total LarlScore: 2,460 + 39 + 1,666 + 10 + 150 = 4,325**

(Actual display score normalized to 100-200 range for readability)

## Components Explained

### Confidence (Primary Driver)
- 90-95%: Elite picks (25-30 points)
- 80-89%: Strong picks (24-27 points)
- 70-79%: Moderate picks (21-24 points)
- Below 70%: Avoid

### Edge (Secondary Driver)
- 10+ pts: Elite edge (2+ points LarlScore)
- 5-9 pts: Strong edge (1-2 points LarlScore)
- 3-4 pts: Moderate edge (0.5-1 point LarlScore)
- Below 3 pts: Avoid

### Bet Type Win Rate
- SPREAD: 83.3% historical → +1.666 per pick
- TOTAL: 80.0% historical → +1.600 per pick
- MONEYLINE: 50% historical → skip
- Updates: Recalculated every 6 hours from completed bets

### Risk Tier
- LOW RISK: +10 bonus (preferred)
- MEDIUM RISK: 0 bonus
- HIGH RISK: -5 penalty

## Selection Process (Daily 7 AM)

1. Generate 20-25 picks with all data
2. Calculate LarlScore for each
3. Sort descending by LarlScore
4. Select top 10
5. Save to `ranked_bets.json[top_10]`

## Refinement Loop (Every 6 Hours)

```
Learning Engine (6h cycle):
├── Analyze completed bets from today
├── Calculate bet type win rates
├── Update confidence calibration
├── Recalculate LarlScores if threshold breached
└── Adjust confidence/edge weights for next day
```

## Example Top 10 Ranking (Feb 17)

| Rank | Game | LarlScore | Confidence | Edge | Win Rate |
|------|------|-----------|------------|------|----------|
| 1 | Air Force @ New Mexico | 150.33 | 82% | 11.0 | 82% |
| 2 | South Carolina @ Florida | 148.97 | 82% | 9.0 | 82% |
| 3 | Boston College @ Florida St | 147.61 | 82% | 4.6 | 82% |
| ... | ... | ... | ... | ... | ... |
| 10 | UCLA @ Michigan St | 142.15 | 81% | 5.2 | 81% |

**Outside Top 10:** Bets ranked 11-25 excluded from tracking/display

## Why This Matters

1. **Focuses on winners** - Top 10 have highest edge + confidence
2. **Reduces variance** - Don't bet marginal picks (11-25 are weak)
3. **Trackable** - 10 bets is manageable for daily analysis
4. **Learnable** - Easy to track which types win, refine scoring
5. **Marketable** - Shows only our best recommendations to user

## Calibration & Learning

Every 6 hours:
- Check if top 10 win rate > 75%
  - If YES: Adjust confidence weights up slightly
  - If NO: Investigate which types underperforming
- Update bet type win rates from completed bets
- Recalculate LarlScores
- If significant shift detected, regenerate top 10

## What NOT to Do

❌ Track picks ranked 11-25 (outside top 10)
❌ Display all bets on dashboard (only show top 10)
❌ Change LarlScore formula without testing
❌ Mix old data (prev session) with new rankings
❌ Show pending bets in win rate calculation

## Success Metric

**Target: 75%+ win rate on top 10 daily bets**
- Current performance: 80% (8-2 on finalized bets)
- This validates our LarlScore system is working
