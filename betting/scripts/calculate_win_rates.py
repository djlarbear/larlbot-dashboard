#!/usr/bin/env python3
"""
Calculate Historical Win Rates - Run after scores come in
Tracks win rate by bet type and confidence level
Updates daily after NCAA-API scores are loaded
Feeds into next day's LARLScore calculations
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

WORKSPACE = Path("/Users/macmini/.openclaw/workspace")

def calculate_historical_win_rates():
    """
    Load all completed bets and calculate win rates by:
    1. Bet type (SPREAD, TOTAL, MONEYLINE)
    2. Confidence level (50-60, 60-70, 70-80, 80-90, 90%+)
    3. Date (to detect drift over time)
    
    Returns dict with statistics for use in LARLScore calculations
    """
    all_bets = []
    
    # Load all completed_bets files
    for f in sorted(WORKSPACE.glob("completed_bets_*.json")):
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                if isinstance(data, dict) and 'bets' in data:
                    all_bets.extend(data['bets'])
                elif isinstance(data, list):
                    all_bets.extend(data)
        except Exception as e:
            print(f"Warning: Error loading {f}: {e}")
    
    # Initialize result structure
    results = {
        'by_type': {},
        'by_confidence': {},
        'by_date': {},
        'overall_stats': {
            'total_bets': 0,
            'total_wins': 0,
            'total_losses': 0,
            'overall_win_rate': 0
        },
        'timestamp': datetime.now().isoformat(),
        'notes': 'Used in LARLScore formula: (confidence/100) × edge × (win_rate / 0.5)'
    }
    
    # Calculate by bet type
    for bet_type in ['SPREAD', 'TOTAL', 'MONEYLINE']:
        type_bets = [b for b in all_bets 
                     if b.get('bet_type', '').upper() == bet_type 
                     and b.get('result', '').upper() in ['WIN', 'LOSS']]
        
        if type_bets:
            wins = len([b for b in type_bets if b['result'].upper() == 'WIN'])
            losses = len([b for b in type_bets if b['result'].upper() == 'LOSS'])
            total = wins + losses
            win_rate = wins / total if total > 0 else 0.5
            
            results['by_type'][bet_type] = {
                'wins': wins,
                'losses': losses,
                'total': total,
                'win_rate': round(win_rate, 4),
                'win_rate_percent': f"{win_rate*100:.1f}%",
                'win_loss_string': f"{wins}-{losses}"
            }
        else:
            results['by_type'][bet_type] = {
                'wins': 0,
                'losses': 0,
                'total': 0,
                'win_rate': 0.5,  # Default neutral
                'win_rate_percent': '50.0%',
                'win_loss_string': '0-0',
                'note': 'No data - using neutral 50% default'
            }
    
    # Calculate by confidence level
    confidence_bins = [
        ('50-60%', 50, 61),
        ('60-70%', 60, 71),
        ('70-80%', 70, 81),
        ('80-90%', 80, 91),
        ('90%+', 90, 101)
    ]
    
    for label, min_conf, max_conf in confidence_bins:
        conf_bets = [b for b in all_bets 
                     if min_conf <= b.get('confidence', 50) < max_conf
                     and b.get('result', '').upper() in ['WIN', 'LOSS']]
        
        if conf_bets:
            wins = len([b for b in conf_bets if b['result'].upper() == 'WIN'])
            losses = len([b for b in conf_bets if b['result'].upper() == 'LOSS'])
            total = wins + losses
            win_rate = wins / total if total > 0 else 0.5
            
            results['by_confidence'][label] = {
                'wins': wins,
                'losses': losses,
                'total': total,
                'win_rate': round(win_rate, 4),
                'win_rate_percent': f"{win_rate*100:.1f}%"
            }
    
    # Calculate by date
    for bet in all_bets:
        if 'result' not in bet or bet['result'].upper() not in ['WIN', 'LOSS']:
            continue
        
        # Try to extract date from game_time or use current date
        date_key = 'unknown'
        if 'game_time' in bet:
            # Most game times are like "07:00 PM EST"
            # We'll use the file date instead
            date_key = 'current'  # Simplified for now
        
        if date_key not in results['by_date']:
            results['by_date'][date_key] = defaultdict(lambda: {'wins': 0, 'losses': 0})
        
        bet_type = bet.get('bet_type', 'UNKNOWN').upper()
        if bet['result'].upper() == 'WIN':
            results['by_date'][date_key][bet_type]['wins'] += 1
        else:
            results['by_date'][date_key][bet_type]['losses'] += 1
    
    # Calculate overall stats
    total_wins = sum(v['wins'] for v in results['by_type'].values())
    total_losses = sum(v['losses'] for v in results['by_type'].values())
    total = total_wins + total_losses
    
    results['overall_stats']['total_bets'] = total
    results['overall_stats']['total_wins'] = total_wins
    results['overall_stats']['total_losses'] = total_losses
    results['overall_stats']['overall_win_rate'] = round(total_wins / total, 4) if total > 0 else 0.5
    results['overall_stats']['overall_win_rate_percent'] = f"{(total_wins/total*100):.1f}%" if total > 0 else "50.0%"
    
    return results

def save_win_rates(results):
    """Save calculated win rates to file"""
    output_file = WORKSPACE / "historical_win_rates.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return output_file

def print_win_rates(results):
    """Print win rates to console"""
    print("\n" + "="*80)
    print("📊 HISTORICAL WIN RATE ANALYSIS")
    print("="*80)
    
    print("\n📈 BY BET TYPE:")
    for bet_type, stats in results['by_type'].items():
        if stats['total'] > 0:
            print(f"  {bet_type:12} | {stats['win_loss_string']:5} | Win Rate: {stats['win_rate_percent']:6} ({stats['win_rate']:.4f})")
    
    print("\n📊 BY CONFIDENCE LEVEL:")
    for conf_range, stats in results['by_confidence'].items():
        if stats['total'] > 0:
            print(f"  {conf_range:8} | W:{stats['wins']:2}  L:{stats['losses']:2}  | Win Rate: {stats['win_rate_percent']:6}")
    
    print("\n📌 OVERALL STATISTICS:")
    overall = results['overall_stats']
    print(f"  Total Bets: {overall['total_bets']}")
    print(f"  Total Wins: {overall['total_wins']}")
    print(f"  Total Losses: {overall['total_losses']}")
    print(f"  Overall Win Rate: {overall['overall_win_rate_percent']} ({overall['overall_win_rate']:.4f})")
    
    print("\n" + "="*80)

def main():
    """Main execution"""
    print("[*] Calculating historical win rates...")
    results = calculate_historical_win_rates()
    
    print("[*] Saving win rates...")
    output_file = save_win_rates(results)
    print(f"    ✅ Saved to {output_file}")
    
    print_win_rates(results)
    
    print("\n📋 Use these win rates in bet_ranker.py:")
    print("   win_rates = results['by_type']")
    print("   larlescore = (confidence/100) * edge * (win_rates[bet_type] / 0.5)")
    
    return results

if __name__ == '__main__':
    main()
