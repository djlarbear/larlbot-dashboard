#!/usr/bin/env python3
"""
Get the last odds update timestamp from cache
"""

import sqlite3
from datetime import datetime
import pytz

def get_last_odds_update():
    """Get the most recent odds update timestamp from cache"""
    try:
        conn = sqlite3.connect('odds_cache.db')
        cursor = conn.cursor()
        
        # Get the most recent update across all sports
        cursor.execute('''
            SELECT MAX(last_updated) FROM odds_cache
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # Parse timestamp and convert to EST
            last_updated = datetime.fromisoformat(result[0])
            est = pytz.timezone('America/New_York')
            last_updated_est = last_updated.astimezone(est)
            return last_updated_est.strftime('%I:%M %p').lstrip('0')
        
        return "Never"
    
    except Exception as e:
        print(f"Error getting odds timestamp: {e}")
        return "Unknown"

if __name__ == "__main__":
    timestamp = get_last_odds_update()
    print(f"Last odds update: {timestamp}")
