# 🛠️ QUALITY AUDIT FIXES - Implementation Guide

## Quick Summary

**Issues Found:** 3 Critical, 2 Major  
**Root Cause:** No historical learning loop; pure edge ranking that favors failing bet types  
**Time to Fix:** 2-4 hours for all critical fixes

---

## Critical Issue #1: Learning System Disabled

**Problem:**  
- System uses `pure_edge_ranking` instead of calibrated scoring
- No historical win rate data being tracked
- No day-to-day performance improvement

**Current Code (in bet_ranker.py):**
```python
'selection_method': '5_spreads_5_totals_2_moneylines'  # ← NOT BEING USED
```

**Actual Output (ranked_bets_2026-02-16.json):**
```json
"selection_method": "pure_edge_ranking"  # ← THIS IS RUNNING INSTEAD
```

**Fix:** Create `larlscore_v3.py` that implements historical learning:

```python
#!/usr/bin/env python3
"""
LARLScore v3.0 - Learning-Aware Ranking and Loss Score
Implements: Confidence calibration + historical win rate weighting
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

WORKSPACE = Path("/Users/macmini/.openclaw/workspace")

def calculate_confidence_calibration(completed_bets):
    """
    Track actual win rate vs claimed confidence for each bet type
    Returns: calibration_factors[bet_type][confidence] = actual_win_rate
    """
    calibration = defaultdict(lambda: defaultdict(list))
    
    for bet in completed_bets:
        if 'result' not in bet or 'bet_type' not in bet:
            continue
        
        bet_type = bet.get('bet_type', 'SPREAD').upper()
        confidence = bet.get('confidence', 70)
        result = 1 if bet['result'].upper() == 'WIN' else 0
        
        calibration[bet_type][confidence].append(result)
    
    # Convert to actual win rates
    calibration_rates = {}
    for bet_type in calibration:
        calibration_rates[bet_type] = {}
        for conf, results in calibration[bet_type].items():
            if results:
                actual_rate = sum(results) / len(results)
                calibration_rates[bet_type][conf] = {
                    'actual_rate': actual_rate,
                    'sample_size': len(results),
                    'expected_rate': conf / 100,
                    'error': abs(actual_rate - conf/100)
                }
    
    return calibration_rates

def get_calibration_factor(bet_type, confidence, calibration_rates):
    """
    Get adjustment factor for this bet type + confidence combo
    If 82% confidence has 100% actual win rate, factor = 1.0
    If 58% confidence has 0% actual win rate, factor = 0.0 (disable bet)
    """
    if bet_type not in calibration_rates:
        return 1.0  # No historical data, use default
    
    if confidence not in calibration_rates[bet_type]:
        # Find closest confidence level
        closest = min(
            calibration_rates[bet_type].keys(),
            key=lambda x: abs(x - confidence)
        )
        confidence = closest
    
    data = calibration_rates[bet_type].get(confidence, {})
    actual_rate = data.get('actual_rate', 0.5)
    
    # For TOTAL bets with 0% win rate, disable them
    if bet_type == 'TOTAL' and actual_rate < 0.1:
        return 0.0  # Red line: don't rank TOTAL bets
    
    return actual_rate

def score_bet_with_learning(bet, calibration_rates):
    """
    Score = (raw_edge * calibration_factor) + risk_adjustment
    
    Factors:
    - Use ACTUAL historical win rate, not claimed confidence
    - Penalize bet types with poor calibration
    - Disable catastrophically-failing bet types
    """
    bet_type = bet.get('bet_type', 'SPREAD').upper()
    claimed_confidence = bet.get('confidence', 70) / 100
    edge = bet.get('edge', 2.0)
    
    # Get calibration factor (what this confidence level ACTUALLY wins at)
    calibration_factor = get_calibration_factor(
        bet_type, 
        bet.get('confidence', 70),
        calibration_rates
    )
    
    # Cap edge to max 10 (prevent TOTAL dominance)
    capped_edge = min(edge, 10.0)
    edge_multiplier = 1.0 + (capped_edge / 10.0)
    
    # Risk adjustment
    risk_tier = bet.get('risk_tier', 'LOW RISK')
    risk_mult = 1.0 if 'LOW' in risk_tier else (0.9 if 'MODERATE' in risk_tier else 0.7)
    
    # CRITICAL: Use calibration_factor instead of claimed_confidence
    score = (calibration_factor * edge_multiplier * risk_mult) * 100
    
    return {
        'score': score,
        'calibration_factor': calibration_factor,
        'raw_edge': edge,
        'risk_multiplier': risk_mult,
        'debug': {
            'claimed_confidence': claimed_confidence * 100,
            'actual_win_rate': get_calibration_factor(bet_type, bet.get('confidence', 70), calibration_rates) * 100,
            'bet_type_performance': f"{bet_type} @ {bet.get('confidence')}%"
        }
    }

def rank_bets_with_learning(active_bets, completed_bets):
    """Main ranking function with historical learning"""
    
    # Step 1: Calculate calibration from historical data
    calibration_rates = calculate_confidence_calibration(completed_bets)
    
    # Step 2: Score each bet
    scored_bets = []
    for bet in active_bets:
        scoring = score_bet_with_learning(bet, calibration_rates)
        scored_bets.append({
            'bet': bet,
            'score': scoring['score'],
            'calibration_factor': scoring['calibration_factor'],
            'debug': scoring['debug']
        })
    
    # Step 3: Sort and rank
    scored_bets.sort(key=lambda x: x['score'], reverse=True)
    for i, item in enumerate(scored_bets, 1):
        item['rank'] = i
    
    # Step 4: Red line check - remove failing bet types
    final_top_10 = []
    for item in scored_bets:
        # Skip bets with 0 score (disabled by calibration)
        if item['score'] <= 0.1:
            continue
        final_top_10.append(item)
        if len(final_top_10) >= 10:
            break
    
    return final_top_10, calibration_rates

def save_ranked_with_learning(top_10, calibration_rates, completed_bets):
    """Save ranked bets with calibration data"""
    
    # Calculate performance summary
    perf_by_type = {}
    for bet in completed_bets:
        bet_type = bet.get('bet_type', 'SPREAD').upper()
        if bet_type not in perf_by_type:
            perf_by_type[bet_type] = {'wins': 0, 'losses': 0}
        
        if bet['result'].upper() == 'WIN':
            perf_by_type[bet_type]['wins'] += 1
        else:
            perf_by_type[bet_type]['losses'] += 1
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'selection_method': 'larlescore_v3_learning',
        'calibration_data': {
            str(k): {str(conf): v for conf, v in val.items()}
            for k, val in calibration_rates.items()
        },
        'performance_by_type': perf_by_type,
        'top_10': []
    }
    
    for item in top_10:
        bet = item['bet']
        output['top_10'].append({
            'rank': item['rank'],
            'score': round(item['score'], 2),
            'game': bet.get('game'),
            'bet_type': bet.get('bet_type'),
            'recommendation': bet.get('recommendation'),
            'claimed_confidence': bet.get('confidence'),
            'calibration_factor': round(item['calibration_factor'], 3),
            'actual_expected_win_rate': round(item['calibration_factor'] * 100, 1),
            'edge': bet.get('edge'),
            'risk_tier': bet.get('risk_tier'),
            'game_time': bet.get('game_time'),
            'reason': bet.get('reason'),
            'debug_info': item['debug']
        })
    
    # Save
    with open(WORKSPACE / 'ranked_bets_larlescore_v3.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    return output

# Example usage
if __name__ == '__main__':
    # Load data
    with open(WORKSPACE / 'completed_bets_2026-02-16.json') as f:
        completed = json.load(f)['bets']
    
    with open(WORKSPACE / 'active_bets.json') as f:
        active = json.load(f)['bets']
    
    # Rank with learning
    top_10, calibration = rank_bets_with_learning(active, completed)
    
    # Save
    save_ranked_with_learning(top_10, calibration, completed)
    
    print("✅ LARLScore v3 ranking complete")
    print(f"   Tracked {len(calibration)} bet types with calibration data")
    print(f"   Ranked top {len(top_10)} bets using historical win rates")
```

---

## Critical Issue #2: TOTAL Bets Have 0% Win Rate

**Problem:**
- All 5 TOTAL bets in top 10 lost (0% win rate)
- Yet they're ranked #1-5 by pure edge metric
- This is backwards logic

**Why It Happened:**
- TOTAL bets have large edge numbers (21.5) due to how edge is calculated
- Scoring function: `score = confidence * edge * win_rate`
- TOTAL edge is inflated (21pt vs 6pt for spreads)
- But actual predictions are systematically low

**Quick Fix - Red Line in bet_ranker.py:**

```python
def score_bet(bet, win_rates):
    """..."""
    bet_type = bet.get('bet_type', 'SPREAD').upper()
    
    # 🛑 RED LINE: Don't rank TOTAL bets (0% historical win rate)
    if bet_type == 'TOTAL':
        total_win_rate = win_rates.get('TOTAL', 0.0)
        if total_win_rate < 0.1:  # Less than 10% win rate
            return -999  # Disable from ranking
    
    # ... rest of scoring logic
```

---

## Critical Issue #3: Confidence Miscalibration

**Problem:**
- 58% confidence bets: 0% actual win rate (40pt error)
- 60% confidence bets: 20% actual win rate (40pt error)
- 82% confidence bets: 100% actual win rate (but small sample)

**Fix - Calibration Check Script:**

```python
def validate_confidence_calibration(completed_bets, threshold=10):
    """Daily validation: flag any confidence level with >10pt error"""
    
    conf_buckets = defaultdict(list)
    for bet in completed_bets:
        conf = bet.get('confidence', 70)
        result = 1 if bet['result'] == 'WIN' else 0
        conf_buckets[conf].append(result)
    
    issues = []
    for conf, results in conf_buckets.items():
        actual = 100 * sum(results) / len(results)
        error = abs(actual - conf)
        
        if error > threshold:
            issues.append({
                'confidence': conf,
                'claimed': f"{conf}%",
                'actual': f"{actual:.0f}%",
                'error': f"{error:.0f}pt",
                'severity': 'CRITICAL' if error > 30 else 'WARNING'
            })
    
    return issues
```

**Action:** Run this daily, alert if any confidence level has >30pt error.

---

## Major Issue #1: Simulated Data Instead of Real Scores

**Problem:**
```json
"processing_notes": {
  "matched_from_ncaa_api": 0,
  "simulated_scores": 15
}
```

**Why It's Bad:**
- Can't learn from real data if we're using fake scores
- System is backfitting to hit target win rates (70% for top 10)
- Real NCAA games will fail differently

**Fix:**
1. Use real ESPN API or NCAA API data only
2. Remove simulated score generation
3. Accept real win rates (even if not 70%)

---

## Major Issue #2: No Historical Tracking File

**Missing:** `historical_performance.json`

**Create it:**

```python
def init_historical_tracking():
    """Create historical performance database"""
    
    historical = {
        'by_bet_type': {
            'SPREAD': {
                'all_time': {'wins': 0, 'losses': 0},
                'by_confidence': {}
            },
            'TOTAL': {
                'all_time': {'wins': 0, 'losses': 0},
                'by_confidence': {}
            },
            'MONEYLINE': {
                'all_time': {'wins': 0, 'losses': 0},
                'by_confidence': {}
            }
        },
        'by_edge_bucket': {
            '0-2pt': {'wins': 0, 'losses': 0},
            '2-5pt': {'wins': 0, 'losses': 0},
            '5-10pt': {'wins': 0, 'losses': 0},
            '10+pt': {'wins': 0, 'losses': 0}
        },
        'daily_snapshots': {}
    }
    
    with open(WORKSPACE / 'historical_performance.json', 'w') as f:
        json.dump(historical, f, indent=2)
```

---

## Implementation Checklist

- [ ] Create `larlscore_v3.py` with calibration logic
- [ ] Add red line check for failing bet types
- [ ] Implement daily confidence calibration validation
- [ ] Create `historical_performance.json` tracker
- [ ] Update `active_bets.json` generation to use real NCAA API only
- [ ] Remove simulated score generation
- [ ] Add unit tests for WIN/LOSS scoring logic
- [ ] Daily automated check: calibration vs actual (alert if >30pt error)
- [ ] Weekly review: Did we learn? Are confidence adjustments helping?

---

## Monitoring Dashboard

Add to daily reports:

```
CONFIDENCE CALIBRATION STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Confidence   Actual   Error   Status
70%          73%      +3pt    ✓ OK
75%          68%      -7pt    ✓ OK  
80%          75%      -5pt    ✓ OK
82%          100%     +18pt   ⚠ REVIEW (small sample?)
58%          0%       -58pt   ❌ DISABLE

BET TYPE PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type         W-L      %       Trend
SPREAD       10-4     71%     ✓ Stable
MONEYLINE   1-4      20%     ❌ Disabled
TOTAL        0-5      0%      ❌ Disabled

LEARNING LOOP STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Historical data tracked
[ ] Calibration factors updated
[ ] Red lines enforced
[ ] Recommendations adjusted
```

---

## Testing

```bash
# Verify scoring logic
python3 -c "
from auto_result_tracker_v2 import score_under_bet
assert score_under_bet(79, 67, 143.5) == 'LOSS'  # 146 > 143.5
assert score_under_bet(140, 70, 143.5) == 'WIN'  # 210 > 143.5
assert score_under_bet(70, 70, 143.5) == 'WIN'   # 140 < 143.5
print('✅ Scoring logic correct')
"

# Verify learning is working
python3 larlscore_v3.py
grep "selection_method" ranked_bets_larlescore_v3.json
# Should show: "selection_method": "larlescore_v3_learning"
```

---

## Deployment

```bash
# Backup current system
cp ranked_bets.json ranked_bets_backup_feb17.json
cp bet_ranker.py bet_ranker_backup_feb17.py

# Deploy new system
python3 larlscore_v3.py

# Monitor for 24 hours
tail -f bet_tracking.log | grep LEARNING

# If good, make permanent
cp ranked_bets_larlescore_v3.json ranked_bets.json
```

---

**Next Steps:** Implement learning loop first (critical), then fix TOTAL/ML bets, then deploy historical tracking.
