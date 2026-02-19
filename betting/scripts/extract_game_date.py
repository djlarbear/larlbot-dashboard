#!/usr/bin/env python3
"""
Extract actual game date from game_time, not completion date
Games at 6+ PM EST likely play that day (evening games)
Games before 6 PM EST likely play that day (afternoon games)
All games happen on the date referenced by the event
"""

from datetime import datetime, timedelta
import json
import glob

def extract_game_date(game_time_str, completed_at_str):
    """
    Extract the actual game date from game_time and completed_at
    
    Logic:
    - If game is at 6 PM EST or later, it plays that evening
    - We process it the next morning (Feb 15)
    - So if game_time is evening, date should be one day before completed_at
    - For afternoon games, date is the same as completed_at
    """
    try:
        # Parse completed_at to get year/month
        completed_dt = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
        
        # Parse game_time (e.g., "08:04 PM EST")
        # Remove 'EST' and parse
        time_str = game_time_str.replace(' EST', '').strip()
        
        # Handle various formats
        if ':' in time_str:
            time_parts = time_str.split()
            time_only = time_parts[0]  # "08:04" or "8:04"
            am_pm = time_parts[-1] if len(time_parts) > 1 else 'PM'  # "PM" or "AM"
            
            # Parse time
            try:
                game_time = datetime.strptime(f"{time_only} {am_pm}", "%I:%M %p")
            except:
                game_time = datetime.strptime(f"{time_only} {am_pm}", "%H:%M %p")
            
            hour = game_time.hour
            
            # Evening games (6 PM or later) typically play that evening
            # We process them the next morning
            # So subtract 1 day if evening game
            if hour >= 18:  # 6 PM or later
                game_date = completed_dt - timedelta(days=1)
            else:
                # Afternoon/morning games
                game_date = completed_dt
            
            return game_date.strftime('%Y-%m-%d')
        else:
            # Fallback
            return completed_dt.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error parsing game_time '{game_time_str}': {e}")
        # Fallback to completed_at - 1 day for evening games
        if '08:' in game_time_str or '09:' in game_time_str or '10:' in game_time_str:
            completed_dt = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
            return (completed_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        return None

def fix_completed_bets_dates():
    """Fix dates in all completed_bets_*.json files"""
    fixed_count = 0
    total_count = 0
    
    for filepath in glob.glob('completed_bets_*.json'):
        print(f"\n📝 Processing {filepath}...")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for bet in data.get('bets', []):
            total_count += 1
            
            if not bet.get('date'):
                game_time = bet.get('game_time', '')
                completed_at = bet.get('completed_at', '')
                
                if game_time and completed_at:
                    correct_date = extract_game_date(game_time, completed_at)
                    if correct_date:
                        bet['date'] = correct_date
                        fixed_count += 1
                        print(f"  ✅ {bet.get('game', 'unknown')[:40]}: {correct_date}")
        
        # Save fixed data
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  Fixed: {sum(1 for b in data['bets'] if 'date' in b)}/{len(data['bets'])}")
    
    print(f"\n✅ Total fixed: {fixed_count}/{total_count}")

if __name__ == '__main__':
    fix_completed_bets_dates()
