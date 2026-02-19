#!/usr/bin/env python3
"""
Real Odds Collection from The-Odds-API
Get actual market odds instead of simulated ones
"""

import requests
import json
from datetime import datetime
import sqlite3
from draftkings_scraper import DraftKingsScraper
from odds_cache_manager import OddsCacheManager
from oddsapi_rate_limiter import OddsAPIRateLimiter

class OddsCollector:
    def __init__(self, api_key=None):
        # OddsAPI key - Paid tier ($50/month) - 20,000 requests/month + player props!
        self.api_key = api_key or "82865426fd192e243376eb4e51185f3b"
        self.base_url = "https://api.the-odds-api.com/v4"
        self.dk_scraper = DraftKingsScraper()
        self.cache_manager = OddsCacheManager()
        self.rate_limiter = OddsAPIRateLimiter(api_key=self.api_key)
        
    def get_sports_odds(self, sport='basketball_nba', bookmakers='fanduel,draftkings,betonlineag'):
        """Get odds for a specific sport with smart caching"""
        
        # Check cache first
        cached_odds, last_updated = self.cache_manager.get_cached_odds(sport)
        
        # Use cache if fresh or if we've hit daily limit
        if cached_odds is not None and not self.cache_manager.should_refresh_odds(sport):
            cache_age = (datetime.now() - last_updated).total_seconds() / 3600
            print(f"💾 Using cached {sport} data ({cache_age:.1f}h old)")
            return cached_odds
        
        # Check rate limiter before making API call
        can_request, message = self.rate_limiter.can_make_request(1)
        if not can_request:
            print(f"⚠️ Rate limit reached: {message}")
            if cached_odds is not None:
                return cached_odds
            else:
                return self.get_mock_odds(sport)
        
        # Make API call if allowed
        if not self.cache_manager.can_make_api_call():
            print(f"⚠️ Daily API limit reached! Using cached data or mock data")
            if cached_odds is not None:
                return cached_odds
            else:
                return self.get_mock_odds(sport)
        
        # Fetch fresh data with FanDuel preference
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': bookmakers  # Prefer FanDuel, fallback to DK/BetOnline
        }
        
        try:
            print(f"🔄 Fetching fresh {sport} odds from API (preferring FanDuel)...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Record usage in rate limiter and cache the data
            self.rate_limiter.record_request(1)
            self.cache_manager.increment_daily_usage()
            self.cache_manager.cache_odds(sport, data)
            
            daily_usage = self.cache_manager.get_daily_usage()
            print(f"✅ Fresh odds from OddsAPI: {len(data)} games (API calls today: {daily_usage}/500)")
            
            return data
            
        except Exception as e:
            print(f"⚠️ OddsAPI failed ({e})")
            # Try cache as fallback
            if cached_odds is not None:
                print("💾 Falling back to cached data")
                return cached_odds
            else:
                print("🎭 Using mock data")
                return self.get_mock_odds(sport)
    
    def get_player_props_for_event(self, event_id, bookmakers='fanduel,draftkings'):
        """Get player props for a specific event using the /events/{eventId}/odds endpoint
        
        NOTE: Player props require a PAID OddsAPI tier ($50/month minimum)
        Free tier does NOT include player props markets
        """
        url = f"{self.base_url}/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'player_points,player_rebounds,player_assists,player_threes',
            'oddsFormat': 'american',
            'bookmakers': bookmakers  # Prefer FanDuel, fallback to DraftKings
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to our player props format
            return self.convert_player_props(data)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️ Player props not available for event {event_id} (requires paid tier)")
            else:
                print(f"⚠️ Player props failed for event {event_id}: {e}")
            return []
        except Exception as e:
            print(f"⚠️ Player props failed for event {event_id}: {e}")
            return []
    
    def convert_player_props(self, event_data):
        """Convert OddsAPI player props response to our format"""
        player_props = []
        
        if not event_data or not event_data.get('bookmakers'):
            return player_props
        
        away_team = event_data.get('away_team', 'Unknown')
        home_team = event_data.get('home_team', 'Unknown') 
        game_matchup = f"{away_team} @ {home_team}"
        
        for bookmaker in event_data['bookmakers']:
            bookmaker_key = bookmaker.get('key', 'unknown')
            
            for market in bookmaker.get('markets', []):
                market_key = market.get('key', '')
                prop_type = market_key.replace('player_', '') if market_key.startswith('player_') else market_key
                
                for outcome in market.get('outcomes', []):
                    # For player props, the outcome name is the player name
                    player_name = outcome.get('name', 'Unknown Player')
                    prop_line = outcome.get('point', 0)
                    prop_odds = outcome.get('price', -110)
                    
                    player_props.append({
                        'game': game_matchup,
                        'player': player_name,
                        'prop_type': prop_type,
                        'line': prop_line,
                        'odds': prop_odds,
                        'bookmaker': bookmaker_key,
                        'event_id': event_data.get('id')
                    })
        
        return player_props
    
    def get_mock_odds(self, sport):
        """Mock odds data for testing (realistic values)"""
        mock_odds = {
            'basketball_nba': [
                {
                    'id': 'mock_nba_1',
                    'home_team': 'Los Angeles Lakers',
                    'away_team': 'Golden State Warriors',
                    'bookmakers': [
                        {
                            'key': 'draftkings',
                            'markets': [
                                {
                                    'key': 'spreads',
                                    'outcomes': [
                                        {'name': 'Los Angeles Lakers', 'price': -110, 'point': -3.5},
                                        {'name': 'Golden State Warriors', 'price': -110, 'point': 3.5}
                                    ]
                                },
                                {
                                    'key': 'totals',
                                    'outcomes': [
                                        {'name': 'Over', 'price': -110, 'point': 225.5},
                                        {'name': 'Under', 'price': -110, 'point': 225.5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            'basketball_ncaab': [
                {
                    'id': 'mock_ncb_1', 
                    'home_team': 'Duke Blue Devils',
                    'away_team': 'North Carolina Tar Heels',
                    'bookmakers': [
                        {
                            'key': 'fanduel',
                            'markets': [
                                {
                                    'key': 'spreads',
                                    'outcomes': [
                                        {'name': 'Duke Blue Devils', 'price': -108, 'point': -5.5},
                                        {'name': 'North Carolina Tar Heels', 'price': -112, 'point': 5.5}
                                    ]
                                },
                                {
                                    'key': 'totals', 
                                    'outcomes': [
                                        {'name': 'Over', 'price': -110, 'point': 152.5},
                                        {'name': 'Under', 'price': -110, 'point': 152.5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        return mock_odds.get(sport, [])
    
    def parse_odds_data(self, odds_data):
        """Parse odds data into standard format, preferring FanDuel"""
        parsed_odds = []
        
        for game in odds_data:
            if not game.get('bookmakers'):
                continue
            
            # Prefer FanDuel, then DraftKings, then any other bookmaker
            bookmaker = None
            for bm in game['bookmakers']:
                if bm['key'] == 'fanduel':
                    bookmaker = bm
                    break
            
            if not bookmaker:
                for bm in game['bookmakers']:
                    if bm['key'] == 'draftkings':
                        bookmaker = bm
                        break
            
            if not bookmaker:
                bookmaker = game['bookmakers'][0]  # Fallback to first available
            
            game_odds = {
                'game_id': game['id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'bookmaker': bookmaker['key'],
                'spreads': {},
                'totals': {}
            }
            
            for market in bookmaker.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        if outcome['name'] == game['home_team']:
                            game_odds['spreads']['home_spread'] = outcome.get('point', 0)
                            game_odds['spreads']['home_price'] = outcome.get('price', -110)
                        else:
                            game_odds['spreads']['away_spread'] = outcome.get('point', 0)
                            game_odds['spreads']['away_price'] = outcome.get('price', -110)
                            
                elif market['key'] == 'totals':
                    for outcome in market['outcomes']:
                        if outcome['name'] == 'Over':
                            game_odds['totals']['over_total'] = outcome.get('point', 0)
                            game_odds['totals']['over_price'] = outcome.get('price', -110)
                        else:
                            game_odds['totals']['under_total'] = outcome.get('point', 0)  
                            game_odds['totals']['under_price'] = outcome.get('price', -110)
            
            parsed_odds.append(game_odds)
        
        return parsed_odds
    
    def collect_all_odds(self):
        """Collect odds from multiple sources"""
        sports_map = {
            'basketball_nba': ('nba', 'NBA'),
            'basketball_ncaab': ('ncb', 'NCAA Basketball'), 
            'baseball_mlb': ('mlb', 'MLB'),
            'americanfootball_nfl': ('nfl', 'NFL')
        }
        
        all_odds = {}
        
        for api_sport, (dk_sport, sport_name) in sports_map.items():
            print(f"📊 Collecting odds for {sport_name}...")
            
            # Try OddsAPI first
            odds_data = self.get_sports_odds(api_sport)
            parsed_odds = []
            
            if odds_data and not isinstance(odds_data, list) or len(odds_data) > 0:
                try:
                    parsed_odds = self.parse_odds_data(odds_data)
                    if parsed_odds:
                        print(f"✅ OddsAPI: {len(parsed_odds)} {sport_name} games")
                except Exception as e:
                    print(f"⚠️ Error parsing OddsAPI data: {e}")
            
            # If OddsAPI fails or has no data, try DraftKings scraping
            if not parsed_odds:
                print(f"🎯 Trying DraftKings scraping for {sport_name}...")
                try:
                    dk_odds = self.dk_scraper.get_dk_odds(dk_sport)
                    if dk_odds:
                        parsed_odds = self.parse_dk_odds(dk_odds)
                        print(f"✅ DraftKings: {len(parsed_odds)} {sport_name} games")
                except Exception as e:
                    print(f"⚠️ DraftKings scraping failed: {e}")
            
            if parsed_odds:
                all_odds[api_sport] = parsed_odds
            else:
                print(f"❌ No odds found for {sport_name}")
        
        return all_odds
    
    def parse_dk_odds(self, dk_data):
        """Parse DraftKings scraped data into standard format"""
        parsed_odds = []
        
        for game in dk_data:
            if game.get('home_team') and game.get('away_team'):
                parsed_odds.append({
                    'game_id': game['game_id'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'bookmaker': 'draftkings',
                    'spreads': {
                        'home_spread': game.get('spread'),
                        'home_price': -110,  # Default DK pricing
                        'away_spread': -game.get('spread') if game.get('spread') else None,
                        'away_price': -110
                    },
                    'totals': {
                        'over_total': game.get('total'),
                        'over_price': -110,
                        'under_total': game.get('total'),
                        'under_price': -110
                    }
                })
        
        return parsed_odds

if __name__ == "__main__":
    # Test odds collection
    collector = OddsCollector()
    odds = collector.collect_all_odds()
    print(f"\n📈 Odds Collection Summary:")
    for sport, games in odds.items():
        print(f"   {sport}: {len(games)} games with odds")