#!/usr/bin/env python3
"""
Automated Bet Tracking and Results Update System
Monitors games and updates bet outcomes automatically
"""

import json
import sqlite3
from datetime import datetime, date

def get_completed_games():
    """Get today's completed games from database"""
    conn = sqlite3.connect('sports_betting.db')
    query = """
        SELECT id, sport, date, home_team, away_team, home_score, away_score, status
        FROM games 
        WHERE date >= date('now', '-1 day')
        AND status = 'Final'
        AND home_score IS NOT NULL
        AND away_score IS NOT NULL
        ORDER BY date DESC
    """
    cursor = conn.cursor()
    cursor.execute(query)
    games = cursor.fetchall()
    conn.close()
    
    completed = []
    for game in games:
        game_id, sport, date_str, home_team, away_team, home_score, away_score, status = game
        completed.append({
            'id': game_id,
            'sport': sport,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'final_score': f"{away_score}-{home_score}",
            'total': home_score + away_score,
            'margin': home_score - away_score,
            'date': date_str.split('T')[0]
        })
    
    return completed

def load_bet_tracker():
    """Load bet tracker JSON"""
    try:
        with open('bet_tracker_input.json', 'r') as f:
            return json.load(f)
    except:
        return {'instructions': 'Manual bet tracking', 'bets': []}

def save_bet_tracker(data):
    """Save bet tracker JSON"""
    with open('bet_tracker_input.json', 'w') as f:
        json.dump(data, f, indent=2)

def check_and_update_bets():
    """Check pending bets against completed games and update results"""
    tracker = load_bet_tracker()
    completed_games = get_completed_games()
    
    updated = False
    
    for bet in tracker['bets']:
        # Skip already completed bets
        if bet.get('result') != 'PENDING':
            continue
        
        # Find matching game
        for game in completed_games:
            game_match = (
                (bet['game'] in f"{game['away_team']} @ {game['home_team']}") or
                (f"{game['away_team']} @ {game['home_team']}" in bet['game'])
            )
            
            if not game_match:
                continue
            
            print(f"✅ Found completed game: {bet['game']}")
            
            # Update bet based on type
            if bet['bet_type'] == 'UNDER':
                actual_total = game['total']
                line = bet['line']
                
                if actual_total < line:
                    result = 'WIN'
                    profit = 100  # Standard -110 payout
                elif actual_total > line:
                    result = 'LOSS'
                    profit = -110
                else:
                    result = 'PUSH'
                    profit = 0
                
                bet['actual_total'] = actual_total
                bet['result'] = result
                bet['profit'] = profit
                bet['final_score'] = game['final_score']
                bet['bet_result'] = f"Under {line}"
                
                print(f"   {result}: {actual_total} vs {line} (Profit: ${profit:+d})")
                updated = True
                
            elif bet['bet_type'] == 'OVER':
                actual_total = game['total']
                line = bet['line']
                
                if actual_total > line:
                    result = 'WIN'
                    profit = 100
                elif actual_total < line:
                    result = 'LOSS'
                    profit = -110
                else:
                    result = 'PUSH'
                    profit = 0
                
                bet['actual_total'] = actual_total
                bet['result'] = result
                bet['profit'] = profit
                bet['final_score'] = game['final_score']
                bet['bet_result'] = f"Over {line}"
                
                print(f"   {result}: {actual_total} vs {line} (Profit: ${profit:+d})")
                updated = True
                
            elif bet['bet_type'] == 'SPREAD':
                actual_margin = game['margin']
                team = bet.get('team', '')
                line = bet['line']
                
                # Determine if betting on home or away
                if team in game['home_team']:
                    # Bet on home team
                    if actual_margin > line:
                        result = 'WIN'
                        profit = 100
                    elif actual_margin < line:
                        result = 'LOSS'
                        profit = -110
                    else:
                        result = 'PUSH'
                        profit = 0
                else:
                    # Bet on away team (reverse margin)
                    if -actual_margin > line:
                        result = 'WIN'
                        profit = 100
                    elif -actual_margin < line:
                        result = 'LOSS'
                        profit = -110
                    else:
                        result = 'PUSH'
                        profit = 0
                
                bet['actual_margin'] = actual_margin
                bet['result'] = result
                bet['profit'] = profit
                bet['final_score'] = game['final_score']
                
                print(f"   {result}: {actual_margin} vs {line} (Profit: ${profit:+d})")
                updated = True
    
    if updated:
        save_bet_tracker(tracker)
        print(f"\n✅ Updated bet tracker!")
        return True
    else:
        print("📊 No pending bets to update")
        return False

if __name__ == "__main__":
    print("🎰 LarlBot Automated Bet Tracker")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    check_and_update_bets()
