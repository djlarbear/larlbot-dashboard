#!/usr/bin/env python3
"""
LarlBot Learning Engine v1.0
Analyzes past betting performance and generates insights to improve future picks

Features:
- Analyzes wins/losses by sport, bet type, risk tier, confidence level
- Identifies profitable patterns and unprofitable ones
- Calculates optimal thresholds (edge, confidence, risk)
- Generates actionable recommendations for model tuning
- Saves learning insights to learning_insights.json
"""

import json
import glob
from datetime import datetime
from collections import defaultdict
import statistics

class LearningEngine:
    def __init__(self):
        self.learning_file = 'learning_insights.json'
        self.completed_bets = []
        self.insights = {}
        
    def load_completed_bets(self):
        """Load all completed bets from all sources"""
        all_bets = []
        
        # Load from bet_tracker_input.json
        try:
            with open('bet_tracker_input.json', 'r') as f:
                tracker = json.load(f)
                for b in tracker.get('bets', []):
                    b['result'] = (b.get('result') or '').strip().upper()
                bets = [b for b in tracker.get('bets', []) if b.get('result') in ['WIN', 'LOSS']]
                all_bets.extend(bets)
        except:
            pass
        
        # Load from completed_bets_*.json files
        for filename in glob.glob('completed_bets_*.json'):
            try:
                with open(filename, 'r') as f:
                    completed_file = json.load(f)
                    for b in completed_file.get('bets', []):
                        b['result'] = (b.get('result') or '').strip().upper()
                    bets = [b for b in completed_file.get('bets', []) if b.get('result') in ['WIN', 'LOSS']]
                    all_bets.extend(bets)
            except:
                pass
        
        # Deduplicate
        seen = set()
        unique_bets = []
        for bet in all_bets:
            game = (bet.get('game') or bet.get('game_name') or '').strip()
            rec = (bet.get('recommendation') or '').strip()
            key = (game, bet.get('bet_type'), rec)
            if key not in seen:
                seen.add(key)
                unique_bets.append(bet)
        
        self.completed_bets = unique_bets
        return len(unique_bets)
    
    def analyze_by_dimension(self, dimension_key):
        """Analyze performance by any dimension (sport, bet_type, risk_tier, etc.)"""
        stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
        
        for bet in self.completed_bets:
            dimension_value = bet.get(dimension_key, 'Unknown')
            if isinstance(dimension_value, str):
                dimension_value = dimension_value.replace('🏀 ', '').replace('🏈 ', '').replace('⚾ ', '').replace('🟢 ', '').replace('🟡 ', '').replace('🔴 ', '').strip()
            
            result = bet.get('result')
            stats[dimension_value]['total'] += 1
            
            if result == 'WIN':
                stats[dimension_value]['wins'] += 1
            elif result == 'LOSS':
                stats[dimension_value]['losses'] += 1
        
        # Calculate win rates
        results = {}
        for key, data in stats.items():
            if data['total'] > 0:
                win_rate = (data['wins'] / data['total']) * 100
                results[key] = {
                    'wins': data['wins'],
                    'losses': data['losses'],
                    'total': data['total'],
                    'win_rate': round(win_rate, 1),
                    'record': f"{data['wins']}-{data['losses']}"
                }
        
        return results
    
    def analyze_confidence_buckets(self):
        """Analyze win rate by confidence level buckets"""
        buckets = {
            '90-100%': {'wins': 0, 'losses': 0, 'confidences': []},
            '80-89%': {'wins': 0, 'losses': 0, 'confidences': []},
            '70-79%': {'wins': 0, 'losses': 0, 'confidences': []},
            '60-69%': {'wins': 0, 'losses': 0, 'confidences': []},
            '50-59%': {'wins': 0, 'losses': 0, 'confidences': []},
        }
        
        for bet in self.completed_bets:
            confidence = bet.get('confidence', 0)
            result = bet.get('result')
            
            if confidence >= 90:
                bucket = '90-100%'
            elif confidence >= 80:
                bucket = '80-89%'
            elif confidence >= 70:
                bucket = '70-79%'
            elif confidence >= 60:
                bucket = '60-69%'
            else:
                bucket = '50-59%'
            
            buckets[bucket]['confidences'].append(confidence)
            if result == 'WIN':
                buckets[bucket]['wins'] += 1
            elif result == 'LOSS':
                buckets[bucket]['losses'] += 1
        
        results = {}
        for bucket, data in buckets.items():
            total = data['wins'] + data['losses']
            if total > 0:
                win_rate = (data['wins'] / total) * 100
                avg_confidence = statistics.mean(data['confidences']) if data['confidences'] else 0
                results[bucket] = {
                    'wins': data['wins'],
                    'losses': data['losses'],
                    'total': total,
                    'win_rate': round(win_rate, 1),
                    'avg_confidence': round(avg_confidence, 1),
                    'record': f"{data['wins']}-{data['losses']}"
                }
        
        return results
    
    def analyze_edge_buckets(self):
        """Analyze win rate by edge size"""
        buckets = {
            '10+ pts': {'wins': 0, 'losses': 0, 'edges': []},
            '5-9.9 pts': {'wins': 0, 'losses': 0, 'edges': []},
            '3-4.9 pts': {'wins': 0, 'losses': 0, 'edges': []},
            '1-2.9 pts': {'wins': 0, 'losses': 0, 'edges': []},
            '0-0.9 pts': {'wins': 0, 'losses': 0, 'edges': []},
        }
        
        for bet in self.completed_bets:
            edge = bet.get('edge', 0)
            result = bet.get('result')
            
            if edge >= 10:
                bucket = '10+ pts'
            elif edge >= 5:
                bucket = '5-9.9 pts'
            elif edge >= 3:
                bucket = '3-4.9 pts'
            elif edge >= 1:
                bucket = '1-2.9 pts'
            else:
                bucket = '0-0.9 pts'
            
            buckets[bucket]['edges'].append(edge)
            if result == 'WIN':
                buckets[bucket]['wins'] += 1
            elif result == 'LOSS':
                buckets[bucket]['losses'] += 1
        
        results = {}
        for bucket, data in buckets.items():
            total = data['wins'] + data['losses']
            if total > 0:
                win_rate = (data['wins'] / total) * 100
                avg_edge = statistics.mean(data['edges']) if data['edges'] else 0
                results[bucket] = {
                    'wins': data['wins'],
                    'losses': data['losses'],
                    'total': total,
                    'win_rate': round(win_rate, 1),
                    'avg_edge': round(avg_edge, 1),
                    'record': f"{data['wins']}-{data['losses']}"
                }
        
        return results
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Overall stats
        total_bets = len(self.completed_bets)
        total_wins = sum(1 for b in self.completed_bets if b.get('result') == 'WIN')
        overall_win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
        
        # Analyze by sport
        by_sport = self.analyze_by_dimension('sport')
        best_sport = max(by_sport.items(), key=lambda x: x[1]['win_rate']) if by_sport else (None, None)
        worst_sport = min(by_sport.items(), key=lambda x: x[1]['win_rate']) if by_sport else (None, None)
        
        if best_sport[0] and best_sport[1]['win_rate'] > overall_win_rate + 10:
            recommendations.append({
                'type': 'FOCUS',
                'priority': 'HIGH',
                'action': f"Increase bet frequency on {best_sport[0]} (win rate: {best_sport[1]['win_rate']}%)",
                'reason': f"{best_sport[1]['win_rate'] - overall_win_rate:.1f}% above overall average"
            })
        
        if worst_sport[0] and worst_sport[1]['win_rate'] < overall_win_rate - 10 and worst_sport[1]['total'] >= 3:
            recommendations.append({
                'type': 'REDUCE',
                'priority': 'HIGH',
                'action': f"Reduce or pause bets on {worst_sport[0]} (win rate: {worst_sport[1]['win_rate']}%)",
                'reason': f"{overall_win_rate - worst_sport[1]['win_rate']:.1f}% below overall average"
            })
        
        # Analyze by bet type
        by_bet_type = self.analyze_by_dimension('bet_type')
        for bet_type, stats in by_bet_type.items():
            if stats['total'] >= 3:
                if stats['win_rate'] < 50:
                    recommendations.append({
                        'type': 'REDUCE',
                        'priority': 'MEDIUM',
                        'action': f"Reduce {bet_type} bets (win rate: {stats['win_rate']}%)",
                        'reason': f"Below 50% threshold with {stats['total']} bets"
                    })
                elif stats['win_rate'] > 75:
                    recommendations.append({
                        'type': 'INCREASE',
                        'priority': 'MEDIUM',
                        'action': f"Increase {bet_type} bets (win rate: {stats['win_rate']}%)",
                        'reason': f"Strong performance with {stats['total']} bets"
                    })
        
        # Analyze confidence calibration
        by_confidence = self.analyze_confidence_buckets()
        for bucket, stats in by_confidence.items():
            if stats['total'] >= 3:
                expected_min = int(bucket.split('-')[0].replace('%', ''))
                if stats['win_rate'] < expected_min - 10:
                    recommendations.append({
                        'type': 'CALIBRATE',
                        'priority': 'HIGH',
                        'action': f"Lower confidence for {bucket} bucket (actual: {stats['win_rate']}% vs expected: {expected_min}%+)",
                        'reason': f"Model is overconfident by {expected_min - stats['win_rate']:.1f}%"
                    })
        
        # Analyze edge effectiveness
        by_edge = self.analyze_edge_buckets()
        for bucket, stats in by_edge.items():
            if stats['total'] >= 3:
                if 'pts' in bucket and stats['win_rate'] < 55:
                    recommendations.append({
                        'type': 'THRESHOLD',
                        'priority': 'MEDIUM',
                        'action': f"Raise minimum edge threshold for {bucket} range",
                        'reason': f"Only {stats['win_rate']}% win rate with edge range {bucket}"
                    })
        
        # Risk tier analysis
        by_risk = self.analyze_by_dimension('risk_tier')
        for tier, stats in by_risk.items():
            if stats['total'] >= 3:
                if 'HIGH' in tier and stats['win_rate'] < 60:
                    recommendations.append({
                        'type': 'REDUCE',
                        'priority': 'HIGH',
                        'action': f"Reduce HIGH RISK bets (win rate: {stats['win_rate']}%)",
                        'reason': f"High risk should exceed 65% to justify variance"
                    })
                elif 'LOW' in tier and stats['win_rate'] > 80:
                    recommendations.append({
                        'type': 'INCREASE',
                        'priority': 'LOW',
                        'action': f"Increase LOW RISK bet size or frequency",
                        'reason': f"Strong {stats['win_rate']}% performance with low variance"
                    })
        
        return recommendations
    
    def calculate_optimal_thresholds(self):
        """Calculate optimal thresholds based on historical performance"""
        thresholds = {
            'min_confidence': 70,  # Default
            'min_edge': 2.0,  # Default
            'max_high_risk_pct': 20,  # Default
        }
        
        # Find minimum confidence that maintains 70%+ win rate
        by_confidence = self.analyze_confidence_buckets()
        profitable_buckets = [b for b, s in by_confidence.items() if s['win_rate'] >= 70 and s['total'] >= 3]
        if profitable_buckets:
            lowest_profitable = min([int(b.split('-')[0].replace('%', '')) for b in profitable_buckets])
            thresholds['min_confidence'] = lowest_profitable
        
        # Find minimum edge that maintains 70%+ win rate
        by_edge = self.analyze_edge_buckets()
        profitable_edges = [b for b, s in by_edge.items() if s['win_rate'] >= 70 and s['total'] >= 3]
        if profitable_edges:
            edge_map = {
                '10+ pts': 10,
                '5-9.9 pts': 5,
                '3-4.9 pts': 3,
                '1-2.9 pts': 1,
                '0-0.9 pts': 0
            }
            lowest_edge = min([edge_map.get(b, 0) for b in profitable_edges])
            thresholds['min_edge'] = lowest_edge
        
        # Calculate safe high-risk percentage
        by_risk = self.analyze_by_dimension('risk_tier')
        high_risk_stats = by_risk.get('HIGH RISK', {})
        if high_risk_stats and high_risk_stats.get('win_rate', 0) < 65:
            thresholds['max_high_risk_pct'] = 10  # Reduce high risk exposure
        elif high_risk_stats and high_risk_stats.get('win_rate', 0) > 75:
            thresholds['max_high_risk_pct'] = 30  # Increase if profitable
        
        return thresholds
    
    def run_analysis(self):
        """Run complete analysis and save insights"""
        print("\n" + "=" * 70)
        print("🧠 LarlBot Learning Engine v1.0")
        print("=" * 70)
        
        # Load data
        num_bets = self.load_completed_bets()
        print(f"📊 Loaded {num_bets} completed bets for analysis\n")
        
        if num_bets < 5:
            print("⚠️  Need at least 5 completed bets to generate insights")
            print("Keep betting and check back later!")
            return
        
        # Run analyses
        by_sport = self.analyze_by_dimension('sport')
        by_bet_type = self.analyze_by_dimension('bet_type')
        by_risk = self.analyze_by_dimension('risk_tier')
        by_confidence = self.analyze_confidence_buckets()
        by_edge = self.analyze_edge_buckets()
        recommendations = self.generate_recommendations()
        optimal_thresholds = self.calculate_optimal_thresholds()
        
        # Overall stats
        total_wins = sum(1 for b in self.completed_bets if b.get('result') == 'WIN')
        overall_win_rate = (total_wins / num_bets * 100)
        
        # Display results
        print(f"📈 Overall Win Rate: {overall_win_rate:.1f}% ({total_wins}-{num_bets - total_wins})\n")
        
        print("🏀 Performance by Sport:")
        for sport, stats in sorted(by_sport.items(), key=lambda x: x[1]['win_rate'], reverse=True):
            emoji = '🔥' if stats['win_rate'] >= 75 else '✅' if stats['win_rate'] >= 60 else '⚠️' if stats['win_rate'] >= 50 else '❌'
            print(f"  {emoji} {sport:20} {stats['record']:6} ({stats['win_rate']:5.1f}%)")
        
        print("\n📊 Performance by Bet Type:")
        for bet_type, stats in sorted(by_bet_type.items(), key=lambda x: x[1]['win_rate'], reverse=True):
            emoji = '🔥' if stats['win_rate'] >= 75 else '✅' if stats['win_rate'] >= 60 else '⚠️' if stats['win_rate'] >= 50 else '❌'
            print(f"  {emoji} {bet_type:12} {stats['record']:6} ({stats['win_rate']:5.1f}%)")
        
        print("\n🎯 Confidence Calibration:")
        for bucket, stats in sorted(by_confidence.items(), reverse=True):
            expected = int(bucket.split('-')[0].replace('%', ''))
            diff = stats['win_rate'] - expected
            emoji = '✅' if abs(diff) < 10 else '⚠️' if abs(diff) < 20 else '❌'
            print(f"  {emoji} {bucket:10} {stats['record']:6} ({stats['win_rate']:5.1f}% actual vs {expected}% expected)")
        
        print("\n💰 Edge Analysis:")
        for bucket, stats in sorted(by_edge.items(), key=lambda x: x[1]['avg_edge'], reverse=True):
            emoji = '🔥' if stats['win_rate'] >= 75 else '✅' if stats['win_rate'] >= 60 else '⚠️' if stats['win_rate'] >= 50 else '❌'
            print(f"  {emoji} {bucket:12} {stats['record']:6} ({stats['win_rate']:5.1f}%)")
        
        print("\n🎲 Risk Tier Performance:")
        for tier, stats in sorted(by_risk.items(), key=lambda x: x[1]['win_rate'], reverse=True):
            emoji = '🔥' if stats['win_rate'] >= 75 else '✅' if stats['win_rate'] >= 60 else '⚠️' if stats['win_rate'] >= 50 else '❌'
            print(f"  {emoji} {tier:15} {stats['record']:6} ({stats['win_rate']:5.1f}%)")
        
        print("\n💡 Recommendations:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = '🔴' if rec['priority'] == 'HIGH' else '🟡' if rec['priority'] == 'MEDIUM' else '🟢'
                print(f"  {i}. {priority_emoji} [{rec['type']}] {rec['action']}")
                print(f"     → {rec['reason']}")
        else:
            print("  ✅ No major adjustments needed - keep doing what you're doing!")
        
        print("\n⚙️  Optimal Thresholds:")
        print(f"  • Minimum Confidence: {optimal_thresholds['min_confidence']}%")
        print(f"  • Minimum Edge: {optimal_thresholds['min_edge']} pts")
        print(f"  • Max High-Risk %: {optimal_thresholds['max_high_risk_pct']}%")
        
        # Save insights
        insights = {
            'generated_at': datetime.now().isoformat(),
            'total_bets_analyzed': num_bets,
            'overall_win_rate': round(overall_win_rate, 1),
            'by_sport': by_sport,
            'by_bet_type': by_bet_type,
            'by_risk_tier': by_risk,
            'by_confidence': by_confidence,
            'by_edge': by_edge,
            'recommendations': recommendations,
            'optimal_thresholds': optimal_thresholds
        }
        
        with open(self.learning_file, 'w') as f:
            json.dump(insights, f, indent=2)
        
        print(f"\n💾 Insights saved to: {self.learning_file}")
        print("=" * 70)

if __name__ == '__main__':
    engine = LearningEngine()
    engine.run_analysis()
