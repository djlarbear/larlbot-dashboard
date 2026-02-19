#!/usr/bin/env python3
"""
Mark today's top 10 bets with WIN/LOSS results
Usage: python3 mark_todays_results.py
"""

import json

def mark_results():
    """Interactively mark bet results"""
    
    with open('ranked_bets.json', 'r') as f:
        ranked = json.load(f)
    
    top_10 = ranked.get('top_10', [])
    
    if not top_10:
        print("❌ No top 10 bets found")
        return
    
    print("=" * 70)
    print("🎰 Mark Today's Bet Results")
    print("=" * 70)
    
    for i, item in enumerate(top_10):
        bet = item.get('full_bet', {})
        current_result = bet.get('result', 'NOT MARKED')
        
        print(f"\n#{i+1} {bet.get('recommendation', 'BET')}")
        print(f"    Game: {bet.get('game', 'N/A')}")
        print(    f"    Current: {current_result}")
        print(f"    Edge: {bet.get('edge', 0)}pt | Conf: {bet.get('confidence', 0)}%")
        
        # Ask for result
        while True:
            result = input(f"    Mark as [W]in/[L]oss/[S]kip? ").strip().upper()
            if result in ['W', 'L', 'S']:
                break
            print("    ❌ Invalid. Enter W, L, or S")
        
        if result == 'W':
            item['full_bet']['result'] = 'WIN'
            print("    ✅ Marked as WIN")
        elif result == 'L':
            item['full_bet']['result'] = 'LOSS'
            print("    ✅ Marked as LOSS")
        else:
            print("    ⏭️  Skipped")
    
    # Save
    with open('ranked_bets.json', 'w') as f:
        json.dump(ranked, f, indent=2)
    
    # Show summary
    wins = sum(1 for item in top_10 if item.get('full_bet', {}).get('result') == 'WIN')
    losses = sum(1 for item in top_10 if item.get('full_bet', {}).get('result') == 'LOSS')
    
    print("\n" + "=" * 70)
    print(f"📊 Summary: {wins}W - {losses}L ({len(top_10)} total)")
    if wins + losses > 0:
        wr = int((wins / (wins + losses) * 100))
        print(f"📈 Win Rate: {wr}%")
    print("=" * 70)
    print("✅ Results saved to ranked_bets.json")

if __name__ == '__main__':
    mark_results()
