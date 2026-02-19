#!/usr/bin/env python3
"""
LarlBot Smart Betting Analyzer 🎰
Data-driven picks using real team stats and intelligent analysis
"""

import requests
import json
from datetime import datetime, timedelta
from odds_collector import OddsCollector

class SmartBettingAnalyzer:
    def __init__(self):
        self.odds_collector = OddsCollector()
        self.team_cache = {}
        
    def normalize_team_name(self, name):
        """Normalize team names for matching"""
        # Convert to lowercase and strip
        name = name.lower().strip()
        
        # Common nickname mappings
        mappings = {
            'pitt': 'pittsburgh',
            'unc': 'north carolina',
            'ttu': 'texas tech',
            'isu': 'iowa state',
            'uk': 'kentucky',
            'uva': 'virginia',
            'vt': 'virginia tech',
            'fsu': 'florida state',
            'osu': 'ohio state',
            'msu': 'michigan state',
            'ku': 'kansas'
        }
        
        # Check if it's a known abbreviation
        for abbrev, full in mappings.items():
            if name == abbrev:
                return full
        
        # Remove common mascot suffixes to get school name
        suffixes = [
            ' jayhawks', ' cyclones', ' wildcats', ' tar heels', ' panthers',
            ' boilermakers', ' hawkeyes', ' red raiders', ' gators', ' blue devils',
            ' spartans', ' badgers', ' terrapins', ' hoosiers', ' wolverines',
            ' eagles', ' tigers', ' bulldogs', ' bears', ' cardinals', ' cowboys',
            ' aggies', ' huskies', ' ducks', ' trojans', ' bruins', ' sun devils',
            ' fighting irish', ' commodores', ' volunteers', ' crimson tide'
        ]
        
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name.replace(suffix, '').strip()
                break
        
        return name
    
    def get_team_stats(self, team_name, sport='ncb'):
        """Get real team statistics from ESPN"""
        cache_key = f"{sport}_{team_name}"
        if cache_key in self.team_cache:
            return self.team_cache[cache_key]
        
        # Search for team
        sport_map = {
            'ncb': 'mens-college-basketball',
            'nba': 'nba'
        }
        
        sport_path = sport_map.get(sport, 'mens-college-basketball')
        
        try:
            # Get team list
            url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/{sport_path}/teams'
            r = requests.get(url, timeout=10)
            
            if r.status_code != 200:
                return None
            
            data = r.json()
            teams = data['sports'][0]['leagues'][0]['teams']
            
            # Normalize search name
            search_name = self.normalize_team_name(team_name)
            
            # Find matching team - try multiple matching strategies
            team_id = None
            for team_data in teams:
                team = team_data['team']
                team_full = team['displayName'].lower()
                team_location = team.get('location', '').lower()
                team_nick = team.get('nickname', '').lower()
                
                # Try multiple matching strategies
                if search_name in team_full or \
                   team_location == search_name or \
                   search_name in team_location or \
                   team_nick in search_name:
                    team_id = team['id']
                    break
            
            if not team_id:
                return None
            
            # Get detailed team info
            url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/{sport_path}/teams/{team_id}'
            r = requests.get(url, timeout=10)
            
            if r.status_code != 200:
                return None
            
            team_data = r.json()['team']
            
            # Extract key stats
            record_items = team_data.get('record', {}).get('items', [])
            overall_record = None
            for item in record_items:
                if item.get('type') == 'total':
                    overall_record = item.get('summary', '0-0')
                    break
            
            if not overall_record:
                overall_record = record_items[0].get('summary', '0-0') if record_items else '0-0'
            
            wins, losses = map(int, overall_record.split('-'))
            win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0.5
            
            stats = {
                'name': team_data['displayName'],
                'record': overall_record,
                'wins': wins,
                'losses': losses,
                'win_pct': win_pct,
                'team_id': team_id
            }
            
            self.team_cache[cache_key] = stats
            return stats
            
        except Exception as e:
            print(f"   ⚠️ Error fetching stats for {team_name}: {e}")
            return None
    
    def predict_game_spread(self, away_team, home_team, sport='ncb'):
        """Predict game spread based on team strength
        
        Returns predicted spread from HOME team perspective
        Positive = home favored, Negative = away favored
        """
        away_stats = self.get_team_stats(away_team, sport)
        home_stats = self.get_team_stats(home_team, sport)
        
        if not away_stats or not home_stats:
            print(f"   ⚠️ Missing stats for {away_team} or {home_team}")
            return None, None
        
        # Calculate strength difference
        # Win percentage difference * 100 gives rough point spread
        strength_diff = (home_stats['win_pct'] - away_stats['win_pct']) * 100
        
        # Add home court advantage (NCAA ~4 points)
        home_advantage = 4.0 if sport == 'ncb' else 3.5
        
        predicted_spread = strength_diff + home_advantage
        
        # Get recent form (simplified - could enhance later)
        home_form_bonus = 0
        away_form_bonus = 0
        
        # Adjust for record strength
        if home_stats['wins'] > 20:
            home_form_bonus += 1
        if away_stats['wins'] > 20:
            away_form_bonus += 1
        
        predicted_spread += (home_form_bonus - away_form_bonus)
        
        # Return negative for home favorite (matches betting convention)
        # E.g., Home -7.5 means home favored by 7.5
        final_spread = -predicted_spread if predicted_spread > 0 else predicted_spread
        
        return round(final_spread, 1), {
            'home_stats': home_stats,
            'away_stats': away_stats,
            'strength_diff': strength_diff,
            'home_advantage': home_advantage
        }
    
    def analyze_bet(self, away_team, home_team, market_spread, sport='ncb'):
        """Analyze if there's a betting edge
        
        Args:
            market_spread: From HOME team perspective (e.g., -7.5 means home favored by 7.5)
        
        Returns:
            dict with recommendation
        """
        predicted_spread, analysis = self.predict_game_spread(away_team, home_team, sport)
        
        if predicted_spread is None:
            return None
        
        # Calculate edge
        edge = abs(predicted_spread - market_spread)
        
        # Determine which side to bet
        recommendation = None
        reason_parts = []
        
        # Key logic: Compare our prediction to market
        # If we predict home team STRONGER than market (more negative spread or less positive):
        #   -> Bet home team
        # If we predict home team WEAKER than market:
        #   -> Bet away team
        
        if predicted_spread < market_spread:
            # We think home team is STRONGER than market does
            # (More negative spread = bigger favorite)
            # Bet HOME team
            if market_spread < 0:
                recommendation = f"{home_team} {market_spread}"
            else:
                recommendation = f"{home_team} +{market_spread}"
            
            reason_parts.append(f"We predict {home_team} -{abs(predicted_spread):.1f}")
            reason_parts.append(f"Market only has them at {market_spread}")
            reason_parts.append(f"{home_team} stronger than market thinks by {edge:.1f} pts")
        
        else:
            # We think home team is WEAKER than market does
            # (Less negative spread or more positive = smaller favorite / bigger underdog)
            # Bet AWAY team
            if market_spread < 0:
                # Home is favored, so away gets points
                recommendation = f"{away_team} +{abs(market_spread)}"
            else:
                # Away is favored (market spread positive for home)
                recommendation = f"{away_team} {market_spread}"
            
            reason_parts.append(f"We predict {home_team} only {predicted_spread:.1f}")
            reason_parts.append(f"Market has them at {market_spread}")
            reason_parts.append(f"{away_team} better than market thinks by {edge:.1f} pts")
        
        # Calculate confidence based on edge and team records
        base_confidence = min(edge * 10, 80)  # 1 point edge = 10% confidence, max 80%
        
        # Boost confidence for teams with strong records
        home_record_quality = analysis['home_stats']['wins'] / (analysis['home_stats']['wins'] + analysis['home_stats']['losses'])
        away_record_quality = analysis['away_stats']['wins'] / (analysis['away_stats']['wins'] + analysis['away_stats']['losses'])
        avg_quality = (home_record_quality + away_record_quality) / 2
        
        if avg_quality > 0.6:
            base_confidence += 5
        
        confidence = min(base_confidence, 85)
        
        return {
            'recommendation': recommendation,
            'edge': round(edge, 1),
            'confidence': int(confidence),
            'predicted_spread': predicted_spread,
            'market_spread': market_spread,
            'reason': ' | '.join(reason_parts),
            'home_record': analysis['home_stats']['record'],
            'away_record': analysis['away_stats']['record']
        }
    
    def get_todays_recommendations(self, min_edge=2.0, min_confidence=40):
        """Get today's value betting recommendations"""
        print("🎰 LarlBot Smart Betting Analysis")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Get today's games with odds
        print("📊 Collecting odds data...")
        odds_data = self.odds_collector.collect_all_odds()
        
        recommendations = []
        
        # Analyze NCAA Basketball games
        if 'basketball_ncaab' in odds_data:
            print(f"\n🏀 Analyzing {len(odds_data['basketball_ncaab'])} NCAA Basketball games...\n")
            
            for game in odds_data['basketball_ncaab'][:20]:  # Limit to avoid API spam
                away_team = game['away_team']
                home_team = game['home_team']
                
                spreads = game.get('spreads', {})
                if not spreads or not spreads.get('home_spread'):
                    continue
                
                market_spread = spreads['home_spread']
                bookmaker = game.get('bookmaker', 'Unknown')
                
                print(f"⚡ {away_team} @ {home_team}")
                print(f"   Market: {home_team} {market_spread} ({bookmaker})")
                
                analysis = self.analyze_bet(away_team, home_team, market_spread, sport='ncb')
                
                if analysis:
                    print(f"   Prediction: {home_team} {analysis['predicted_spread']}")
                    print(f"   Edge: {analysis['edge']} points")
                    print(f"   Confidence: {analysis['confidence']}%")
                    
                    if analysis['edge'] >= min_edge and analysis['confidence'] >= min_confidence:
                        print(f"   🎰 VALUE BET: {analysis['recommendation']}")
                        recommendations.append({
                            'game': f"{away_team} @ {home_team}",
                            'sport': 'NCAA Basketball',
                            'recommendation': analysis['recommendation'],
                            'edge': analysis['edge'],
                            'confidence': analysis['confidence'],
                            'reason': analysis['reason'],
                            'home_record': analysis['home_record'],
                            'away_record': analysis['away_record'],
                            'bookmaker': bookmaker,
                            'market_line': f"{home_team} {market_spread}"
                        })
                    print()
        
        print(f"\n{'='*80}")
        print(f"🎰 FOUND {len(recommendations)} VALUE BETS")
        print(f"{'='*80}\n")
        
        for i, bet in enumerate(recommendations, 1):
            print(f"{i}. {bet['game']}")
            print(f"   BET: {bet['recommendation']}")
            print(f"   Edge: {bet['edge']} pts | Confidence: {bet['confidence']}%")
            print(f"   Records: Home {bet['home_record']} | Away {bet['away_record']}")
            print(f"   {bet['reason']}")
            print()
        
        return recommendations

if __name__ == "__main__":
    analyzer = SmartBettingAnalyzer()
    recommendations = analyzer.get_todays_recommendations(min_edge=2.0, min_confidence=40)
