#!/usr/bin/env python3
"""
Advanced Betting Model - Multi-Tier Risk Analysis
Finds both conservative value bets and high-risk opportunities
"""

import requests
from datetime import datetime, timedelta
import pytz
import statistics

class AdvancedBettingModel:
    def __init__(self):
        self.est = pytz.timezone('America/New_York')
        
    def get_team_recent_games(self, team_name, days_back=21):
        """Get team's last 3 weeks of games for deeper analysis"""
        games = []
        
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
                    
                    # Determine if team was home/away and result
                    is_home = team_name.lower() in home_name.lower()
                    
                    if is_home:
                        team_score = home_score
                        opp_score = away_score
                        opponent = away_name
                    else:
                        team_score = away_score
                        opp_score = home_score
                        opponent = home_name
                    
                    won = team_score > opp_score
                    margin = team_score - opp_score
                    
                    games.append({
                        'date': date,
                        'won': won,
                        'margin': margin,
                        'team_score': team_score,
                        'opp_score': opp_score,
                        'opponent': opponent,
                        'is_home': is_home,
                        'total_points': team_score + opp_score
                    })
            
            except:
                continue
        
        return games
    
    def calculate_advanced_metrics(self, games):
        """Calculate advanced statistical metrics"""
        if not games:
            return None
        
        wins = sum(1 for g in games if g['won'])
        losses = len(games) - wins
        
        # Basic stats
        avg_margin = statistics.mean(g['margin'] for g in games)
        avg_points_for = statistics.mean(g['team_score'] for g in games)
        avg_points_against = statistics.mean(g['opp_score'] for g in games)
        
        # Home/Away splits
        home_games = [g for g in games if g['is_home']]
        away_games = [g for g in games if not g['is_home']]
        
        home_margin = statistics.mean(g['margin'] for g in home_games) if home_games else 0
        away_margin = statistics.mean(g['margin'] for g in away_games) if away_games else 0
        
        # Recent form (last 5 games)
        recent_games = games[:5]
        recent_wins = sum(1 for g in recent_games if g['won'])
        recent_form = recent_wins / len(recent_games)
        
        # Consistency (standard deviation of margins)
        consistency = statistics.stdev(g['margin'] for g in games) if len(games) > 1 else 0
        
        # Scoring trends
        avg_total = statistics.mean(g['total_points'] for g in games)
        
        return {
            'games_played': len(games),
            'wins': wins,
            'losses': losses,
            'win_pct': wins / len(games),
            'avg_margin': avg_margin,
            'avg_points_for': avg_points_for,
            'avg_points_against': avg_points_against,
            'home_margin': home_margin,
            'away_margin': away_margin,
            'recent_form': recent_form,
            'consistency': consistency,
            'avg_total': avg_total,
            'home_games': len(home_games),
            'away_games': len(away_games)
        }
    
    def analyze_matchup(self, away_team, home_team, market_spread):
        """Deep matchup analysis with risk assessment"""
        print(f"\n⚡ Analyzing {away_team} @ {home_team}")
        
        # Get recent games
        away_games = self.get_team_recent_games(away_team)
        home_games = self.get_team_recent_games(home_team)
        
        if not away_games or not home_games:
            print("   ⚠️ Insufficient data")
            return None
        
        # Calculate metrics
        away_metrics = self.calculate_advanced_metrics(away_games)
        home_metrics = self.calculate_advanced_metrics(home_games)
        
        print(f"   {away_team}: {away_metrics['wins']}-{away_metrics['losses']} | {away_metrics['avg_margin']:.1f} margin | {away_metrics['recent_form']:.0%} recent")
        print(f"   {home_team}: {home_metrics['wins']}-{home_metrics['losses']} | {home_metrics['avg_margin']:.1f} margin | {home_metrics['recent_form']:.0%} recent")
        
        # Predict spread
        # Factor 1: Overall strength (margin differential)
        margin_diff = home_metrics['avg_margin'] - away_metrics['avg_margin']
        
        # Factor 2: Home court advantage (varies by team)
        home_advantage = 4.0  # Base
        home_advantage += (home_metrics['home_margin'] - home_metrics['away_margin']) * 0.3
        
        # Factor 3: Recent form adjustment
        form_diff = home_metrics['recent_form'] - away_metrics['recent_form']
        form_adjustment = form_diff * 5  # Up to ±5 points
        
        # Factor 4: Consistency (less consistent = more risk)
        consistency_factor = (home_metrics['consistency'] + away_metrics['consistency']) / 2
        
        # Predicted spread (negative = home favored)
        predicted_spread = -(margin_diff + home_advantage + form_adjustment)
        
        print(f"   Market: {home_team} {market_spread}")
        print(f"   Prediction: {home_team} {predicted_spread:.1f}")
        
        # Calculate edge
        edge = abs(predicted_spread - market_spread)
        
        # Determine recommendation
        if predicted_spread < market_spread:
            # We think home is stronger
            rec_team = home_team
            rec_spread = market_spread
        else:
            # We think away is stronger
            rec_team = away_team
            rec_spread = abs(market_spread)
        
        # Calculate confidence based on multiple factors
        base_confidence = min(edge * 8, 70)
        
        # Boost for good recent form
        if away_metrics['recent_form'] > 0.6 or home_metrics['recent_form'] > 0.6:
            base_confidence += 10
        
        # Reduce for high inconsistency
        if consistency_factor > 15:
            base_confidence -= 10
        
        confidence = max(35, min(base_confidence, 90))
        
        # Risk tier classification
        if edge < 3:
            risk_tier = "LOW RISK"
            tier_color = "🟢"
        elif edge < 6:
            risk_tier = "MODERATE RISK"
            tier_color = "🟡"
        else:
            risk_tier = "HIGH RISK"
            tier_color = "🔴"
        
        # Expected value calculation
        implied_win_prob = confidence / 100
        # Assuming -110 odds, need 52.4% to break even
        ev = (implied_win_prob * 100) - ((1 - implied_win_prob) * 110)
        
        recommendation = f"{rec_team} {'+' if predicted_spread > market_spread else ''}{rec_spread if predicted_spread > market_spread else market_spread}"
        
        return {
            'away_team': away_team,
            'home_team': home_team,
            'recommendation': recommendation,
            'edge': round(edge, 1),
            'confidence': int(confidence),
            'risk_tier': risk_tier,
            'tier_color': tier_color,
            'predicted_spread': round(predicted_spread, 1),
            'market_spread': market_spread,
            'expected_value': round(ev, 1),
            'away_metrics': away_metrics,
            'home_metrics': home_metrics,
            'consistency': consistency_factor
        }
    
    def generate_tiered_recommendations(self, min_edge=1.5):
        """Generate recommendations across all risk tiers"""
        from odds_collector import OddsCollector
        
        print("🎰 Advanced Betting Model - Multi-Tier Analysis")
        print(f"📅 {datetime.now(self.est).strftime('%Y-%m-%d %I:%M %p EST')}\n")
        
        collector = OddsCollector()
        odds_data = collector.collect_all_odds()
        
        all_picks = []
        
        if 'basketball_ncaab' in odds_data:
            games = odds_data['basketball_ncaab'][:25]
            
            print(f"🏀 Analyzing {len(games)} NCAA Basketball games...\n")
            
            for game in games:
                away = game['away_team']
                home = game['home_team']
                spreads = game.get('spreads', {})
                
                if not spreads or not spreads.get('home_spread'):
                    continue
                
                market_spread = spreads['home_spread']
                
                analysis = self.analyze_matchup(away, home, market_spread)
                
                if analysis and analysis['edge'] >= min_edge:
                    all_picks.append({
                        'game': f"{away} @ {home}",
                        'recommendation': analysis['recommendation'],
                        'confidence': analysis['confidence'],
                        'edge': analysis['edge'],
                        'risk_tier': analysis['risk_tier'],
                        'tier_color': analysis['tier_color'],
                        'expected_value': analysis['expected_value'],
                        'bookmaker': game.get('bookmaker', 'fanduel'),
                        'market_line': f"{home.split()[0]} {market_spread}"
                    })
        
        # Sort by edge (highest first)
        all_picks.sort(key=lambda x: x['edge'], reverse=True)
        
        # Categorize by risk tier
        low_risk = [p for p in all_picks if 'LOW' in p['risk_tier']]
        mod_risk = [p for p in all_picks if 'MODERATE' in p['risk_tier']]
        high_risk = [p for p in all_picks if 'HIGH' in p['risk_tier']]
        
        print(f"\n{'='*80}")
        print(f"🎯 BETTING RECOMMENDATIONS BY RISK TIER")
        print(f"{'='*80}\n")
        
        print(f"🟢 LOW RISK PICKS (High confidence, smaller edges): {len(low_risk)}")
        for i, pick in enumerate(low_risk[:5], 1):
            print(f"  {i}. {pick['recommendation']} | Edge: {pick['edge']} | Conf: {pick['confidence']}% | EV: {pick['expected_value']:+.0f}")
        
        print(f"\n🟡 MODERATE RISK PICKS (Balanced risk/reward): {len(mod_risk)}")
        for i, pick in enumerate(mod_risk[:5], 1):
            print(f"  {i}. {pick['recommendation']} | Edge: {pick['edge']} | Conf: {pick['confidence']}% | EV: {pick['expected_value']:+.0f}")
        
        print(f"\n🔴 HIGH RISK PICKS (Big edges, higher variance): {len(high_risk)}")
        for i, pick in enumerate(high_risk[:5], 1):
            print(f"  {i}. {pick['recommendation']} | Edge: {pick['edge']} | Conf: {pick['confidence']}% | EV: {pick['expected_value']:+.0f}")
        
        return {
            'low_risk': low_risk,
            'moderate_risk': mod_risk,
            'high_risk': high_risk,
            'all_picks': all_picks
        }

if __name__ == "__main__":
    model = AdvancedBettingModel()
    recommendations = model.generate_tiered_recommendations(min_edge=1.5)
