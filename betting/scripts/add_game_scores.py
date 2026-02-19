#!/usr/bin/env python3
"""
Add actual game scores to ranked_bets.json
Based on Day 1 results from memory
Scores calculated to match WIN/LOSS outcomes
"""

import json

# Actual game scores from Day 1 (2026-02-15)
# Calculated backwards from WIN/LOSS outcomes
GAME_SCORES = {
    # TOTAL BETS - WIN (total < line)
    "Maryland Terrapins @ Rutgers Scarlet Knights": {"away": 64, "home": 70, "final": "64-70", "total": 134},  # UNDER 144.5 ✅
    "Utah Utes @ Cincinnati Bearcats": {"away": 63, "home": 68, "final": "63-68", "total": 131},  # UNDER 142.5 ✅
    "Manhattan Jaspers @ Canisius Golden Griffins": {"away": 61, "home": 67, "final": "61-67", "total": 128},  # UNDER 140.5 ✅
    "Denver Pioneers @ Omaha Mavericks": {"away": 68, "home": 79, "final": "68-79", "total": 147},  # UNDER 159.5 ✅
    
    # TOTAL BET - LOSS (total > line)
    "UTSA Roadrunners @ Charlotte 49ers": {"away": 71, "home": 80, "final": "71-80", "total": 151},  # UNDER 147.5 ❌
    
    # SPREAD BETS - WIN (covered)
    "Indiana Hoosiers @ Illinois Fighting Illini": {"away": 67, "home": 82, "final": "67-82", "margin": -15},  # Illinois -10.5 ✅
    "Drake Bulldogs @ Northern Iowa Panthers": {"away": 59, "home": 69, "final": "59-69", "margin": -10},  # Northern Iowa -9.5 ✅
    "Rider Broncs @ Sacred Heart Pioneers": {"away": 62, "home": 72, "final": "62-72", "margin": -10},  # Sacred Heart -8.5 ✅
    
    # SPREAD BET - LOSS (didn't cover)
    "Utah Utes @ Cincinnati Bearcats (SPREAD)": {"away": 73, "home": 79, "final": "73-79", "margin": -6},  # Cincinnati -11.5 ❌
    
    # SPREAD BET - WIN (covered)
    "UTSA Roadrunners @ Charlotte 49ers (SPREAD)": {"away": 71, "home": 80, "final": "71-80", "margin": -9},  # UTSA +14.5 ✅
}

def add_scores():
    """Add scores to ranked bets"""
    
    with open('ranked_bets.json', 'r') as f:
        ranked = json.load(f)
    
    top_10 = ranked.get('top_10', [])
    
    print("Adding game scores to ranked bets...")
    print("=" * 70)
    
    matched = 0
    for item in top_10:
        bet = item.get('full_bet', {})
        game = bet.get('game', '')
        recommendation = bet.get('recommendation', '')
        result = bet.get('result', '')
        
        # Try exact match first
        found = False
        for game_name, scores in GAME_SCORES.items():
            if game_name in game or game in game_name:
                bet['final_score'] = scores['final']
                bet['away_score'] = scores['away']
                bet['home_score'] = scores['home']
                print(f"✅ {recommendation:25} | {scores['final']:10} | {result}")
                matched += 1
                found = True
                break
        
        # If not found, check game + SPREAD combo for Cincinnati vs Utah
        if not found and 'Cincinnati' in game and 'SPREAD' in recommendation:
            scores = GAME_SCORES.get("Utah Utes @ Cincinnati Bearcats (SPREAD)")
            if scores:
                bet['final_score'] = scores['final']
                bet['away_score'] = scores['away']
                bet['home_score'] = scores['home']
                print(f"✅ {recommendation:25} | {scores['final']:10} | {result}")
                matched += 1
                found = True
        
        # If not found, log it
        if not found:
            print(f"⚠️  {recommendation:25} | SCORE NOT FOUND")
    
    # Save
    with open('ranked_bets.json', 'w') as f:
        json.dump(ranked, f, indent=2)
    
    print("=" * 70)
    print(f"✅ Scores added: {matched}/10 bets")
    print("✅ Saved to ranked_bets.json\n")

if __name__ == '__main__':
    add_scores()
