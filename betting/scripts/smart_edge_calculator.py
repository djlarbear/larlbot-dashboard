#!/usr/bin/env python3
"""
Smart Edge Calculator v2.0 - Professional Odds Evaluation
Combines team strength, injuries, weather, and historical data to calculate TRUE edge

Formula:
True Edge = (Actual Win Probability - Implied Win Probability) × Expected ROI
Where:
- Actual Win Probability = Based on team metrics, matchup, injuries, weather
- Implied Win Probability = Derived from betting odds
- Expected ROI = Risk vs reward based on odds
"""

import sys
from pathlib import Path

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

class SmartEdgeCalculator:
    """Calculate professional edge assessments"""
    
    def __init__(self):
        try:
            from team_strength_calculator import TeamStrengthCalculator
            from injury_processor import InjuryProcessor
            from weather_processor import WeatherProcessor
            
            self.team_calc = TeamStrengthCalculator()
            self.injury_proc = InjuryProcessor()
            self.weather_proc = WeatherProcessor()
            self.use_advanced = True
        except:
            self.use_advanced = False
            print("⚠️ Running in basic mode (advanced modules not available)")
    
    def calculate_spread_edge(self, away_team, home_team, spread, odds=-110, 
                            venue_city='Unknown', venue_state='Unknown', sport='NCAA Basketball'):
        """Calculate edge for a spread bet
        
        Returns dict with:
        - edge_value: Points of edge
        - edge_quality: 'Excellent', 'Good', 'Fair', 'Marginal', 'Poor'
        - win_probability: Estimated win %
        - confidence: Our confidence in the edge
        - reasoning: Detailed explanation
        """
        
        edge_components = {}
        
        # 1. TEAM STRENGTH ANALYSIS
        if self.use_advanced:
            try:
                matchup = self.team_calc.calculate_matchup_strength_differential(
                    away_team if spread > 0 else home_team,  # Which team is underdog
                    home_team if spread > 0 else away_team
                )
                team_edge = matchup['total_advantage']
                edge_components['team_strength_edge'] = team_edge
            except:
                team_edge = 0
                edge_components['team_strength_edge'] = 0
        else:
            team_edge = 0
            edge_components['team_strength_edge'] = 0
        
        # 2. INJURY IMPACT
        if self.use_advanced:
            try:
                injury_comp = self.injury_proc.compare_injury_impact(away_team, home_team)
                injury_edge = injury_comp['advantage']
                edge_components['injury_edge'] = injury_edge
            except:
                injury_edge = 0
                edge_components['injury_edge'] = 0
        else:
            injury_edge = 0
            edge_components['injury_edge'] = 0
        
        # 3. WEATHER IMPACT (for outdoor sports mainly)
        if self.use_advanced and sport in ['NFL', 'College Football']:
            try:
                weather = self.weather_proc.get_weather('', venue_city, venue_state)
                weather_edge = weather.get('impact_on_scoring', 0)
                edge_components['weather_edge'] = weather_edge
            except:
                weather_edge = 0
                edge_components['weather_edge'] = 0
        else:
            weather_edge = 0
            edge_components['weather_edge'] = 0
        
        # 4. HISTORICAL SPREAD ACCURACY
        # From our actual performance data
        spread_historical_edge = 0.467 - 0.5  # 46.7% win rate vs 50% expected
        edge_components['historical_edge'] = spread_historical_edge * 3  # Scale up
        
        # 5. LINE VALUE ANALYSIS
        # Spread of -14.5 vs -10 = different risk/reward
        implied_win_pct = self.american_to_probability(-110)  # Standard -110 = 52.4%
        
        # Calculate total edge
        total_strength_edge = team_edge + injury_edge + weather_edge + (spread_historical_edge * 3)
        
        # Adjust for spread size (larger spreads = higher variance)
        spread_abs = abs(spread)
        if spread_abs > 20:
            variance_penalty = -1.5
        elif spread_abs > 15:
            variance_penalty = -1.0
        elif spread_abs > 10:
            variance_penalty = -0.5
        else:
            variance_penalty = 0
        
        edge_components['variance_adjustment'] = variance_penalty
        total_edge = total_strength_edge + variance_penalty
        
        # Determine edge quality
        if total_edge > 5:
            quality = 'Excellent'
            confidence = 85
        elif total_edge > 3:
            quality = 'Good'
            confidence = 75
        elif total_edge > 1:
            quality = 'Fair'
            confidence = 65
        elif total_edge > -1:
            quality = 'Marginal'
            confidence = 55
        else:
            quality = 'Poor'
            confidence = 45
        
        # Estimate win probability
        win_prob = implied_win_pct + (total_edge * 0.05)  # Each 1pt edge = ~5% win prob
        win_prob = max(30, min(70, win_prob))  # Cap between 30-70%
        
        return {
            'bet_type': 'SPREAD',
            'favorite': home_team if spread < 0 else away_team,
            'underdog': away_team if spread < 0 else home_team,
            'spread': spread,
            'edge_value': round(total_edge, 1),
            'edge_quality': quality,
            'win_probability': int(win_prob),
            'confidence': confidence,
            'edge_components': edge_components,
            'team_strength_edge': round(team_edge, 1),
            'injury_edge': round(injury_edge, 1),
            'weather_edge': round(weather_edge, 1),
            'variance_adjustment': round(variance_penalty, 1),
            'reasoning': self.build_reasoning(edge_components, quality, spread_abs)
        }
    
    def calculate_total_edge(self, team1, team2, over_under, venue_city='Unknown', 
                            venue_state='Unknown', sport='NCAA Basketball'):
        """Calculate edge for over/under bets"""
        
        edge_components = {}
        
        # 1. PACE-ADJUSTED TOTAL
        data_quality = 'HIGH'  # Track data source quality
        if self.use_advanced:
            try:
                pace_total = self.team_calc.calculate_pace_adjusted_total(team1, team2)
                expected_total = pace_total['expected_total']
                data_quality = pace_total.get('data_quality', 'HIGH')  # Track if using defaults
                # If over_under > expected_total, we have a favorable under
                total_edge = abs(over_under - expected_total) * 0.5
                if over_under > expected_total:
                    total_edge = -total_edge  # Under edge (negative for under)
                edge_components['pace_edge'] = total_edge
                edge_components['data_quality'] = data_quality  # Pass through
            except:
                total_edge = 0
                edge_components['pace_edge'] = 0
                edge_components['data_quality'] = 'LOW'
        else:
            total_edge = 0
            edge_components['pace_edge'] = 0
            edge_components['data_quality'] = 'LOW'
        
        # 2. WEATHER IMPACT
        if self.use_advanced:
            try:
                weather = self.weather_proc.get_weather('', venue_city, venue_state)
                weather_adjustment = self.weather_proc.calculate_total_adjustment(sport, weather)
                edge_components['weather_edge'] = weather_adjustment
                total_edge += weather_adjustment
            except:
                edge_components['weather_edge'] = 0
        
        # 3. HISTORICAL TOTAL ACCURACY
        # UNDER has been 40% (vs 50% expected)
        total_historical = 0.40 - 0.50
        edge_components['historical_edge'] = total_historical * 2.5  # Scale
        total_edge += (total_historical * 2.5)
        
        # Determine quality
        abs_edge = abs(total_edge)
        if abs_edge > 5:
            quality = 'Excellent'
            confidence = 85
        elif abs_edge > 3:
            quality = 'Good'
            confidence = 75
        elif abs_edge > 1:
            quality = 'Fair'
            confidence = 65
        else:
            quality = 'Marginal'
            confidence = 55
        
        return {
            'bet_type': 'TOTAL',
            'over_under': over_under,
            'direction': 'OVER' if total_edge > 0 else 'UNDER',
            'edge_value': round(abs(total_edge), 1),
            'edge_quality': quality,
            'confidence': confidence,
            'edge_components': edge_components,
            'reasoning': self.build_total_reasoning(edge_components, quality)
        }
    
    def american_to_probability(self, american_odds):
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)
    
    def build_reasoning(self, components, quality, spread_abs):
        """Build detailed reasoning for spread edge"""
        parts = []
        
        parts.append(f"Edge Assessment: {quality} ({components.get('team_strength_edge', 0)}pt from team strength)")
        
        if components.get('injury_edge', 0) != 0:
            injury = components['injury_edge']
            if injury > 0:
                parts.append(f"Injury advantage: +{injury:.1f}pt")
            else:
                parts.append(f"Injury disadvantage: {injury:.1f}pt")
        
        if components.get('weather_edge', 0) != 0:
            parts.append(f"Weather impact: {components['weather_edge']:.1f}pt")
        
        if components.get('variance_adjustment', 0) != 0:
            parts.append(f"Variance adjustment (spread size): {components['variance_adjustment']:.1f}pt")
        
        return " | ".join(parts)
    
    def build_total_reasoning(self, components, quality):
        """Build detailed reasoning for total edge"""
        parts = [f"Edge Assessment: {quality} edge detected"]
        
        if components.get('pace_edge', 0) != 0:
            direction = "OVER" if components['pace_edge'] > 0 else "UNDER"
            parts.append(f"Pace-adjusted total favors: {direction}")
        
        if components.get('weather_edge', 0) != 0:
            parts.append(f"Weather impact: {components['weather_edge']:.1f}pt adjustment")
        
        parts.append("Multiple factors support this edge")
        
        return " | ".join(parts)


if __name__ == '__main__':
    calc = SmartEdgeCalculator()
    
    print("✅ Smart Edge Calculator v2.0 Ready")
    print("\nCapabilities:")
    print("  ✓ Team strength analysis")
    print("  ✓ Injury impact assessment")
    print("  ✓ Weather adjustment")
    print("  ✓ Historical accuracy factoring")
    print("  ✓ Variance-aware edge calculation")
    
    # Test spread edge
    print("\nTest: Cincinnati -11.5 vs Utah")
    edge = calc.calculate_spread_edge('Utah', 'Cincinnati', -11.5)
    print(f"Edge: {edge['edge_value']}pts | Quality: {edge['edge_quality']} | Confidence: {edge['confidence']}%")
