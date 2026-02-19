#!/usr/bin/env python3
"""
🎰 LarlBot Game Result Fixer
Marks finished games and moves them to previous results
"""

import json
import os
from datetime import datetime, timedelta
import pytz

WORKSPACE = "/Users/macmini/.openclaw/workspace"
ACTIVE_BETS_FILE = f"{WORKSPACE}/active_bets.json"
COMPLETED_BETS_FILE = f"{WORKSPACE}/completed_bets_2026-02-15.json"

def parse_game_time(game_time_str, date_str="2026-02-15"):
    """Parse game time string like '12:00 PM EST' to datetime"""
    try:
        # Parse time (e.g., "12:00 PM EST")
        time_part = game_time_str.replace(" EST", "").strip()
        dt_str = f"{date_str} {time_part}"
        
        # Create datetime object
        naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
        
        # Localize to EST
        est = pytz.timezone('US/Eastern')
        dt = est.localize(naive_dt)
        
        return dt
    except Exception as e:
        print(f"❌ Error parsing time '{game_time_str}': {e}")
        return None

def main():
    print("=" * 70)
    print("🎰 LarlBot Game Result Fixer")
    print("=" * 70)
    
    # Load active bets
    with open(ACTIVE_BETS_FILE, 'r') as f:
        active_data = json.load(f)
    
    bets = active_data.get('bets', [])
    date = active_data.get('date', '2026-02-15')
    
    print(f"\n📂 Processing {len(bets)} bets from {date}")
    
    # Get current time in EST
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    print(f"⏰ Current time: {now.strftime('%I:%M %p %Z')}")
    
    # Separate bets into active and finished
    active_bets = []
    finished_bets = []
    
    for bet in bets:
        game_time_str = bet.get('game_time', '')
        if not game_time_str:
            # No game time, assume pending
            bet['result'] = 'PENDING'
            active_bets.append(bet)
            continue
        
        # Parse game time
        game_time = parse_game_time(game_time_str, date)
        if not game_time:
            bet['result'] = 'PENDING'
            active_bets.append(bet)
            continue
        
        # Add ~3 hours to account for game duration
        estimated_end = game_time + timedelta(hours=3)
        
        # If estimated end is before now, game is finished
        if estimated_end < now:
            print(f"   ✅ FINISHED: {bet['game']} ({game_time_str}) - Ended ~{estimated_end.strftime('%I:%M %p')}")
            bet['result'] = 'PENDING'  # Will be updated when we get ESPN data
            bet['status'] = 'FINISHED'
            finished_bets.append(bet)
        else:
            print(f"   ⏳ ACTIVE: {bet['game']} ({game_time_str}) - Ends ~{estimated_end.strftime('%I:%M %p')}")
            bet['result'] = 'PENDING'
            active_bets.append(bet)
    
    # Update active_bets.json with ONLY active bets
    print(f"\n💾 Updating active_bets.json...")
    print(f"   📊 Active bets: {len(active_bets)}")
    print(f"   ✅ Finished bets: {len(finished_bets)}")
    
    active_data['bets'] = active_bets
    active_data['last_updated'] = datetime.now().isoformat()
    
    with open(ACTIVE_BETS_FILE, 'w') as f:
        json.dump(active_data, f, indent=2)
    
    # Save finished bets for reference
    if finished_bets:
        try:
            with open(COMPLETED_BETS_FILE, 'r') as f:
                completed_data = json.load(f)
        except:
            completed_data = {'date': date, 'bets': []}
        
        # Add finished bets to completed
        completed_data['bets'].extend(finished_bets)
        
        with open(COMPLETED_BETS_FILE, 'w') as f:
            json.dump(completed_data, f, indent=2)
        
        print(f"\n✅ Moved {len(finished_bets)} finished bets to completed_bets_2026-02-15.json")
    
    print(f"\n✅ Fix complete!")
    print(f"   Today's Bets dashboard now shows: {len(active_bets)} active bets")
    print(f"   Finished games ready for result verification via ESPN")

if __name__ == "__main__":
    main()
