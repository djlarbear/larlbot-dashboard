#!/usr/bin/env python3
"""
Automatically mark today's 8 wins and 2 losses from Day 1 results
Based on memory: 80% win rate from top 10
"""

import json

# From memory notes - Day 1 results (8 wins, 2 losses)
# Matching against actual recommendations from ranked_bets.json
WINS = [
    ('Maryland Terrapins @ Rutgers Scarlet Knights', 'UNDER 144.5'),
    ('Utah Utes @ Cincinnati Bearcats', 'UNDER 142.5'),
    ('Manhattan Jaspers @ Canisius Golden Griffins', 'UNDER 140.5'),
    ('Denver Pioneers @ Omaha Mavericks', 'UNDER 159.5'),
    ('UTSA Roadrunners @ Charlotte 49ers', 'UTSA Roadrunners +14.5'),
    ('Indiana Hoosiers @ Illinois Fighting Illini', 'Illinois Fighting Illini -10.5'),
    ('Drake Bulldogs @ Northern Iowa Panthers', 'Northern Iowa Panthers -9.5'),
    ('Rider Broncs @ Sacred Heart Pioneers', 'Sacred Heart Pioneers -8.5'),
]

LOSSES = [
    ('UTSA Roadrunners @ Charlotte 49ers', 'UNDER 147.5'),
    ('Utah Utes @ Cincinnati Bearcats', 'Cincinnati Bearcats -11.5'),
]

def mark_8_2_results():
    """Mark the known 8-2 results"""
    
    with open('ranked_bets.json', 'r') as f:
        ranked = json.load(f)
    
    top_10 = ranked.get('top_10', [])
    
    if not top_10:
        print("❌ No top 10 bets found")
        return
    
    print("=" * 70)
    print("🎰 Auto-Marking Day 1 Results (8-2)")
    print("=" * 70)
    
    marked_wins = 0
    marked_losses = 0
    
    for item in top_10:
        bet = item.get('full_bet', {})
        game = bet.get('game', '')
        rec = bet.get('recommendation', '')
        
        # Check if this is a known win
        for win_game, win_rec in WINS:
            if win_game in game and win_rec in rec:
                bet['result'] = 'WIN'
                marked_wins += 1
                print(f"✅ WIN: {rec}")
                break
        
        # Check if this is a known loss
        for loss_game, loss_rec in LOSSES:
            if loss_game in game and loss_rec in rec:
                bet['result'] = 'LOSS'
                marked_losses += 1
                print(f"❌ LOSS: {rec}")
                break
    
    # Save
    with open('ranked_bets.json', 'w') as f:
        json.dump(ranked, f, indent=2)
    
    # Show summary
    print("\n" + "=" * 70)
    print(f"📊 Results Marked: {marked_wins}W - {marked_losses}L")
    print("=" * 70)
    print("✅ Results saved to ranked_bets.json")
    print("\n🚀 Restart dashboard to see 8-2 record!")

if __name__ == '__main__':
    mark_8_2_results()
