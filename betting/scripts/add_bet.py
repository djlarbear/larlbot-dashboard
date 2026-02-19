#!/usr/bin/env python3
"""
Quick script to add a new bet to the tracker
Usage: python3 add_bet.py
"""

import json
from datetime import date

def add_bet():
    """Interactive bet entry"""
    print("🎰 Add New Bet to Tracker\n")
    
    # Load existing tracker
    try:
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
    except:
        tracker = {'instructions': 'Manual bet tracking', 'bets': []}
    
    # Get bet details
    print("Enter bet details:")
    game = input("Game (e.g., 'Pittsburgh @ North Carolina'): ").strip()
    bet_type = input("Bet type (UNDER/OVER/SPREAD/MONEYLINE): ").strip().upper()
    
    bet = {
        'date': date.today().strftime('%Y-%m-%d'),
        'game': game,
        'sport': 'NCAA Basketball',
        'bet_type': bet_type,
        'stake': 110,
        'result': 'PENDING',
        'profit': 0
    }
    
    if bet_type in ['UNDER', 'OVER']:
        line = float(input(f"Line (e.g., 144.5): ").strip())
        bet['line'] = line
        bet['actual_total'] = None
        bet['bet_result'] = f"{bet_type.title()} {line}"
        
    elif bet_type == 'SPREAD':
        team = input("Team you're betting on: ").strip()
        line = float(input(f"Spread (e.g., +10.5 or -3.5): ").strip())
        bet['team'] = team
        bet['line'] = line
        bet['actual_margin'] = None
        bet['bet_placed'] = f"{team} {line:+.1f}"
        
    elif bet_type == 'MONEYLINE':
        team = input("Team you're betting on: ").strip()
        odds = int(input("Odds (e.g., -110 or +150): ").strip())
        bet['team'] = team
        bet['odds'] = odds
    
    # Add notes
    notes = input("Notes (optional): ").strip()
    if notes:
        bet['notes'] = notes
    
    # Add to tracker
    tracker['bets'].append(bet)
    
    # Save
    with open('bet_tracker_input.json', 'w') as f:
        json.dump(tracker, f, indent=2)
    
    print(f"\n✅ Added bet: {game} - {bet_type}")
    print(f"📊 Total bets tracked: {len(tracker['bets'])}")
    print("\nRun 'git add bet_tracker_input.json && git commit -m \"Add bet\" && git push' to update dashboard!")

if __name__ == "__main__":
    add_bet()
