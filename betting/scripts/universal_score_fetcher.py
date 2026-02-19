#!/usr/bin/env python3
"""
Universal Score Fetcher - ESPN API wrapper for all sports
Fetches scores and game results for NCAA, NBA, NHL, NFL
"""

import requests
import json
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

from sport_config import get_sport_config, get_active_sports

class UniversalScoreFetcher:
    """Fetch scores from ESPN API for any sport"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports"
        self.timeout = 15
    
    def fetch_scores_for_sport(self, sport_code, date_str=None):
        """
        Fetch all game scores for a sport on a given date
        
        Args:
            sport_code: 'ncaab', 'nba', 'nhl', 'nfl'
            date_str: 'YYYY-MM-DD' or None for today
            
        Returns:
            List of games with scores
        """
        config = get_sport_config(sport_code)
        if not config:
            print(f"❌ Unknown sport: {sport_code}")
            return []
        
        # Get endpoint
        endpoint = config["api_endpoint"]
        
        # Add date if provided
        if date_str:
            # Convert YYYY-MM-DD to YYYYMMDD for ESPN API
            date_formatted = date_str.replace('-', '')
            endpoint += f"?dates={date_formatted}"
        
        try:
            print(f"⏳ Fetching {config['display_name']} scores...")
            response = requests.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            events = data.get('events', [])
            
            print(f"✅ Found {len(events)} games")
            
            # Parse games
            games = []
            for event in events:
                game = self.parse_espn_event(event, sport_code)
                if game:
                    games.append(game)
            
            return games
        
        except Exception as e:
            print(f"❌ Error fetching {sport_code}: {e}")
            return []
    
    def parse_espn_event(self, event, sport_code):
        """Parse ESPN event into standardized game format"""
        try:
            competitors = event.get('competitions', [{}])[0].get('competitors', [])
            if len(competitors) < 2:
                return None
            
            away = competitors[1]  # First competitor is typically away
            home = competitors[0]  # Second is home
            
            # Extract scores if game is finished
            game_state = event.get('competitions', [{}])[0].get('status', {}).get('type', 'PRE')
            
            away_score = away.get('score')
            home_score = home.get('score')
            
            game = {
                'sport': sport_code,
                'game': f"{away.get('team', {}).get('displayName')} @ {home.get('team', {}).get('displayName')}",
                'away_team': away.get('team', {}).get('displayName'),
                'home_team': home.get('team', {}).get('displayName'),
                'away_score': away_score,
                'home_score': home_score,
                'game_state': game_state,
                'date': event.get('date'),
                'finished': game_state == 'Final' if away_score is not None else False,
            }
            
            return game
        except Exception as e:
            print(f"⚠️ Error parsing event: {e}")
            return None
    
    def fetch_all_active_sports(self, date_str=None):
        """Fetch scores for all active sports on a date"""
        all_games = {}
        
        for sport_code in get_active_sports():
            games = self.fetch_scores_for_sport(sport_code, date_str)
            if games:
                all_games[sport_code] = games
                print(f"  → {len(games)} games for {sport_code}")
        
        return all_games

if __name__ == "__main__":
    fetcher = UniversalScoreFetcher()
    
    # Test: Fetch today's scores for all sports
    print("=== UNIVERSAL SCORE FETCHER ===\n")
    all_games = fetcher.fetch_all_active_sports()
    
    print("\n=== SUMMARY ===")
    total_games = sum(len(games) for games in all_games.values())
    print(f"Total games across all sports: {total_games}")
    
    for sport, games in all_games.items():
        config = get_sport_config(sport)
        print(f"\n{config['display_name']}: {len(games)} games")
        for game in games[:2]:  # Show first 2
            print(f"  - {game['game']} ({game['game_state']})")
