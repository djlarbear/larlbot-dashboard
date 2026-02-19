#!/usr/bin/env python3
"""
Morning Bet Update - Send today's recommended bets via Telegram
"""

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
        print(f"Error sending Telegram: {e}")
        return False

def get_todays_bets():
    """Get today's recommended bets"""
    try:
        from daily_recommendations import get_todays_value_bets
        return get_todays_value_bets()
    except:
        return []

def send_morning_update():
    """Send morning betting update"""
    bets = get_todays_bets()
    today = date.today().strftime('%A, %B %d, %Y')
    
    if len(bets) == 0:
        msg = f"🎰 *LarlBot Daily Update*\n"
        msg += f"📅 {today}\n\n"
        msg += f"No value bets identified for today.\n"
        msg += f"Check back tomorrow! 🐭"
        print("📊 No bets today - notification sent")
        return
    
    msg = f"🎰 *LarlBot Daily Betting Report*\n"
    msg += f"📅 {today}\n\n"
    msg += f"🎯 *{len(bets)} Value Bet{'s' if len(bets) != 1 else ''} Found*\n\n"
    
    for i, bet in enumerate(bets, 1):
        msg += f"*{i}. {bet['game']}*\n"
        msg += f"   ⏰ {bet['game_time']}\n"
        msg += f"   💎 Bet: {bet['recommendation']}\n"
        msg += f"   📊 FanDuel: {bet['fanduel_line']}\n"
        msg += f"   📈 Confidence: {bet['confidence']}%\n"
        msg += f"   💡 {bet['reason']}\n\n"
    
    msg += f"Dashboard: https://web-production-a39703.up.railway.app/\n\n"
    msg += f"Good luck! 🍀🎰"
    
        print(f"✅ Sent morning update: {len(bets)} bets")
    else:
        print(f"❌ Failed to send morning update")

if __name__ == "__main__":
    print(f"🎰 Morning Bet Update")
    print(f"📅 {date.today().strftime('%Y-%m-%d')}\n")
    send_morning_update()
