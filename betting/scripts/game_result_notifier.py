#!/usr/bin/env python3
"""
Game Result Notifier - Send Telegram update when games finish
Checks for newly completed games and sends WIN/LOSS notifications
"""

import json
import sqlite3
import subprocess
from datetime import date
import os

STATE_FILE = 'game_notifier_state.json'

    """Send message via Telegram"""
    try:
        result = subprocess.run(
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error sending Telegram: {e}")
        return False

def load_notified_games():
    """Load list of games we've already notified about"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'notified': []}

def save_notified_game(game_id):
    """Mark game as notified"""
    state = load_notified_games()
    if game_id not in state['notified']:
        state['notified'].append(game_id)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_todays_tracked_bets():
    """Get today's tracked bets"""
    try:
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
        
        today = date.today().strftime('%Y-%m-%d')
        return [b for b in tracker.get('bets', []) if b.get('date') == today]
    except:
        return []

def get_completed_games_for_bet(bet):
    """Get game result if it just finished"""
    conn = sqlite3.connect('sports_betting.db')
    cursor = conn.cursor()
    
    # Parse game name
    parts = bet['game'].split('@')
    if len(parts) != 2:
        conn.close()
        return None
    
    away_team = parts[0].strip()
    home_team = parts[1].strip()
    
    # Find completed game
    query = """
        SELECT id, home_team, away_team, home_score, away_score, status
        FROM games 
        WHERE date >= date('now')
        AND status = 'Final'
        AND (
            (home_team LIKE ? OR away_team LIKE ?)
            OR (home_team LIKE ? OR away_team LIKE ?)
        )
        ORDER BY date DESC
        LIMIT 1
    """
    
    cursor.execute(query, (
        f"%{home_team.split()[0]}%",
        f"%{away_team.split()[0]}%",
        f"%{home_team.split()[-1]}%",
        f"%{away_team.split()[-1]}%"
    ))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'home_team': result[1],
            'away_team': result[2],
            'home_score': result[3],
            'away_score': result[4],
            'status': result[5],
            'total': result[3] + result[4],
            'margin': result[3] - result[4]
        }
    
    return None

def calculate_bet_result(bet, game):
    """Calculate if bet won or lost"""
    home = game['home_score']
    away = game['away_score']
    total = home + away
    margin = home - away
    
    if bet['bet_type'] == 'UNDER':
        line = bet['line']
        if total < line:
            return 'WIN', f"Total: {total} < {line}"
        elif total > line:
            return 'LOSS', f"Total: {total} > {line}"
        else:
            return 'PUSH', f"Total: {total} = {line}"
    
    elif bet['bet_type'] == 'OVER':
        line = bet['line']
        if total > line:
            return 'WIN', f"Total: {total} > {line}"
        elif total < line:
            return 'LOSS', f"Total: {total} < {line}"
        else:
            return 'PUSH', f"Total: {total} = {line}"
    
    elif bet['bet_type'] == 'SPREAD':
        team = bet.get('team', '')
        line = bet['line']
        
        # Determine if betting on home or away
        if team in game['home_team']:
            actual_margin = margin
            if actual_margin > line:
                return 'WIN', f"{team} won by {actual_margin} > {line}"
            elif actual_margin < line:
                return 'LOSS', f"{team} won by {actual_margin} < {line}"
            else:
                return 'PUSH', f"{team} won by {actual_margin} = {line}"
        else:
            actual_margin = -margin
            if actual_margin > line:
                return 'WIN', f"{team} lost by {abs(actual_margin)} < {abs(line)}"
            elif actual_margin < line:
                return 'LOSS', f"{team} lost by {abs(actual_margin)} > {abs(line)}"
            else:
                return 'PUSH', f"{team} lost by {abs(actual_margin)} = {abs(line)}"
    
    return 'UNKNOWN', ''

def format_result_message(bet, game, result, reason):
    """Format game result message"""
    away = game['away_score']
    home = game['home_score']
    
    if result == 'WIN':
        emoji = '✅'
        status = '*WIN!*'
    elif result == 'LOSS':
        emoji = '❌'
        status = '*LOSS*'
    else:
        emoji = '🔄'
        status = '*PUSH*'
    
    msg = f"{emoji} *Game Final*\n\n"
    msg += f"🏀 *{bet['game']}*\n"
    msg += f"📊 Final: {game['away_team']} {away} - {home} {game['home_team']}\n\n"
    msg += f"🎯 *Your Bet:* {bet['recommendation']}\n"
    msg += f"🎲 *Result:* {status}\n"
    msg += f"📈 {reason}\n\n"
    msg += f"Confidence: {bet['confidence']}%"
    
    return msg

def check_and_notify():
    """Check for completed games and notify"""
    print(f"🎰 Game Result Notifier")
    print(f"📅 {date.today().strftime('%Y-%m-%d')}\n")
    
    bets = get_todays_tracked_bets()
    state = load_notified_games()
    
    if not bets:
        print("📊 No bets to track today")
        return
    
    print(f"📊 Checking {len(bets)} bet{'s' if len(bets) != 1 else ''}\n")
    
    notifications = 0
    
    for bet in bets:
        # Skip if already notified
        game_key = f"{bet['date']}_{bet['game']}"
        if game_key in state['notified']:
            continue
        
        game = get_completed_games_for_bet(bet)
        
        if game and game['status'] == 'Final':
            print(f"🏀 {bet['game']}: FINAL - {game['away_score']}-{game['home_score']}")
            
            result, reason = calculate_bet_result(bet, game)
            msg = format_result_message(bet, game, result, reason)
            
                save_notified_game(game_key)
                notifications += 1
                print(f"   ✅ Sent {result} notification")
            else:
                print(f"   ❌ Failed to send notification")
        else:
            status = game['status'] if game else 'Not Started'
            print(f"⏳ {bet['game']}: {status}")
    
    if notifications > 0:
        print(f"\n✅ Sent {notifications} notification{'s' if notifications != 1 else ''}")
    else:
        print(f"\n📊 No new results to report")

if __name__ == "__main__":
    check_and_notify()
