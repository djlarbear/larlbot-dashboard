#!/usr/bin/env python3
"""
SWORD: Fetch actual game results from ESPN and update completed bets
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import re

def clean_team_name(name):
    """Clean team name for ESPN lookup"""
    # Remove common suffixes and clean up
    return name.replace('Ragin\' Cajuns', 'Cajuns').replace('Blue Devils', 'Blue').strip()

def fetch_espn_results(date_str):
    """
    Fetch college basketball results for a given date from ESPN
    date_str: 'YYYY-MM-DD' format
    Returns: dict of game results
    """
    
    print(f"\n🔍 Fetching ESPN results for {date_str}...")
    
    # Convert date to ESPN format (20260216)
    espn_date = date_str.replace('-', '')
    
    # This would normally call ESPN API
    # For now, return empty dict (we'll populate manually)
    # TODO: Implement actual ESPN scraping
    
    results = {}
    return results

def update_completed_bets_with_results(date_str, results_map):
    """
    Update completed_bets file with actual game results
    """
    
    workspace = Path('/Users/maclaw/workspace')
    bets_file = workspace / f'completed_bets_{date_str}.json'
    
    if not bets_file.exists():
        print(f"⚠️ File not found: {bets_file}")
        return
    
    with open(bets_file) as f:
        data = json.load(f)
    
    updated = 0
    for bet in data['bets']:
        game = bet['game']
        
        # Try to find matching result
        for game_name, (away_score, home_score, away_team_spread, recommendation_team) in results_map.items():
            if game.lower() in game_name.lower() or game_name.lower() in game.lower():
                # Determine if bet won or lost based on our recommendation
                # This is simplified - real logic would check spread vs final score
                
                bet['final_score'] = f"{away_score}-{home_score}"
                bet['completed_at'] = datetime.now().isoformat()
                
                # TODO: Implement proper WIN/LOSS logic based on our pick
                if bet.get('result') == 'PENDING':
                    # For now, mark as placeholder
                    bet['result'] = 'RESULT_NEEDED'
                
                updated += 1
                break
    
    if updated > 0:
        with open(bets_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Updated {updated} bets in {bets_file}")
    
    return updated

# For now, print instructions for manual fix
print("""
=" * 70)
SWORD: ESPN Result Tracking Not Implemented
=" * 70)

To properly track game results, we need to either:

1. **Use ESPN API** (recommended for production)
   - Requires ESPN API key + endpoint setup
   - Can fetch live scores and final results

2. **Use web scraping** (fallback)
   - Scrape ESPN.com directly
   - More fragile but doesn't require API key

3. **Manual input** (temporary)
   - User provides scores in dashboard
   - We mark bets WIN/LOSS manually

CURRENT STATUS:
✅ Stats aggregation: WORKING (bet_stats.json)
⚠️ Game result fetching: PENDING (needs ESPN integration)
❌ Automated win/loss determination: NEEDS IMPLEMENTATION

ACTION REQUIRED:
Provide Feb 16 game results so we can mark bets WIN/LOSS
OR set up ESPN API credentials
""")
