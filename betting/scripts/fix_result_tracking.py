#!/usr/bin/env python3
"""
SWORD Result Tracking Fix - Properly track wins/losses from ESPN data
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

def aggregate_stats():
    """Aggregate win/loss stats across all completed_bets files"""
    
    workspace = Path('/Users/macmini/.openclaw/workspace')
    
    total_wins = 0
    total_losses = 0
    total_bets = 0
    
    by_type = {'SPREAD': {'W': 0, 'L': 0}, 'TOTAL': {'W': 0, 'L': 0}, 'MONEYLINE': {'W': 0, 'L': 0}}
    
    # Scan all completed_bets files
    for f in sorted(workspace.glob('completed_bets_*.json')):
        try:
            with open(f) as fp:
                data = json.load(fp)
            
            for bet in data.get('bets', []):
                result = bet.get('result', '').upper()
                bet_type = bet.get('bet_type', 'UNKNOWN')
                
                if result in ['WIN', 'LOSS']:
                    total_bets += 1
                    if result == 'WIN':
                        total_wins += 1
                        if bet_type in by_type:
                            by_type[bet_type]['W'] += 1
                    else:
                        total_losses += 1
                        if bet_type in by_type:
                            by_type[bet_type]['L'] += 1
        except Exception as e:
            print(f"Error reading {f}: {e}")
    
    # Calculate win rate
    win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
    
    # Create stats file for dashboard
    stats = {
        "as_of": datetime.now().isoformat(),
        "overall": {
            "total_bets": total_bets,
            "wins": total_wins,
            "losses": total_losses,
            "win_rate": round(win_rate, 1)
        },
        "by_type": {
            "SPREAD": {
                "total": by_type['SPREAD']['W'] + by_type['SPREAD']['L'],
                "wins": by_type['SPREAD']['W'],
                "losses": by_type['SPREAD']['L'],
                "win_rate": round(by_type['SPREAD']['W'] / (by_type['SPREAD']['W'] + by_type['SPREAD']['L']) * 100, 1) if (by_type['SPREAD']['W'] + by_type['SPREAD']['L']) > 0 else 0
            },
            "TOTAL": {
                "total": by_type['TOTAL']['W'] + by_type['TOTAL']['L'],
                "wins": by_type['TOTAL']['W'],
                "losses": by_type['TOTAL']['L'],
                "win_rate": round(by_type['TOTAL']['W'] / (by_type['TOTAL']['W'] + by_type['TOTAL']['L']) * 100, 1) if (by_type['TOTAL']['W'] + by_type['TOTAL']['L']) > 0 else 0
            },
            "MONEYLINE": {
                "total": by_type['MONEYLINE']['W'] + by_type['MONEYLINE']['L'],
                "wins": by_type['MONEYLINE']['W'],
                "losses": by_type['MONEYLINE']['L'],
                "win_rate": round(by_type['MONEYLINE']['W'] / (by_type['MONEYLINE']['W'] + by_type['MONEYLINE']['L']) * 100, 1) if (by_type['MONEYLINE']['W'] + by_type['MONEYLINE']['L']) > 0 else 0
            }
        }
    }
    
    # Save stats
    with open(workspace / 'bet_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("=" * 70)
    print("SWORD BETTING STATISTICS - UPDATED")
    print("=" * 70)
    print(f"\n📊 OVERALL")
    print(f"  Total Bets: {total_bets}")
    print(f"  Wins: {total_wins} ({win_rate:.1f}%)")
    print(f"  Losses: {total_losses}")
    
    print(f"\n🎯 BY BET TYPE")
    for btype in ['SPREAD', 'TOTAL', 'MONEYLINE']:
        s = stats['by_type'][btype]
        if s['total'] > 0:
            print(f"  {btype}: {s['wins']}-{s['losses']} ({s['win_rate']:.1f}%)")
    
    return stats

if __name__ == '__main__':
    stats = aggregate_stats()
