#!/usr/bin/env python3
"""
LarlBot Player Props Analyzer 🎰
Find value in player prop bets - often the softest markets
"""

import pandas as pd
from datetime import datetime
from odds_collector import OddsCollector
import numpy as np

class PlayerPropsAnalyzer:
    def __init__(self):
        self.odds_collector = OddsCollector()
        
        # Player averages (would be better from real API)
        self.player_averages = {
            # Today's mock players with realistic stats
            'Max Klesmit': {'points': 16.2, 'rebounds': 3.1, 'assists': 2.4},
            'Jaden Akins': {'points': 15.1, 'rebounds': 4.2, 'assists': 3.1}, 
            'Tyler Wahl': {'points': 11.8, 'rebounds': 8.2, 'assists': 2.1},
            'Gibson Jimerson': {'points': 19.1, 'rebounds': 4.1, 'assists': 2.8},
            'Philip Alston': {'points': 8.2, 'rebounds': 2.1, 'assists': 6.2},
            'Dwight Wilson': {'points': 21.2, 'rebounds': 5.4, 'assists': 1.8},
            'AJ Clayton': {'points': 14.1, 'rebounds': 9.1, 'assists': 2.4},
        }
        
        # Pace factors by team (faster pace = more stats)
        self.team_pace = {
            'Boston Celtics': 101.2,
            'Phoenix Suns': 102.1,
            'Sacramento Kings': 104.2,  # Fast pace
            'Miami Heat': 97.8,  # Slow pace
            # Would expand this
        }
    
    def get_player_props_odds(self):
        """Get player prop odds - tries real API first, falls back to realistic mock data"""
        print("📊 Collecting player props data...")
        
        # Try to get real player props first
        real_props = self.try_real_player_props()
        
        if real_props:
            print(f"✅ Found {len(real_props)} REAL player prop bets")
            return real_props
        
        # Fall back to smart mock data based on actual games
        print("⚠️ Real player props not available (free tier/off-season), using realistic mock data")
        return self.get_smart_mock_props()
    
    def try_real_player_props(self):
        """Attempt to get real player props from API"""
        try:
            # Get current games 
            all_odds = self.odds_collector.collect_all_odds()
            player_props = []
            
            for sport, games in all_odds.items():
                if not games:
                    continue
                    
                # Try to get raw game data with event IDs
                raw_games = self.odds_collector.get_sports_odds(sport.replace(' ', '_').lower())
                
                # Test first game only to save API calls
                if raw_games:
                    event_id = raw_games[0].get('id')
                    if event_id:
                        props = self.odds_collector.get_player_props_for_event(event_id)
                        if props:  # If we get any real props, use the real system
                            # Get props for a few more games
                            for raw_game in raw_games[:3]:
                                event_id = raw_game.get('id')
                                if event_id:
                                    more_props = self.odds_collector.get_player_props_for_event(event_id)
                                    player_props.extend(more_props)
                            return player_props
            
            return []  # No real props found
            
        except Exception as e:
            print(f"⚠️ Real props API error: {e}")
            return []
    
    def get_smart_mock_props(self):
        """DISABLED - No fake player props until we have real data"""
        print("❌ Player props DISABLED - will not show fake players as real betting opportunities")
        print("🎯 Real player props require:")
        print("   1. NBA/NFL season (more coverage)")  
        print("   2. Paid OddsAPI tier ($50/month)")
        print("   3. Or alternative player props API")
        print()
        print("✅ Game bets (spreads/totals) still work with real odds data!")
        return []
    
    def get_mock_player_props(self):
        """Fallback mock player props"""
        return [
            {'game': 'Michigan State Spartans @ Wisconsin Badgers', 'player': 'Max Klesmit', 'prop_type': 'points', 'line': 14.5, 'odds': -110, 'bookmaker': 'fanduel'},
            {'game': 'Michigan State Spartans @ Wisconsin Badgers', 'player': 'Jaden Akins', 'prop_type': 'points', 'line': 12.5, 'odds': -115, 'bookmaker': 'fanduel'},
            {'game': 'Saint Louis Billikens @ Loyola Chicago Ramblers', 'player': 'Gibson Jimerson', 'prop_type': 'points', 'line': 16.5, 'odds': -110, 'bookmaker': 'betonlineag'},
            {'game': 'Ohio Bobcats @ Miami (OH) RedHawks', 'player': 'Dwight Wilson', 'prop_type': 'points', 'line': 18.5, 'odds': -110, 'bookmaker': 'betonlineag'},
        ]
    
    def analyze_player_prop(self, prop):
        """Analyze a single player prop for value"""
        player = prop['player']
        prop_type = prop['prop_type']  # points, rebounds, assists
        market_line = prop['line']
        
        # Get player's average (simplified)
        player_avg = self.get_player_average(player, prop_type)
        if not player_avg:
            return None
        
        # Pace adjustment
        pace_factor = self.get_pace_adjustment(prop['game'])
        adjusted_avg = player_avg * pace_factor
        
        # Calculate edge
        edge = abs(adjusted_avg - market_line)
        
        # Determine bet recommendation
        if adjusted_avg > market_line + 1.5:  # 1.5+ edge threshold
            recommendation = f"OVER {market_line}"
            confidence = min(0.8, edge / 5)  # Higher edge = higher confidence
        elif adjusted_avg < market_line - 1.5:
            recommendation = f"UNDER {market_line}"  
            confidence = min(0.8, edge / 5)
        else:
            return None
        
        return {
            'game': prop['game'],
            'player': player,
            'prop_type': prop_type.title(),
            'market_line': market_line,
            'our_projection': round(adjusted_avg, 1),
            'recommendation': recommendation,
            'edge': round(edge, 1),
            'confidence': confidence,
            'bookmaker': prop['bookmaker'],
            'bet_type': 'player_prop'
        }
    
    def get_player_average(self, player, stat_type):
        """Get player's average for this stat type"""
        if player in self.player_averages:
            return self.player_averages[player].get(stat_type, None)
        
        # Simplified fallback averages by position/tier
        fallback_averages = {
            'points': np.random.normal(15, 8),  # Would use real data
            'rebounds': np.random.normal(6, 3),
            'assists': np.random.normal(4, 2)
        }
        
        return max(0, fallback_averages.get(stat_type, 10))
    
    def get_pace_adjustment(self, game_matchup):
        """Adjust for game pace - faster games = more stats"""
        # Parse teams from matchup
        if '@' in game_matchup:
            away, home = game_matchup.split(' @ ')
        else:
            return 1.0
        
        away_pace = self.team_pace.get(away.strip(), 100)
        home_pace = self.team_pace.get(home.strip(), 100)
        avg_pace = (away_pace + home_pace) / 2
        
        # Convert to multiplier (100 = average pace)
        return avg_pace / 100
    
    def find_player_prop_values(self):
        """Find all player prop value bets"""
        props = self.get_player_props_odds()
        value_props = []
        
        print("🎯 Analyzing player props for value...")
        
        for prop in props:
            analysis = self.analyze_player_prop(prop)
            if analysis and analysis['confidence'] > 0.4:
                value_props.append(analysis)
        
        # Sort by edge
        value_props.sort(key=lambda x: x['edge'], reverse=True)
        
        print(f"✅ Found {len(value_props)} value player props")
        return value_props
    
    def display_prop_summary(self, props):
        """Display player prop opportunities"""
        if not props:
            print("No player prop values found")
            return
        
        print(f"\n🏀 PLAYER PROP VALUE BETS:")
        print("=" * 50)
        
        for i, prop in enumerate(props, 1):
            print(f"{i}. {prop['player']} - {prop['prop_type']}")
            print(f"   Game: {prop['game']}")
            print(f"   BET: {prop['recommendation']}")
            print(f"   Market Line: {prop['market_line']} | Our Projection: {prop['our_projection']}")
            print(f"   Edge: {prop['edge']} | Confidence: {prop['confidence']:.0%}")
            print(f"   Book: {prop['bookmaker']}")
            print()

if __name__ == "__main__":
    analyzer = PlayerPropsAnalyzer()
    props = analyzer.find_player_prop_values()
    analyzer.display_prop_summary(props)