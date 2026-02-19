#!/usr/bin/env python3
"""
LarlBot Betting Opportunity Analyzer 🎰
Finds value bets across multiple sports
"""

import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import requests
import json
from odds_collector import OddsCollector
from player_props_analyzer import PlayerPropsAnalyzer

class BettingAnalyzer:
    def __init__(self):
        self.db_path = 'sports_betting.db'
        self.odds_collector = OddsCollector()
        self.live_odds = {}  # Cache for current odds data
        
        # Historical averages for prediction baseline
        self.historical_edges = {
            'nba': {'avg_total': 220, 'home_advantage': 3.5},
            'ncb': {'avg_total': 145, 'home_advantage': 4.0}, 
            'mlb': {'avg_total': 8.5, 'home_advantage': 0.5},
            'nfl': {'avg_total': 44, 'home_advantage': 2.5}
        }
        
    def get_todays_games(self):
        """Get today's games from database"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT * FROM games 
            WHERE date >= date('now') 
            AND date < date('now', '+2 days')
            ORDER BY sport, date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def calculate_basic_power_ratings(self, sport):
        """Basic power ratings based on recent performance"""
        conn = sqlite3.connect(self.db_path)
        
        # Get recent games for this sport (last 30 days)
        query = f"""
            SELECT home_team, away_team, home_score, away_score, date
            FROM games 
            WHERE sport = '{sport}' 
            AND date >= date('now', '-30 days')
            AND status NOT LIKE '%scheduled%'
            AND home_score IS NOT NULL
        """
        
        recent_games = pd.read_sql_query(query, conn)
        conn.close()
        
        if recent_games.empty:
            return {}
            
        # Calculate simple ratings
        team_ratings = {}
        
        for _, game in recent_games.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            home_score = game['home_score']
            away_score = game['away_score']
            
            # Initialize ratings if not exists
            if home_team not in team_ratings:
                team_ratings[home_team] = {'points_for': 0, 'points_against': 0, 'games': 0}
            if away_team not in team_ratings:
                team_ratings[away_team] = {'points_for': 0, 'points_against': 0, 'games': 0}
            
            # Update ratings
            team_ratings[home_team]['points_for'] += home_score
            team_ratings[home_team]['points_against'] += away_score
            team_ratings[home_team]['games'] += 1
            
            team_ratings[away_team]['points_for'] += away_score
            team_ratings[away_team]['points_against'] += home_score
            team_ratings[away_team]['games'] += 1
        
        # Calculate efficiency ratings
        power_ratings = {}
        for team, stats in team_ratings.items():
            if stats['games'] > 0:
                avg_for = stats['points_for'] / stats['games']
                avg_against = stats['points_against'] / stats['games']
                # Simple power rating: offensive efficiency - defensive efficiency
                power_ratings[team] = avg_for - avg_against
        
        return power_ratings
    
    def predict_game(self, game, power_ratings):
        """Enhanced prediction with better team analysis"""
        home_team = game['home_team']
        away_team = game['away_team']
        sport = game['sport']
        
        # Get power ratings with better defaults based on team names
        home_rating = self.get_enhanced_rating(home_team, power_ratings, sport)
        away_rating = self.get_enhanced_rating(away_team, power_ratings, sport)
        
        # Enhanced home field advantage based on sport and venue
        home_advantage = self.get_home_advantage(sport, game.get('venue', ''))
        
        # Predicted point differential (home team perspective)  
        predicted_spread = (home_rating - away_rating) + home_advantage
        
        # Enhanced total prediction with pace factors
        avg_total = self.historical_edges[sport]['avg_total']
        pace_factor = (abs(home_rating) + abs(away_rating)) / 8  # Reduced impact
        predicted_total = avg_total + pace_factor
        
        return {
            'predicted_spread': round(predicted_spread, 1),
            'predicted_total': round(predicted_total, 1),
            'home_rating': round(home_rating, 1),
            'away_rating': round(away_rating, 1)
        }
    
    def get_enhanced_rating(self, team_name, power_ratings, sport):
        """Get enhanced team rating with conference/league adjustments"""
        base_rating = power_ratings.get(team_name, 0)
        
        # Conference strength adjustments for NCAA
        if sport == 'ncb':
            conference_boosts = {
                'Duke': 8, 'North Carolina': 7, 'Kansas': 8, 'Kentucky': 6,
                'Villanova': 5, 'Gonzaga': 7, 'Michigan State': 4, 'Wisconsin': 2,
                'Saint Louis': -2, 'Loyola Chicago': -1  # Mid-major adjustments
            }
            
            for team_key, boost in conference_boosts.items():
                if team_key.lower() in team_name.lower():
                    base_rating += boost
                    break
        
        return base_rating
    
    def get_home_advantage(self, sport, venue):
        """Calculate sport and venue-specific home advantage"""
        base_advantage = self.historical_edges[sport]['home_advantage']
        
        # Venue-specific adjustments
        if 'cameron indoor' in venue.lower():
            return base_advantage + 2  # Duke's Cameron Indoor
        elif 'rupp arena' in venue.lower():
            return base_advantage + 1.5  # Kentucky's Rupp Arena
        elif any(word in venue.lower() for word in ['dome', 'center', 'arena']):
            return base_advantage + 0.5  # Big venues
        
        return base_advantage
    
    def normalize_team_name(self, team_name):
        """Normalize team names for better matching"""
        # Remove common suffixes
        name = team_name.lower()
        for suffix in [' spartans', ' badgers', ' tar heels', ' blue devils', ' wildcats', 
                       ' panthers', ' cardinals', ' bears', ' red raiders', ' tigers', 
                       ' cyclones', ' jayhawks', ' bruins', ' wolverines', ' ramblers',
                       ' billikens', ' bobcats', ' redhawks', ' cougars', ' buckeyes',
                       ' razorbacks', ' bulldogs', ' broncos', ' gators', ' cornhuskers',
                       ' red storm', ' friars', ' aggies', ' commodores', ' boilermakers',
                       ' hawkeyes', ' fighting irish', ' yellow jackets', ' terriers',
                       ' bison', ' dolphins', ' eagles', ' midshipmen', ' raiders',
                       ' buccaneers', ' rams', ' horned frogs', ' cowboys', ' hoyas',
                       ' huskies', ' cavaliers']:
            name = name.replace(suffix, '')
        
        # Extract key identifiers
        name = name.strip()
        
        # Handle special cases
        if 'miami' in name and 'oh' in name:
            return 'miami oh'
        if 'saint louis' in name or 'st. louis' in name or 'st louis' in name:
            return 'saint louis'
        if 'loyola' in name and 'chi' in name:
            return 'loyola chicago'
        if 'michigan state' in name:
            return 'michigan state'
        if 'north carolina' in name:
            return 'north carolina'
        if 'ohio state' in name:
            return 'ohio state'
        if 'iowa state' in name:
            return 'iowa state'
        if 'kansas state' in name:
            return 'kansas state'
        if 'byu' in name:
            return 'byu'
        if 'uconn' in name or 'connecticut' in name:
            return 'uconn'
        if 'miami' in name and 'fl' not in name:
            return 'miami oh'
            
        return name
    
    def get_real_market_odds(self, game, prediction):
        """Get real market odds with fuzzy team matching"""
        home_team = game['home_team']
        away_team = game['away_team']
        sport = game['sport']
        
        # Normalize ESPN team names
        espn_home = self.normalize_team_name(home_team)
        espn_away = self.normalize_team_name(away_team)
        
        # Look for matching game in live odds data
        market_odds = None
        
        # Map sport codes
        sport_map = {
            'ncb': 'basketball_ncaab',
            'nba': 'basketball_nba',
            'mlb': 'baseball_mlb',
            'nfl': 'americanfootball_nfl'
        }
        
        target_sport = sport_map.get(sport, sport)
        
        if target_sport not in self.live_odds:
            # Fallback to simulated
            spread_noise = np.random.normal(0, 1.5)
            total_noise = np.random.normal(0, 2.0)
            
            return {
                'market_spread': round(prediction['predicted_spread'] + spread_noise, 1),
                'market_total': round(prediction['predicted_total'] + total_noise, 1),
                'source': 'simulated',
                'teams_flipped': False
            }
        
        for odds_game in self.live_odds[target_sport]:
            # Normalize odds API team names
            odds_home = self.normalize_team_name(odds_game['home_team'])
            odds_away = self.normalize_team_name(odds_game['away_team'])
            
            # Check if teams match
            if (espn_home in odds_home or odds_home in espn_home) and \
               (espn_away in odds_away or odds_away in espn_away):
                
                spreads = odds_game.get('spreads', {})
                totals = odds_game.get('totals', {})
                
                # Only print in non-Streamlit context
                import sys
                if 'streamlit' not in sys.modules:
                    print(f"✅ MATCH: {odds_game['away_team']} @ {odds_game['home_team']}")
                    print(f"   Spread: {spreads.get('home_spread')} / Total: {totals.get('over_total')} ({odds_game.get('bookmaker')})")
                
                market_odds = {
                    'market_spread': spreads.get('home_spread', 0),
                    'market_total': totals.get('over_total', 0),
                    'source': odds_game.get('bookmaker', 'unknown'),
                    'teams_flipped': False
                }
                break
        
        # Fallback to simulated odds if no real odds found
        if not market_odds:
            spread_noise = np.random.normal(0, 1.5)
            total_noise = np.random.normal(0, 2.0)
            
            market_odds = {
                'market_spread': round(prediction['predicted_spread'] + spread_noise, 1),
                'market_total': round(prediction['predicted_total'] + total_noise, 1),
                'source': 'simulated',
                'teams_flipped': False
            }
        
        return market_odds
    
    def find_value_bets(self, confidence_threshold=0.30, edge_threshold=0.5):
        """Find games and player props where our prediction differs significantly from market"""
        # First, collect live odds data
        print("📊 Collecting live odds data...")
        self.live_odds = self.odds_collector.collect_all_odds()
        
        # Find player prop values
        print("🏀 Analyzing player props...")
        props_analyzer = PlayerPropsAnalyzer()
        player_prop_values = props_analyzer.find_player_prop_values()
        
        games_df = self.get_todays_games()
        
        if games_df.empty and not player_prop_values:
            print("No games or player props found for analysis")
            return []
        
        value_bets = []
        
        # Only print in non-Streamlit context
        import sys
        if 'streamlit' not in sys.modules:
            print("🎯 Analyzing games for betting opportunities...")
            print("-" * 60)
        
        for sport in games_df['sport'].unique():
            sport_games = games_df[games_df['sport'] == sport]
            power_ratings = self.calculate_basic_power_ratings(sport)
            
            # Only print in non-Streamlit context
            import sys
            if 'streamlit' not in sys.modules:
                print(f"\n🏀 {sport.upper()} Analysis ({len(sport_games)} games)")
            
            for _, game in sport_games.iterrows():
                prediction = self.predict_game(game, power_ratings)
                market_odds = self.get_real_market_odds(game, prediction)
                
                # Calculate edges
                spread_edge = abs(prediction['predicted_spread'] - market_odds['market_spread'])
                total_edge = abs(prediction['predicted_total'] - market_odds['market_total'])
                
                game_analysis = {
                    'game_id': game['id'],
                    'sport': sport,
                    'matchup': f"{game['away_team']} @ {game['home_team']}",
                    'date': game['date'],
                    'prediction': prediction,
                    'market': market_odds,
                    'spread_edge': round(spread_edge, 1),
                    'total_edge': round(total_edge, 1),
                    'confidence': min(0.9, spread_edge / 5)  # Simple confidence metric
                }
                
                # Only print in non-Streamlit context
                import sys
                if 'streamlit' not in sys.modules:
                    print(f"  {game_analysis['matchup']}")
                    print(f"    Predicted spread: {prediction['predicted_spread']}")
                    print(f"    Market spread: {market_odds['market_spread']} (Edge: {spread_edge}) [{market_odds['source']}]")
                    print(f"    Predicted total: {prediction['predicted_total']}")
                    print(f"    Market total: {market_odds['market_total']} (Edge: {total_edge}) [{market_odds['source']}]")
                
                # Check if this qualifies as value bet
                if (spread_edge >= edge_threshold or total_edge >= edge_threshold) and \
                   game_analysis['confidence'] >= confidence_threshold:
                    
                    bet_type = 'spread' if spread_edge > total_edge else 'total'
                    value_bets.append({
                        **game_analysis,
                        'bet_type': bet_type,
                        'edge': max(spread_edge, total_edge)
                    })
                    # Only print in non-Streamlit context
                    import sys
                    if 'streamlit' not in sys.modules:
                        print(f"    🎰 VALUE BET FOUND! {bet_type.upper()} edge: {max(spread_edge, total_edge)}")
                
                # Only print in non-Streamlit context
                import sys
                if 'streamlit' not in sys.modules:
                    print()
        
        # Add player prop values to the results
        for prop in player_prop_values:
            if prop['confidence'] >= confidence_threshold and prop['edge'] >= edge_threshold:
                # Convert to same format as game bets
                value_bets.append({
                    'game_id': f"prop_{hash(prop['player'] + prop['prop_type'])}",
                    'matchup': f"{prop['player']} {prop['prop_type']} - {prop['game']}",
                    'bet_type': 'player_prop',
                    'edge': prop['edge'],
                    'confidence': prop['confidence'],
                    'prediction': {'projected_stat': prop['our_projection']},
                    'market': {'market_line': prop['market_line'], 'source': prop['bookmaker']},
                    'date': datetime.now().isoformat(),
                    'sport': 'player_props',
                    'prop_details': prop
                })
        
        return value_bets
    
    def display_value_summary(self, value_bets):
        """Display summary of value betting opportunities"""
        if not value_bets:
            print("❌ No value bets found with current criteria")
            return
            
        print(f"\n🎰 VALUE BETTING OPPORTUNITIES FOUND: {len(value_bets)}")
        print("=" * 80)
        
        for i, bet in enumerate(value_bets, 1):
            print(f"\n{i}. {bet['matchup']} ({bet['sport'].upper()})")
            print(f"   Bet Type: {bet['bet_type'].upper()}")
            print(f"   Edge: {bet['edge']} points")
            print(f"   Confidence: {bet['confidence']:.1%}")
            print(f"   Date: {bet['date']}")
        
        print(f"\n💡 Recommended daily action:")
        print(f"   - Place {len(value_bets)} value bets")
        print(f"   - Average edge: {np.mean([b['edge'] for b in value_bets]):.1f} points")
        print(f"   - Use Kelly criterion for bet sizing")

    def run_analysis(self):
        """Main analysis runner - AGGRESSIVE MODE"""
        print("🎰 LarlBot Betting Analysis Started!")
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔥 AGGRESSIVE MODE: Lower thresholds, more opportunities!")
        
        value_bets = self.find_value_bets(
            confidence_threshold=0.30,  # 30% confidence - more aggressive!
            edge_threshold=0.5         # 0.5+ point edge - catch smaller edges!
        )
        
        self.display_value_summary(value_bets)
        return value_bets

if __name__ == "__main__":
    analyzer = BettingAnalyzer()
    analyzer.run_analysis()