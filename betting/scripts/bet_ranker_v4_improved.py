#!/usr/bin/env python3
"""
🚀 Improved Bet Ranker using LarlScore v4.0
Applies data-driven improvements from deep historical analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

WORKSPACE = Path("/Users/macmini/.openclaw/workspace")

def load_active_bets() -> List[Dict]:
    """Load today's active bets"""
    try:
        with open(WORKSPACE / 'active_bets.json', 'r') as f:
            data = json.load(f)
            return data.get('bets', [])
    except Exception as e:
        print(f"Error loading active_bets.json: {e}")
        return []

def calculate_larlescore_v4(bet: Dict) -> float:
    """
    🚀 LarlScore v4.0 - Improved Formula
    
    Based on deep analysis findings:
    - High Edge (10+ pts) wins 75-100% → boost heavily
    - Low Edge (<5pts) wins only 45% → suppress
    - High Confidence (80%+) improves all types → boost
    - MONEYLINE (0% win rate) → disable
    - TOTAL with edge 20+ = 100% → special boost
    - TOTAL overall weak (40%) → suppress unless high edge
    
    Formula:
    base = (confidence/100) × edge × (bet_type_win_rate / 0.5)
    
    Then apply multipliers:
    - Edge bonus: 1.3x if 10-19pts, 1.5x if 20+pts
    - Edge penalty: 0.5x if <5pts
    - Confidence bonus: 1.2x if 80%+, 1.1x if 75%+
    - MONEYLINE penalty: 0x (disabled)
    - TOTAL penalty: 0.75x (weak historically) unless edge >=20
    """
    
    bet_type = bet.get('bet_type', 'SPREAD').upper()
    confidence = bet.get('confidence', 70)
    edge = bet.get('edge', 2.0)
    
    # Historical win rates by type
    win_rates = {
        'SPREAD': 0.636,     # 7W-4L (63.6%)
        'TOTAL': 0.400,      # 6W-9L (40%) - weak overall
        'MONEYLINE': 0.0     # 0W-3L (0%) - disable
    }
    
    # FIRST CHECK: DISABLE MONEYLINE
    if bet_type == 'MONEYLINE':
        return 0.0  # Not recommended
    
    win_rate = win_rates.get(bet_type, 0.5)
    
    # Base score
    base = (confidence / 100) * edge * (win_rate / 0.5)
    
    # EDGE MULTIPLIERS
    if edge >= 20:
        edge_mult = 1.5  # Very high edge - almost guaranteed
    elif edge >= 10:
        edge_mult = 1.3  # High edge - strong predictor
    elif edge < 5:
        edge_mult = 0.5  # Low edge - unreliable
    else:
        edge_mult = 1.0  # Normal edge
    
    # CONFIDENCE MULTIPLIERS
    if confidence >= 80:
        conf_mult = 1.2  # Very confident
    elif confidence >= 75:
        conf_mult = 1.1  # Fairly confident
    else:
        conf_mult = 1.0  # Standard
    
    # BET TYPE SPECIAL HANDLING
    bet_type_mult = 1.0
    if bet_type == 'TOTAL':
        if edge >= 20:
            bet_type_mult = 1.4  # TOTAL with high edge is golden (80% historical)
        else:
            bet_type_mult = 0.75  # TOTAL weak unless high edge
    elif bet_type == 'SPREAD':
        bet_type_mult = 1.22  # SPREAD is our best performer
    
    # Final score
    score = base * edge_mult * conf_mult * bet_type_mult
    
    return score

def rank_today_bets(bets: List[Dict]) -> List[Dict]:
    """Rank today's bets by v4.0 score"""
    scored_bets = []
    
    for i, bet in enumerate(bets, 1):
        score = calculate_larlescore_v4(bet)
        
        scored_bets.append({
            'rank': 0,  # Will be filled in
            'game': bet.get('game', 'Unknown'),
            'bet_type': bet.get('bet_type', 'UNKNOWN'),
            'recommendation': bet.get('recommendation', 'N/A'),
            'confidence': bet.get('confidence', 0),
            'edge': bet.get('edge', 0),
            'fanduel_line': bet.get('fanduel_line', 'N/A'),
            'game_time': bet.get('game_time', 'TBD'),
            'score_v4': score,
            'full_bet': bet,
        })
    
    # Sort by score descending
    scored_bets.sort(key=lambda x: x['score_v4'], reverse=True)
    
    # Assign ranks
    for i, item in enumerate(scored_bets, 1):
        item['rank'] = i
    
    return scored_bets

def save_improved_rankings(scored_bets: List[Dict]):
    """Save improved rankings to file"""
    
    # Separate top 10 from rest
    top_10 = scored_bets[:10]
    rest = scored_bets[10:]
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'larlescore_version': '4.0',
        'larlescore_formula': 'base × edge_mult × conf_mult × bet_type_mult',
        'improvements_applied': [
            'High Edge (10+ pts) boosted 30-50%',
            'Low Edge (<5 pts) penalized 50%',
            'High Confidence (80%+) boosted 20%',
            'MONEYLINE disabled (0% historical win rate)',
            'TOTAL: 0.75x unless edge >= 20pts (then 1.4x)',
            'SPREAD: 1.22x boost (63.6% win rate)',
        ],
        'top_10': [
            {
                'rank': item['rank'],
                'score': round(item['score_v4'], 1),
                'game': item['game'],
                'bet_type': item['bet_type'],
                'recommendation': item['recommendation'],
                'confidence': item['confidence'],
                'edge': item['edge'],
                'fanduel_line': item['fanduel_line'],
                'game_time': item['game_time'],
                'full_bet': item['full_bet'],
            }
            for item in top_10
        ],
        'rest': [
            {
                'rank': item['rank'],
                'score': round(item['score_v4'], 1),
                'game': item['game'],
                'bet_type': item['bet_type'],
            }
            for item in rest
        ],
        'summary': {
            'total_bets': len(scored_bets),
            'top_10_avg_confidence': round(sum(item['confidence'] for item in top_10) / 10, 1) if top_10 else 0,
            'top_10_avg_edge': round(sum(item['edge'] for item in top_10) / 10, 1) if top_10 else 0,
            'by_type': {
                'SPREAD': sum(1 for item in top_10 if item['bet_type'] == 'SPREAD'),
                'TOTAL': sum(1 for item in top_10 if item['bet_type'] == 'TOTAL'),
                'MONEYLINE': sum(1 for item in top_10 if item['bet_type'] == 'MONEYLINE'),
            }
        }
    }
    
    # Save to ranked_bets_v4.json
    with open(WORKSPACE / 'ranked_bets_v4.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Also save as ranked_bets.json (main dashboard file)
    with open(WORKSPACE / 'ranked_bets.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Save dated version
    today = datetime.now().strftime("%Y-%m-%d")
    with open(WORKSPACE / f'ranked_bets_{today}.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    return output

def print_results(scored_bets: List[Dict], output: Dict):
    """Print results"""
    print("\n" + "="*100)
    print("🚀 LARLESCORE v4.0 - IMPROVED RANKINGS")
    print("="*100)
    
    print("\n📊 TOP 10 PICKS (New Rankings):")
    print("-"*100)
    print(f"{'#':3} {'Score':8} {'Type':10} {'Game':40} {'Conf':6} {'Edge':6}")
    print("-"*100)
    
    for i, item in enumerate(scored_bets[:10], 1):
        game = item['game'][:40]
        print(f"{i:3} {item['score_v4']:8.1f} {item['bet_type']:10} {game:40} {item['confidence']:5}% {item['edge']:6.1f}")
    
    # Summary
    summary = output['summary']
    print("\n" + "="*100)
    print("📈 TOP 10 SUMMARY:")
    print("="*100)
    print(f"  Avg Confidence: {summary['top_10_avg_confidence']}%")
    print(f"  Avg Edge: {summary['top_10_avg_edge']} pts")
    print(f"  SPREAD picks: {summary['by_type']['SPREAD']}")
    print(f"  TOTAL picks: {summary['by_type']['TOTAL']}")
    print(f"  MONEYLINE picks: {summary['by_type']['MONEYLINE']}")
    
    print("\n💡 KEY IMPROVEMENTS FROM v3.0 → v4.0:")
    for improvement in output['improvements_applied']:
        print(f"  ✓ {improvement}")
    
    print("\n✅ RESULTS SAVED TO:")
    print(f"  • ranked_bets.json (main dashboard)")
    print(f"  • ranked_bets_v4.json (backup)")
    print(f"  • ranked_bets_2026-02-17.json (dated)")

def main():
    """Main execution"""
    print("\n🚀 Bet Ranker v4.0 - Applying Improved Formula")
    print("="*100)
    
    # Load active bets
    bets = load_active_bets()
    print(f"\n✅ Loaded {len(bets)} active bets")
    
    if not bets:
        print("❌ No active bets found")
        return
    
    # Rank with v4.0
    scored = rank_today_bets(bets)
    
    # Save results
    output = save_improved_rankings(scored)
    
    # Print results
    print_results(scored, output)
    
    print("\n" + "="*100)
    print("✅ V4.0 RANKING COMPLETE - Ready for Sword to use")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()
