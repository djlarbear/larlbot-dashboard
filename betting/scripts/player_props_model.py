#!/usr/bin/env python3
"""
Player Props Model v1.0
Fetches player prop markets from OddsAPI (FanDuel)
Supports: Points, Rebounds, Assists, Threes, etc.
"""

import requests
from datetime import datetime, timezone

class PlayerPropsModel:
    def __init__(self):
        self.oddsapi_key = '82865426fd192e243376eb4e51185f3b'
        self.base_url = "https://api.the-odds-api.com/v4"
        
        # Sports that support player props
        self.prop_sports = [
            {'key': 'basketball_nba', 'display': 'NBA', 'emoji': '🏀'},
            {'key': 'basketball_ncaab', 'display': 'NCAA Basketball', 'emoji': '🏀'},
            {'key': 'americanfootball_nfl', 'display': 'NFL', 'emoji': '🏈'},
            {'key': 'baseball_mlb', 'display': 'MLB', 'emoji': '⚾'},
            {'key': 'ice_hockey_nhl', 'display': 'NHL', 'emoji': '🏒'},
        ]
        
        # Player prop markets
        self.markets = [
            'player_points',
            'player_rebounds', 
            'player_assists',
            'player_threes',
            'player_pass_tds',
            'player_pass_yds',
            'player_rush_yds',
            'player_receptions',
            'player_reception_yds',
            'player_hits',
            'player_total_bases',
            'player_home_runs',
        ]
    
    def fetch_player_props(self, sport_key, market='player_points'):
        """Fetch player props for a specific sport and market"""
        try:
            url = f"{self.base_url}/sports/{sport_key}/events"
            params = {
                'apiKey': self.oddsapi_key,
                'regions': 'us',
                'markets': market,
                'oddsFormat': 'american',
                'bookmakers': 'fanduel',
                'dateFormat': 'iso'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return []
            else:
                print(f"⚠️ Props API error {response.status_code} for {sport_key}/{market}")
                return []
        
        except Exception as e:
            print(f"⚠️ Error fetching props: {e}")
            return []
    
    def generate_prop_picks(self):
        """Generate player prop betting opportunities"""
        all_props = []
        
        print("🏅 Fetching player props from FanDuel...")
        
        for sport in self.prop_sports:
            sport_key = sport['key']
            display_name = sport['display']
            emoji = sport['emoji']
            
            # Try player points/touchdowns for this sport
            for market in self.markets:
                events = self.fetch_player_props(sport_key, market)
                
                if not events:
                    continue
                
                print(f"  [{emoji} {display_name} - {market}] ✅ {len(events)} games")
                
                for event in events:
                    home_team = event.get('home_team', '')
                    away_team = event.get('away_team', '')
                    game = f"{away_team} @ {home_team}"
                    
                    commence_time = event.get('commence_time', '')
                    game_time = self.format_time(commence_time)
                    
                    bookmakers = event.get('bookmakers', [])
                    for book in bookmakers:
                        if book.get('key') != 'fanduel':
                            continue
                        
                        markets = book.get('markets', [])
                        for mkt in markets:
                            if mkt.get('key') != market:
                                continue
                            
                            outcomes = mkt.get('outcomes', [])
                            for outcome in outcomes:
                                player_name = outcome.get('description', 'Unknown Player')
                                line = outcome.get('point', 0)
                                over_price = outcome.get('price', 0)
                                
                                # Find corresponding under
                                under = next((o for o in outcomes if o.get('name') == 'Under' and o.get('description') == player_name), None)
                                under_price = under.get('price', 0) if under else 0
                                
                                # Simple edge calculation (placeholder - can be improved)
                                edge = abs(over_price - under_price) / 20.0
                                confidence = min(85, 55 + edge * 2)
                                
                                prop_pick = {
                                    'game': game,
                                    'sport': f"{emoji} {display_name}",
                                    'bet_type': 'PLAYER PROP',
                                    'prop_market': market.replace('player_', '').replace('_', ' ').title(),
                                    'player': player_name,
                                    'recommendation': f"{player_name} OVER {line}",
                                    'fanduel_line': f"Over {line} ({over_price}) / Under {line} ({under_price})",
                                    'edge': round(edge, 1),
                                    'confidence': round(confidence),
                                    'risk_tier': '🟡 MODERATE RISK',
                                    'game_time': game_time,
                                    'reason': f"Player prop: {player_name} {market.replace('player_', '')} line at {line}",
                                    'bet_instructions': f"📍 PLACE BET ON FanDuel: {player_name} OVER {line} {market.replace('player_', '')}",
                                    'bet_explanation': f"Bet that {player_name} will score OVER {line} {market.replace('player_', '')}",
                                    'bookmaker_source': 'FanDuel',
                                }
                                
                                all_props.append(prop_pick)
        
        print(f"📊 Total player props available: {len(all_props)}\n")
        return all_props
    
    def format_time(self, iso_time):
        """Convert ISO time to EST"""
        try:
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            est = dt.astimezone(timezone.utc).astimezone()
            return est.strftime("%I:%M %p EST")
        except:
            return "TBA"

if __name__ == '__main__':
    model = PlayerPropsModel()
    props = model.generate_prop_picks()
    
    if props:
        print(f"{'='*70}")
        print(f"🏅 Player Props Available")
        print(f"{'='*70}")
        
        for i, prop in enumerate(props[:10], 1):  # Show first 10
            print(f"\n{i}. {prop['player']} - {prop['prop_market']}")
            print(f"   Game: {prop['game']}")
            print(f"   📊 Bet: {prop['recommendation']}")
            print(f"   📈 Confidence: {prop['confidence']}% | Edge: {prop['edge']}")
            print(f"   ⏰ When: {prop['game_time']}")
    else:
        print("⚠️ No player props available today")
