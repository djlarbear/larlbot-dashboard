#!/usr/bin/env python3
"""
On-Demand Betting Update
Triggered when user sends a message asking for an update
"""

import json
import sqlite3
import subprocess
from datetime import date

    """Send message via Telegram"""
    try:
        result = subprocess.run(
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_todays_bets():
    """Get today's recommended bets"""
    try:
        from daily_recommendations import get_todays_value_bets
        return get_todays_value_bets()
    except:
        return []

def get_todays_tracked_bets():
    """Get today's tracked bets with results"""
    try:
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
        
        today = date.today().strftime('%Y-%m-%d')
        return [b for b in tracker.get('bets', []) if b.get('date') == today]
    except:
        return []

def get_game_status(game_name):
    """Get current game status"""
    conn = sqlite3.connect('sports_betting.db')
    cursor = conn.cursor()
    
    parts = game_name.split('@')
    if len(parts) != 2:
        conn.close()
        return None
    
    away_team = parts[0].strip()
    home_team = parts[1].strip()
    
    query = """
        SELECT home_team, away_team, home_score, away_score, status
        FROM games 
        WHERE date >= date('now')
        AND (
            (home_team LIKE ? OR away_team LIKE ?)
            OR (home_team LIKE ? OR away_team LIKE ?)
        )
        ORDER BY date
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
            'home_team': result[0],
            'away_team': result[1],
            'home_score': result[2] or 0,
            'away_score': result[3] or 0,
            'status': result[4],
            'total': (result[2] or 0) + (result[3] or 0),
            'margin': (result[2] or 0) - (result[3] or 0)
        }
    
    return None

def format_status_update():
    """Create comprehensive status update"""
    today = date.today().strftime('%A, %B %d')
    
    msg = f"🎰 *LarlBot Status Update*\n"
    msg += f"📅 {today}\n\n"
    
    # Get today's recommendations
    recs = get_todays_bets()
    tracked = get_todays_tracked_bets()
    
    if not recs and not tracked:
        msg += "No bets for today.\n"
        msg += "Dashboard: https://web-production-a39703.up.railway.app/"
        return msg
    
    # Check each bet's status
    pending = []
    in_progress = []
    completed = []
    
    for bet in tracked:
        game = get_game_status(bet['game'])
        
        if not game:
            pending.append(bet)
        elif game['status'] == 'Final':
            completed.append((bet, game))
        elif game['status'] == 'In Progress':
            in_progress.append((bet, game))
        else:
            pending.append(bet)
    
    # Pending games
    if pending:
        msg += f"⏳ *Pending ({len(pending)}):*\n"
        for bet in pending:
            msg += f"• {bet['recommendation']}\n"
        msg += "\n"
    
    # Live games
    if in_progress:
        msg += f"🔴 *Live ({len(in_progress)}):*\n"
        for bet, game in in_progress:
            msg += f"• {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']}\n"
            msg += f"  Bet: {bet['recommendation']}\n"
        msg += "\n"
    
    # Completed games
    if completed:
        msg += f"✅ *Completed ({len(completed)}):*\n"
        for bet, game in completed:
            result = bet.get('result', 'PENDING')
            emoji = '✅' if result == 'WIN' else '❌' if result == 'LOSS' else '🔄'
            msg += f"{emoji} {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']}\n"
            msg += f"  Bet: {bet['recommendation']} - *{result}*\n"
        msg += "\n"
    
    # Overall stats
    wins = len([b for b in tracked if b.get('result') == 'WIN'])
    losses = len([b for b in tracked if b.get('result') == 'LOSS'])
    total = wins + losses
    
    if total > 0:
        win_rate = (wins / total) * 100
        msg += f"📊 *Today: {wins}-{losses} ({win_rate:.0f}%)*\n\n"
    
    msg += f"Dashboard: https://web-production-a39703.up.railway.app/"
    
    return msg

def send_update():
    """Send on-demand update"""
    print("🎰 On-Demand Update\n")
    
    msg = format_status_update()
    
        print("✅ Sent update to Telegram")
    else:
        print("❌ Failed to send update")

if __name__ == "__main__":
    send_update()
