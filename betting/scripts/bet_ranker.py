#!/usr/bin/env python3
"""
Bet Ranker - Score and rank bets based on historical performance

Calculates:
1. Win % by bet type (SPREAD, MONEYLINE, TOTAL)
2. Composite score: (confidence * win_rate_for_type * edge) + historical_boost
3. Top 10 ranking for dashboard display
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

WORKSPACE = Path("/Users/macmini/.openclaw/workspace")

def load_completed_bets():
    """Load all completed bets from completed_bets_*.json files"""
    all_bets = []
    
    # Find all completed_bets files
    for filename in WORKSPACE.glob("completed_bets_*.json"):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'bets' in data:
                    all_bets.extend(data['bets'])
                elif isinstance(data, list):
                    all_bets.extend(data)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    return all_bets

def calculate_bet_type_performance(completed_bets):
    """Calculate win % for each bet type"""
    performance = {
        'SPREAD': {'wins': 0, 'losses': 0},
        'MONEYLINE': {'wins': 0, 'losses': 0},
        'TOTAL': {'wins': 0, 'losses': 0}
    }
    
    for bet in completed_bets:
        if 'result' not in bet or 'bet_type' not in bet:
            continue
        
        bet_type = bet.get('bet_type', 'SPREAD').upper()
        if bet_type not in performance:
            performance[bet_type] = {'wins': 0, 'losses': 0}
        
        if bet['result'].upper() == 'WIN':
            performance[bet_type]['wins'] += 1
        elif bet['result'].upper() == 'LOSS':
            performance[bet_type]['losses'] += 1
    
    # Convert to win rates
    win_rates = {}
    for bet_type, stats in performance.items():
        total = stats['wins'] + stats['losses']
        if total > 0:
            win_rates[bet_type] = stats['wins'] / total
        else:
            win_rates[bet_type] = 0.5  # Default to 50% if no data
    
    return win_rates, performance

def load_adaptive_weights():
    """Load adaptive weights from learning system"""
    try:
        with open(WORKSPACE / 'adaptive_weights.json', 'r') as f:
            data = json.load(f)
            return data.get('weights', {})
    except:
        # Default weights if file doesn't exist
        return {
            'SPREAD': {'weight': 1.0},
            'MONEYLINE': {'weight': 1.0},
            'TOTAL': {'weight': 1.0}
        }

def score_bet(bet, win_rates):
    """
    Calculate LARLScore for a bet using the ADAPTIVE formula
    
    🎯 ADAPTIVE FORMULA (v3.0):
    LARLScore = (confidence/100) × edge × (historical_win_rate / 0.5) × ADAPTIVE_WEIGHT
    
    This properly weights:
    - Confidence in the pick (0-100%)
    - Edge identified vs. market (points or %)
    - Historical success rate of this bet type
    - Adaptive weight based on learning system (boosts strong types, suppresses weak types)
    
    Higher score = better bet to place
    """
    bet_type = bet.get('bet_type', 'SPREAD').upper()
    confidence = max(0, bet.get('confidence', 70)) / 100  # Convert to 0-1, clamp non-negative
    edge = max(0.0, float(bet.get('edge', 2.0)))  # Clamp edge to non-negative
    
    # Use historical win rate from actual bet performance
    # Default to 50% if bet type not yet tracked
    win_rate = win_rates.get(bet_type, 0.5)
    
    # Load and apply adaptive weight
    adaptive_weights = load_adaptive_weights()
    adaptive_weight = adaptive_weights.get(bet_type, {}).get('weight', 1.0)
    
    # Skip disabled bet types (weight <= 0)
    if adaptive_weight <= 0:
        return 0.0
    
    # 🔥 ADAPTIVE LARLESCORE FORMULA v3.0:
    # LARLScore = (confidence) × edge × (win_rate / 0.5) × ADAPTIVE_WEIGHT
    larlescore = confidence * edge * (win_rate / 0.5) * adaptive_weight
    
    return larlescore

def deduplicate_conflicting_bets(scored_bets):
    """
    Remove conflicting bets (both sides of the same game/bet_type).
    
    For SPREAD bets on the same game, keep only the FIRST (highest scored) one.
    For TOTAL bets on the same game, keep only the FIRST (highest scored) one.
    For MONEYLINE bets on the same game, keep only the FIRST (highest scored) one.
    
    This prevents betting both sides of the same game, which guarantees losing juice.
    
    INPUT: scored_bets must already be sorted by score (descending)
    OUTPUT: filtered list with no duplicate game+bet_type combinations
    """
    seen_keys = set()
    filtered = []
    
    for item in scored_bets:
        bet = item['bet']
        game = (bet.get('game') or bet.get('game_name') or '').strip()
        bet_type = bet.get('bet_type', 'SPREAD').upper()
        
        key = (game, bet_type)
        
        if key not in seen_keys:
            # First time seeing this game + bet_type combo - keep it
            seen_keys.add(key)
            filtered.append(item)
        # else: skip this bet (it's a duplicate/opposite side)
    
    return filtered

def rank_today_bets(today_bets, win_rates):
    """Rank today's bets by score, removing conflicting bets and low-quality picks"""
    scored_bets = []
    low_quality_count = 0
    
    for bet in today_bets:
        # FILTER: Skip bets with LOW data quality (using default stats)
        if bet.get('data_quality') == 'LOW':
            low_quality_count += 1
            continue  # Don't include in ranked list
        
        score = score_bet(bet, win_rates)
        scored_bets.append({
            'bet': bet,
            'score': score,
            'rank': 0  # Will be filled in
        })
    
    if low_quality_count > 0:
        print(f"[*] Filtered {low_quality_count} low-data-quality bets")
    
    # Sort by score descending (highest first)
    scored_bets.sort(key=lambda x: x['score'], reverse=True)
    
    # 🔧 CRITICAL FIX: Remove conflicting bets (both sides of same game)
    scored_bets = deduplicate_conflicting_bets(scored_bets)
    
    # Re-sort after deduplication (order might have changed)
    scored_bets.sort(key=lambda x: x['score'], reverse=True)
    
    # Add rank
    for i, item in enumerate(scored_bets, 1):
        item['rank'] = i
    
    return scored_bets

def load_today_bets():
    """Load today's active bets"""
    try:
        with open(WORKSPACE / 'active_bets.json', 'r') as f:
            data = json.load(f)
            return data.get('bets', [])
    except Exception as e:
        print(f"Error loading active_bets.json: {e}")
        return []

def save_ranked_bets(ranked_bets, performance, win_rates):
    """Save ranked bets to file for dashboard consumption
    
    🔧 CORRECTED: Rank purely by LARLScore formula without artificial balancing
    This allows the formula to properly prioritize high-confidence, high-win-rate bets
    """
    
    adaptive_weights = load_adaptive_weights()
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'larlescore_version': '3.0',
        'larlescore_formula': 'LARLScore = (confidence/100) × edge × (historical_win_rate / 0.5) × ADAPTIVE_WEIGHT',
        'adaptive_weights': adaptive_weights,
        'performance_stats': {
            'by_type': {
                bet_type: {
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'win_rate': win_rates.get(bet_type, 0.5),
                    'win_rate_percent': f"{win_rates.get(bet_type, 0.5)*100:.1f}%",
                    'adaptive_weight': adaptive_weights.get(bet_type, {}).get('weight', 1.0)
                }
                for bet_type, stats in performance.items()
            }
        },
        'top_10': [],
        'rest': [],
        'selection_method': 'adaptive_larlescore_ranking_with_learning'
    }
    
    # Build top 10 based purely on LARLScore
    for item in ranked_bets[:10]:
        bet_data = {
            'rank': item['rank'],
            'score': round(item['score'], 4),
            'game': item['bet'].get('game'),
            'bet_type': item['bet'].get('bet_type'),
            'recommendation': item['bet'].get('recommendation'),
            'confidence': item['bet'].get('confidence'),
            'edge': item['bet'].get('edge'),
            'risk_tier': item['bet'].get('risk_tier'),
            'game_time': item['bet'].get('game_time'),
            'reason': item['bet'].get('reason'),
            'full_bet': item['bet']
        }
        output['top_10'].append(bet_data)
    
    # Add rest
    for item in ranked_bets[10:]:
        bet_data = {
            'rank': item['rank'],
            'score': round(item['score'], 4),
            'game': item['bet'].get('game'),
            'bet_type': item['bet'].get('bet_type'),
            'recommendation': item['bet'].get('recommendation'),
            'confidence': item['bet'].get('confidence'),
            'edge': item['bet'].get('edge'),
            'risk_tier': item['bet'].get('risk_tier'),
            'game_time': item['bet'].get('game_time'),
            'reason': item['bet'].get('reason'),
            'full_bet': item['bet']
        }
        output['rest'].append(bet_data)
    
    # Save to file
    with open(WORKSPACE / 'betting/data/ranked_bets.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    return output

def print_rankings(ranked_bets, win_rates, performance):
    """Print rankings to console"""
    print("\n" + "="*80)
    print("🎯 BET RANKING SYSTEM - LARLESCORE v2.0")
    print("="*80)
    
    print("\n📋 CORRECTED FORMULA:")
    print("   LARLScore = (confidence/100) × edge × (historical_win_rate / 0.5)")
    print("   This formula properly weights:")
    print("   ✓ Confidence in the pick (0-100%)")
    print("   ✓ Edge identified vs. market (points or %)")
    print("   ✓ Historical success rate of this bet type")
    
    print("\n📊 HISTORICAL PERFORMANCE BY BET TYPE:")
    for bet_type, stats in performance.items():
        total = stats['wins'] + stats['losses']
        rate = win_rates.get(bet_type, 0.5)
        rate_pct = rate * 100
        print(f"  {bet_type:12} | W: {stats['wins']:2}  L: {stats['losses']:2}  | Win Rate: {rate_pct:.1f}% ({stats['wins']}-{stats['losses']})")
    
    print("\n🎯 TOP 10 BETS (Ranked by Corrected LARLScore):")
    for item in ranked_bets[:10]:
        bet = item['bet']
        bet_type = bet.get('bet_type', 'UNKNOWN')
        win_rate = win_rates.get(bet_type, 0.5) * 100
        print(f"\n  #{item['rank']} [LARLScore: {item['score']:.4f}] {bet.get('game')}")
        print(f"       Type: {bet_type:12} | Confidence: {bet.get('confidence')}% | Edge: {bet.get('edge'):.1f}pt | Win Rate: {win_rate:.1f}%")
        print(f"       Bet: {bet.get('recommendation')}")
    
    remaining = len(ranked_bets) - 10
    if remaining > 0:
        print(f"\n  ... and {remaining} more bets ranked #{11}-{len(ranked_bets)}")
    
    print("\n" + "="*80)

def main():
    """Main execution"""
    print("[*] Loading completed bets...")
    completed_bets = load_completed_bets()
    print(f"    Loaded {len(completed_bets)} completed bets")
    
    print("[*] Calculating performance by bet type...")
    win_rates, performance = calculate_bet_type_performance(completed_bets)
    
    print("[*] Loading today's bets...")
    today_bets = load_today_bets()
    print(f"    Loaded {len(today_bets)} active bets")
    
    print("[*] Ranking bets by expected value...")
    ranked_bets = rank_today_bets(today_bets, win_rates)
    
    print("[*] Saving ranked bets...")
    output = save_ranked_bets(ranked_bets, performance, win_rates)
    
    print_rankings(ranked_bets, win_rates, performance)
    
    print(f"\n✅ Ranked bets saved to ranked_bets.json")
    print(f"   Top 10: {len(output['top_10'])} bets")
    print(f"   Rest:   {len(output['rest'])} bets")
    print(f"   Total:  {len(ranked_bets)} bets")

if __name__ == '__main__':
    main()
