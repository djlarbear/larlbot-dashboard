#!/usr/bin/env python3
"""
Live Game Tracker - Sends Telegram updates at quarter/half marks
Shows bet performance in real-time
"""

import json
import sqlite3
from datetime import datetime, date
import subprocess
import time

    """Send message via Telegram using OpenClaw message tool"""
    try:
        # Use OpenClaw's message command
        result = subprocess.run(
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Sent Telegram update")
            return True
        else:
            print(f"⚠️  Telegram send failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  Error sending Telegram: {e}")
        return False

def get_todays_pending_bets():
    """Get today's tracked bets that are still pending"""
    try:
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
        
        today = date.today().strftime('%Y-%m-%d')
        pending = [b for b in tracker.get('bets', []) 
                   if b.get('date') == today and b.get('result') == 'PENDING']
        
        return pending
    except:
        return []

def get_game_status(game_name):
    """Get current game status from ESPN database"""
    conn = sqlite3.connect('sports_betting.db')
    cursor = conn.cursor()
    
    # Try to match game by team names
    parts = game_name.split('@')
    if len(parts) != 2:
        conn.close()
        return None
    
    away_team = parts[0].strip()
    home_team = parts[1].strip()
    
    # Fuzzy match on team names
    query = """
        SELECT home_team, away_team, home_score, away_score, status, date
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
            'home_score': result[2],
            'away_score': result[3],
            'status': result[4],
            'total': (result[2] or 0) + (result[3] or 0),
            'margin': (result[2] or 0) - (result[3] or 0)
        }
    
    return None

def format_bet_status(bet, game):
    """Format bet status message"""
    if not game or game['status'] != 'In Progress':
        return None
    
    home = game['home_score'] or 0
    away = game['away_score'] or 0
    total = home + away
    margin = home - away
    
    msg = f"🏀 *{bet['game']}*\n"
    msg += f"📊 Score: {game['away_team']} {away} - {home} {game['home_team']}\n"
    msg += f"📈 Total: {total}\n\n"
    msg += f"🎯 *Your Bet:* {bet['recommendation']}\n"
    
    # Calculate current status
    if bet['bet_type'] == 'UNDER':
        line = bet['line']
        diff = total - line
        if diff < 0:
            msg += f"✅ Tracking UNDER {line} (Currently {diff:+.1f})\n"
        else:
            msg += f"⚠️ Tracking UNDER {line} (Currently {diff:+.1f})\n"
    
    elif bet['bet_type'] == 'OVER':
        line = bet['line']
        diff = total - line
        if diff > 0:
            msg += f"✅ Tracking OVER {line} (Currently {diff:+.1f})\n"
        else:
            msg += f"⚠️ Tracking OVER {line} (Currently {diff:+.1f})\n"
    
    elif bet['bet_type'] == 'SPREAD':
        team = bet.get('team', '')
        line = bet['line']
        
        # Determine if betting on home or away
        if team in game['home_team']:
            actual_margin = margin
            diff = actual_margin - line
            if diff > 0:
                msg += f"✅ {team} {line:+.1f} (Currently {actual_margin:+.1f}, diff: {diff:+.1f})\n"
            else:
                msg += f"⚠️ {team} {line:+.1f} (Currently {actual_margin:+.1f}, diff: {diff:+.1f})\n"
        else:
            actual_margin = -margin
            diff = actual_margin - line
            if diff > 0:
                msg += f"✅ {team} {line:+.1f} (Currently {actual_margin:+.1f}, diff: {diff:+.1f})\n"
            else:
                msg += f"⚠️ {team} {line:+.1f} (Currently {actual_margin:+.1f}, diff: {diff:+.1f})\n"
    
    msg += f"\nConfidence: {bet['confidence']}%"
    
    return msg

def check_and_notify():
    """Check games and send updates if at quarter/half marks"""
    print(f"🎰 Live Game Tracker")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    pending_bets = get_todays_pending_bets()
    
    if not pending_bets:
        print("📊 No pending bets to track")
        return
    
    print(f"📊 Tracking {len(pending_bets)} pending bet{'s' if len(pending_bets) != 1 else ''}\n")
    
    updates_sent = 0
    
    for bet in pending_bets:
        game = get_game_status(bet['game'])
        
        if game and game['status'] == 'In Progress':
            print(f"🏀 {bet['game']}: {game['away_score']}-{game['home_score']} (In Progress)")
            
            msg = format_bet_status(bet, game)
            if msg:
                # Send update
                    updates_sent += 1
                
                # Small delay between messages
                time.sleep(2)
        else:
            status = game['status'] if game else 'Not Started'
            print(f"⏳ {bet['game']}: {status}")
    
    if updates_sent > 0:
        print(f"\n✅ Sent {updates_sent} update{'s' if updates_sent != 1 else ''}")
    else:
        print(f"\n📊 No live games to report")

if __name__ == "__main__":
    check_and_notify()
