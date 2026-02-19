#!/usr/bin/env python3
"""
Quick betting analyzer using simplified team strength metrics
Works without needing full ESPN team database
"""

import requests
from datetime import datetime, timedelta

class QuickBettingAnalyzer:
    def __init__(self):
        self.team_stats_cache = {}
    
    def get_team_recent_games(self, team_name, days_back=14):
        """Get team's recent game results from ESPN scoreboard"""
        stats = {'wins': 0, 'losses': 0, 'avg_margin': 0, 'games': []}
        
        for days_ago in range(days_back):
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
            
            try:
                url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
                r = requests.get(url, params={'dates': date}, timeout=10)
                
                if r.status_code != 200:
                    continue
                
                data = r.json()
                
                for event in data.get('events', []):
                    comp = event['competitions'][0]
                    home = comp['competitors'][0]
                    away = comp['competitors'][1]
                    
                    home_name = home['team']['displayName']
                    away_name = away['team']['displayName']
                    
                    # Check if this team played
                    if team_name.lower() not in home_name.lower() and \
                       team_name.lower() not in away_name.lower():
                        continue
                    
                    # Get scores
                    if 'score' not in home or 'score' not in away:
                        continue
                    
                    home_score = int(home.get('score', 0))
                    away_score = int(away.get('score', 0))
                    
                    if home_score == 0 and away_score == 0:
                        continue
                    
                    # Determine if team won and margin
                    if team_name.lower() in home_name.lower():
                        won = home_score > away_score
                        margin = home_score - away_score
                    else:
                        won = away_score > home_score
                        margin = away_score - home_score
                    
                    if won:
                        stats['wins'] += 1
                    else:
                        stats['losses'] += 1
                    
                    stats['games'].append({
                        'date': date,
                        'won': won,
                        'margin': margin,
                        'score': f"{home_score}-{away_score}"
                    })
            
            except:
                continue
        
        # Calculate average margin
        if stats['games']:
            stats['avg_margin'] = sum(g['margin'] for g in stats['games']) / len(stats['games'])
            stats['win_pct'] = stats['wins'] / (stats['wins'] + stats['losses'])
        else:
            stats['avg_margin'] = 0
            stats['win_pct'] = 0.5
        
        return stats
    
    def predict_and_recommend(self, away_team, home_team, market_spread):
        """Predict game and make recommendation
        
        market_spread: negative = home favored (e.g., -7.5 means home favored by 7.5)
        """
        print(f"⚡ Analyzing {away_team} @ {home_team}...")
        
        # Get recent performance
        away_stats = self.get_team_recent_games(away_team)
        home_stats = self.get_team_recent_games(home_team)
        
        if not away_stats['games'] or not home_stats['games']:
            print(f"   ⚠️ Insufficient data")
            return None
        
        print(f"   Recent form: {away_team} ({away_stats['wins']}-{away_stats['losses']}, avg margin: {away_stats['avg_margin']:.1f})")
        print(f"   Recent form: {home_team} ({home_stats['wins']}-{home_stats['losses']}, avg margin: {home_stats['avg_margin']:.1f})")
        
        # Simple prediction: home advantage + form difference
        home_advantage = 4.0
        form_diff = home_stats['avg_margin'] - away_stats['avg_margin']
        predicted_spread = -(form_diff + home_advantage)  # Negative = home favored
        
        print(f"   Predicted: {home_team} {predicted_spread:.1f}")
        print(f"   Market: {home_team} {market_spread}")
        
        edge = abs(predicted_spread - market_spread)
        
        # Determine recommendation
        if predicted_spread < market_spread:
            # We think home is stronger
            rec = f"{home_team} {market_spread}"
            reason = f"{home_team} stronger than market thinks"
        else:
            # We think away is stronger
            rec = f"{away_team} +{abs(market_spread)}"
            reason = f"{away_team} better than market thinks"
        
        confidence = min(int(edge * 10 + 40), 85)
        
        return {
            'recommendation': rec,
            'edge': edge,
            'confidence': confidence,
            'reason': reason,
            'away_record': f"{away_stats['wins']}-{away_stats['losses']}",
            'home_record': f"{home_stats['wins']}-{home_stats['losses']}"
        }

if __name__ == "__main__":
    analyzer = QuickBettingAnalyzer()
    
    # Test on Kansas vs Iowa State
    result = analyzer.predict_and_recommend('Kansas', 'Iowa State', -7.5)
    
    if result:
        print(f"\n🎰 RECOMMENDATION: {result['recommendation']}")
        print(f"   Confidence: {result['confidence']}%")
        print(f"   Reason: {result['reason']}")
