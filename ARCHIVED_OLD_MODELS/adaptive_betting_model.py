#!/usr/bin/env python3
"""
Adaptive Betting Model v1.0
Integrates learning insights to dynamically adjust betting strategy

Features:
- Loads learning_insights.json from learning engine
- Adjusts confidence thresholds based on historical calibration
- Adjusts edge requirements based on actual profitability
- Reduces exposure to unprofitable patterns
- Increases exposure to profitable patterns
- Updates daily_recommendations.py with adaptive filters
"""

import json
import os

class AdaptiveBettingModel:
    def __init__(self):
        self.learning_file = 'learning_insights.json'
        self.insights = None
        self.default_thresholds = {
            'min_confidence': 70,
            'min_edge': 2.0,
            'max_high_risk_pct': 20,
            'min_bets_for_learning': 10  # Need at least 10 bets to adjust
        }
        self.load_insights()
    
    def load_insights(self):
        """Load learning insights if available"""
        try:
            if os.path.exists(self.learning_file):
                with open(self.learning_file, 'r') as f:
                    self.insights = json.load(f)
                return True
        except:
            pass
        return False
    
    def get_thresholds(self):
        """Get current thresholds (adaptive if enough data, default otherwise)"""
        if not self.insights:
            return self.default_thresholds
        
        total_bets = self.insights.get('total_bets_analyzed', 0)
        
        # Need minimum sample size to trust insights
        if total_bets < self.default_thresholds['min_bets_for_learning']:
            return self.default_thresholds
        
        # Use learned optimal thresholds
        optimal = self.insights.get('optimal_thresholds', {})
        return {
            'min_confidence': optimal.get('min_confidence', self.default_thresholds['min_confidence']),
            'min_edge': optimal.get('min_edge', self.default_thresholds['min_edge']),
            'max_high_risk_pct': optimal.get('max_high_risk_pct', self.default_thresholds['max_high_risk_pct']),
            'min_bets_for_learning': self.default_thresholds['min_bets_for_learning']
        }
    
    def should_reduce_bet_type(self, bet_type):
        """Check if a bet type should be reduced based on performance"""
        if not self.insights:
            return False
        
        by_bet_type = self.insights.get('by_bet_type', {})
        stats = by_bet_type.get(bet_type, {})
        
        # Reduce if win rate < 50% and sample size >= 5
        if stats.get('total', 0) >= 5 and stats.get('win_rate', 100) < 50:
            return True
        
        return False
    
    def should_increase_bet_type(self, bet_type):
        """Check if a bet type should be increased based on performance"""
        if not self.insights:
            return False
        
        by_bet_type = self.insights.get('by_bet_type', {})
        stats = by_bet_type.get(bet_type, {})
        
        # Increase if win rate > 75% and sample size >= 3
        if stats.get('total', 0) >= 3 and stats.get('win_rate', 0) > 75:
            return True
        
        return False
    
    def should_reduce_sport(self, sport):
        """Check if a sport should be reduced based on performance"""
        if not self.insights:
            return False
        
        sport = sport.replace('🏀 ', '').replace('🏈 ', '').replace('⚾ ', '').strip()
        
        by_sport = self.insights.get('by_sport', {})
        stats = by_sport.get(sport, {})
        overall_win_rate = self.insights.get('overall_win_rate', 70)
        
        # Reduce if win rate < overall - 15% and sample size >= 5
        if stats.get('total', 0) >= 5 and stats.get('win_rate', 100) < overall_win_rate - 15:
            return True
        
        return False
    
    def get_sport_priority(self, sport):
        """Get priority multiplier for sport (1.0 = normal, >1.0 = increase, <1.0 = decrease)"""
        if not self.insights:
            return 1.0
        
        sport = sport.replace('🏀 ', '').replace('🏈 ', '').replace('⚾ ', '').strip()
        
        by_sport = self.insights.get('by_sport', {})
        stats = by_sport.get(sport, {})
        overall_win_rate = self.insights.get('overall_win_rate', 70)
        
        if not stats or stats.get('total', 0) < 3:
            return 1.0  # Not enough data
        
        sport_win_rate = stats.get('win_rate', overall_win_rate)
        
        # Calculate priority based on performance vs average
        diff = sport_win_rate - overall_win_rate
        
        if diff > 15:
            return 1.5  # High priority (50% more picks)
        elif diff > 5:
            return 1.2  # Medium priority (20% more picks)
        elif diff < -15:
            return 0.5  # Low priority (50% fewer picks)
        elif diff < -5:
            return 0.8  # Reduced priority (20% fewer picks)
        else:
            return 1.0  # Normal priority
    
    def adjust_confidence(self, original_confidence, bet_type, sport):
        """Adjust confidence based on historical calibration"""
        if not self.insights:
            return original_confidence
        
        # Check confidence bucket performance
        by_confidence = self.insights.get('by_confidence', {})
        
        # Find which bucket this falls into
        if original_confidence >= 90:
            bucket = '90-100%'
        elif original_confidence >= 80:
            bucket = '80-89%'
        elif original_confidence >= 70:
            bucket = '70-79%'
        elif original_confidence >= 60:
            bucket = '60-69%'
        else:
            bucket = '50-59%'
        
        bucket_stats = by_confidence.get(bucket, {})
        
        if bucket_stats.get('total', 0) >= 3:
            actual_win_rate = bucket_stats.get('win_rate', original_confidence)
            expected_win_rate = int(bucket.split('-')[0].replace('%', ''))
            
            # If model is overconfident, reduce confidence
            if actual_win_rate < expected_win_rate - 10:
                adjustment = -10
                return max(50, original_confidence + adjustment)
        
        # Check bet type performance
        by_bet_type = self.insights.get('by_bet_type', {})
        bet_stats = by_bet_type.get(bet_type, {})
        
        if bet_stats.get('total', 0) >= 5:
            if bet_stats.get('win_rate', 100) < 50:
                # Small confidence reduction for underperforming bet types (not eliminate)
                return max(60, original_confidence - 8)  # Smaller penalty, learn but still bet
        
        return original_confidence
    
    def filter_picks(self, picks):
        """Enhance and prioritize picks based on learning insights (DON'T filter out bet types)"""
        if not self.insights or not picks:
            return picks
        
        thresholds = self.get_thresholds()
        enhanced_picks = []
        
        for pick in picks:
            bet_type = pick.get('bet_type', '').upper()
            sport = pick.get('sport', '')
            
            # Store original values
            pick['original_confidence'] = pick.get('confidence', 70)
            pick['original_edge'] = pick.get('edge', 0)
            
            # Adjust confidence based on historical performance
            adjusted_confidence = self.adjust_confidence(
                pick.get('confidence', 70),
                bet_type,
                sport
            )
            pick['confidence'] = adjusted_confidence
            
            # Add learning-based priority score
            by_bet_type = self.insights.get('by_bet_type', {})
            bet_stats = by_bet_type.get(bet_type, {})
            
            if bet_stats.get('total', 0) >= 3:
                historical_win_rate = bet_stats.get('win_rate', 50)
                # Boost or penalize edge based on historical performance
                if historical_win_rate > 70:
                    pick['edge'] = pick.get('edge', 0) * 1.2  # Boost edge by 20%
                    pick['learning_boost'] = '+20% (proven winner)'
                elif historical_win_rate < 50:
                    pick['edge'] = pick.get('edge', 0) * 0.8  # Reduce edge by 20%
                    pick['learning_boost'] = '-20% (needs improvement)'
                else:
                    pick['learning_boost'] = 'neutral'
            else:
                pick['learning_boost'] = 'insufficient data'
            
            # Add sport-based priority
            sport_priority = self.get_sport_priority(sport)
            if sport_priority > 1.0:
                pick['sport_priority'] = f'HIGH ({sport_priority}x)'
            elif sport_priority < 1.0:
                pick['sport_priority'] = f'LOW ({sport_priority}x)'
            else:
                pick['sport_priority'] = 'NORMAL'
            
            # Calculate composite score (confidence * edge * sport_priority)
            pick['learning_score'] = pick.get('confidence', 0) * pick.get('edge', 0) * sport_priority
            
            # Add learning metadata
            pick['learning_applied'] = True
            pick['thresholds_used'] = thresholds
            
            # Add recommendation on HOW to bet this type better
            if bet_stats.get('total', 0) >= 3:
                historical_wr = bet_stats.get('win_rate', 50)
                if historical_wr < 50:
                    pick['learning_advice'] = f'{bet_type}: {historical_wr:.0f}% historical - bet smaller or improve edge requirement'
                elif historical_wr > 75:
                    pick['learning_advice'] = f'{bet_type}: {historical_wr:.0f}% historical - increase bet size!'
                else:
                    pick['learning_advice'] = f'{bet_type}: {historical_wr:.0f}% historical - continue current strategy'
            
            enhanced_picks.append(pick)
        
        # Sort by learning score (best picks first)
        enhanced_picks.sort(key=lambda x: x.get('learning_score', 0), reverse=True)
        
        return enhanced_picks
    
    def get_status(self):
        """Get current adaptive model status"""
        if not self.insights:
            return {
                'status': 'DEFAULT',
                'message': 'Using default thresholds (no learning data yet)',
                'thresholds': self.default_thresholds
            }
        
        total_bets = self.insights.get('total_bets_analyzed', 0)
        if total_bets < self.default_thresholds['min_bets_for_learning']:
            return {
                'status': 'LEARNING',
                'message': f'Collecting data ({total_bets}/{self.default_thresholds["min_bets_for_learning"]} bets)',
                'thresholds': self.default_thresholds
            }
        
        thresholds = self.get_thresholds()
        recommendations = self.insights.get('recommendations', [])
        
        return {
            'status': 'ADAPTIVE',
            'message': f'Learning from {total_bets} completed bets',
            'thresholds': thresholds,
            'recommendations': recommendations[:3],  # Top 3
            'overall_win_rate': self.insights.get('overall_win_rate', 0)
        }

# Convenience functions for daily_recommendations.py integration
def get_adaptive_thresholds():
    """Get current adaptive thresholds"""
    model = AdaptiveBettingModel()
    return model.get_thresholds()

def apply_learning_filter(picks):
    """Apply learning-based filter to picks"""
    model = AdaptiveBettingModel()
    return model.filter_picks(picks)

def get_learning_status():
    """Get current learning status"""
    model = AdaptiveBettingModel()
    return model.get_status()

if __name__ == '__main__':
    # Test the adaptive model
    model = AdaptiveBettingModel()
    status = model.get_status()
    
    print("\n" + "=" * 60)
    print("🧠 Adaptive Betting Model Status")
    print("=" * 60)
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    print("\nCurrent Thresholds:")
    for key, value in status['thresholds'].items():
        if key != 'min_bets_for_learning':
            print(f"  • {key}: {value}")
    
    if status.get('recommendations'):
        print("\nTop Recommendations:")
        for i, rec in enumerate(status['recommendations'], 1):
            print(f"  {i}. [{rec['priority']}] {rec['action']}")
    
    print("=" * 60)
