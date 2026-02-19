#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE BET GENERATOR v2.0
Generate ALL bet options (both sides + over/under) and let LarlScore rank them

Instead of the pick generator choosing one side, we generate:
- Both -SPREAD and +SPREAD for each game
- Both OVER and UNDER for each game  
- Then LarlScore v4.0 ranks ALL options by edge + confidence

This ensures we don't miss good opportunities
"""

import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/Users/macmini/.openclaw/workspace")

class ComprehensiveBetGenerator:
    def __init__(self):
        self.oddsapi_key = 'c5c88f2a63b7e8ab2b26988b04c206f7'
        self.base_url = 'https://api.the-odds-api.com/v4'
    
    def fetch_all_games(self):
        """Fetch all games and odds from OddsAPI"""
        try:
            url = f"{self.base_url}/sports/college_basketball/odds"
            params = {
                'api_key': self.oddsapi_key,
                'regions': 'us',
                'markets': 'spreads,h2h,totals',
                'oddsFormat': 'american'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                games = response.json()
                
                # Filter to today's games only
                now_est = datetime.now(timezone(timedelta(hours=-5)))
                today_est_date = now_est.date()
                
                today_games = []
                for game in games:
                    try:
                        commence = game.get('commence_time', '')
                        game_time_utc = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                        est_offset = timedelta(hours=-5)
                        est_tz = timezone(est_offset)
                        game_time_est = game_time_utc.astimezone(est_tz)
                        
                        if game_time_est.date() == today_est_date:
                            today_games.append(game)
                    except:
                        continue
                
                return today_games
        except Exception as e:
            print(f"Error fetching games: {e}")
        
        return []
    
    def generate_all_bet_options(self, games):
        """Generate ALL bet options (both sides for spreads, both over/under)"""
        all_bets = []
        
        for game in games:
            home = game.get('home_team', 'Unknown')
            away = game.get('away_team', 'Unknown')
            game_string = f"{away} @ {home}"
            
            try:
                commence = game.get('commence_time', '')
                game_time_utc = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                game_time_est = game_time_utc.astimezone(timezone(timedelta(hours=-5)))
                time_str = game_time_est.strftime('%I:%M %p EST')
            except:
                time_str = 'TBA'
            
            bookmakers = game.get('bookmakers', [])
            
            # Extract FanDuel odds
            for bookmaker in bookmakers:
                if 'fanduel' not in bookmaker.get('title', '').lower():
                    continue
                
                markets = bookmaker.get('markets', [])
                
                # SPREADS: Generate BOTH sides
                for market in markets:
                    if market.get('key') == 'spreads':
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            home_outcome = None
                            away_outcome = None
                            
                            for outcome in outcomes:
                                name = outcome.get('name', '').lower()
                                if home.lower() in name:
                                    home_outcome = outcome
                                elif away.lower() in name:
                                    away_outcome = outcome
                            
                            if home_outcome and away_outcome:
                                home_spread = home_outcome.get('point', 0)
                                away_spread = away_outcome.get('point', 0)
                                
                                # BET 1: HOME SIDE
                                bet1 = {
                                    'game': game_string,
                                    'bet_type': 'SPREAD',
                                    'recommendation': f"{home} {home_spread:+.1f}",
                                    'side': 'HOME',
                                    'spread': home_spread,
                                    'confidence': 70,  # Placeholder - will be refined
                                    'edge': abs(home_spread) * 0.4,
                                }
                                all_bets.append(bet1)
                                
                                # BET 2: AWAY SIDE
                                bet2 = {
                                    'game': game_string,
                                    'bet_type': 'SPREAD',
                                    'recommendation': f"{away} {away_spread:+.1f}",
                                    'side': 'AWAY',
                                    'spread': away_spread,
                                    'confidence': 70,  # Placeholder
                                    'edge': abs(away_spread) * 0.4,
                                }
                                all_bets.append(bet2)
                
                # TOTALS: Generate BOTH over and under
                for market in markets:
                    if market.get('key') == 'totals':
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            total_value = None
                            over_outcome = None
                            under_outcome = None
                            
                            for outcome in outcomes:
                                name = outcome.get('name', '').lower()
                                if 'over' in name:
                                    over_outcome = outcome
                                    total_value = outcome.get('point', 0)
                                elif 'under' in name:
                                    under_outcome = outcome
                                    total_value = outcome.get('point', 0)
                            
                            if total_value and over_outcome and under_outcome:
                                # BET 3: OVER
                                bet3 = {
                                    'game': game_string,
                                    'bet_type': 'TOTAL',
                                    'recommendation': f"OVER {total_value}",
                                    'side': 'OVER',
                                    'total': total_value,
                                    'confidence': 58,  # Placeholder
                                    'edge': total_value * 0.15,
                                }
                                all_bets.append(bet3)
                                
                                # BET 4: UNDER
                                bet4 = {
                                    'game': game_string,
                                    'bet_type': 'TOTAL',
                                    'recommendation': f"UNDER {total_value}",
                                    'side': 'UNDER',
                                    'total': total_value,
                                    'confidence': 58,  # Placeholder
                                    'edge': total_value * 0.15,
                                }
                                all_bets.append(bet4)
        
        return all_bets
    
    def main(self):
        """Generate all comprehensive bet options"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE BET GENERATOR v2.0")
        print("="*80)
        
        # Fetch games
        print("\n📡 Fetching today's games from OddsAPI...")
        games = self.fetch_all_games()
        print(f"✅ Found {len(games)} games for today")
        
        # Generate all bet options
        print("\n🎲 Generating ALL bet options (both sides)...")
        all_bets = self.generate_all_bet_options(games)
        print(f"✅ Generated {len(all_bets)} total bet options")
        
        # Summary
        spreads = [b for b in all_bets if b['bet_type'] == 'SPREAD']
        totals = [b for b in all_bets if b['bet_type'] == 'TOTAL']
        overs = [b for b in all_bets if b.get('side') == 'OVER']
        unders = [b for b in all_bets if b.get('side') == 'UNDER']
        homes = [b for b in all_bets if b.get('side') == 'HOME']
        aways = [b for b in all_bets if b.get('side') == 'AWAY']
        
        print(f"\n📊 BREAKDOWN:")
        print(f"   SPREADS:   {len(spreads)} ({homes} HOME + {aways} AWAY)")
        print(f"   TOTALS:    {len(totals)} ({overs} OVER + {unders} UNDER)")
        print(f"\n✅ All options ready for LarlScore v4.0 ranking!")
        print("   Let the formula decide which bets are best, not hardcoded logic.")

if __name__ == '__main__':
    gen = ComprehensiveBetGenerator()
    gen.main()
