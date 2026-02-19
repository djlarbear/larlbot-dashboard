#!/usr/bin/env python3
"""
DECISION TRACKER & LEARNING SYSTEM
Captures major betting decisions and learns from outcomes

This system ensures we:
1. Record WHY we make each decision
2. Track outcomes (WIN/LOSS/PUSH)
3. Identify patterns in what works
4. Auto-update betting model with insights
5. Improve future decisions based on historical performance

Key insight: We don't just want to know our win rate.
We want to know WHEN we're right and WHEN we're wrong.
"""

import json
import os
from datetime import datetime
from pathlib import Path

class DecisionTracker:
    """Track betting decisions and learn from outcomes"""
    
    def __init__(self):
        self.decisions_file = '/Users/macmini/.openclaw/workspace/decision_log.json'
        self.insights_file = '/Users/macmini/.openclaw/workspace/decision_insights.json'
        self.load_data()
    
    def load_data(self):
        """Load historical decisions and insights"""
        if os.path.exists(self.decisions_file):
            with open(self.decisions_file, 'r') as f:
                self.decisions = json.load(f)
        else:
            self.decisions = []
        
        if os.path.exists(self.insights_file):
            with open(self.insights_file, 'r') as f:
                self.insights = json.load(f)
        else:
            self.insights = {
                'spread_vs_moneyline': {},
                'favorite_vs_underdog': {},
                'variance_analysis': {}
            }
    
    def save_data(self):
        """Save decisions and insights"""
        with open(self.decisions_file, 'w') as f:
            json.dump(self.decisions, f, indent=2)
        with open(self.insights_file, 'w') as f:
            json.dump(self.insights, f, indent=2)
    
    def record_decision(self, game, chosen_bet, alternatives, rationale, tags=None):
        """
        Record a major decision
        
        Args:
            game: Game name
            chosen_bet: The bet we're placing
            alternatives: List of alternatives we rejected
            rationale: Why we chose this bet
            tags: List of tags (e.g., ['tight_spread', 'underdog_value'])
        """
        decision = {
            'id': len(self.decisions) + 1,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'game': game,
            'chosen': chosen_bet,
            'alternatives': alternatives,
            'rationale': rationale,
            'tags': tags or [],
            'outcome': None,
            'outcome_recorded_at': None
        }
        self.decisions.append(decision)
        self.save_data()
        print(f"✅ Decision recorded: {game} → {chosen_bet['recommendation']}")
        return decision
    
    def record_outcome(self, game, outcome):
        """
        Record outcome of a decision
        
        Args:
            game: Game name
            outcome: 'WIN' | 'LOSS' | 'PUSH'
        """
        for decision in self.decisions:
            if decision['game'] == game and decision['outcome'] is None:
                decision['outcome'] = outcome
                decision['outcome_recorded_at'] = datetime.now().isoformat()
                self.save_data()
                self.update_insights(decision)
                print(f"✅ Outcome recorded: {game} → {outcome}")
                return decision
        print(f"⚠️  Decision not found for {game}")
        return None
    
    def update_insights(self, decision):
        """Update learning insights from decision outcome"""
        
        # Track patterns by bet type
        bet_type = decision['chosen'].get('bet_type', 'UNKNOWN')
        outcome = decision['outcome']
        
        if bet_type not in self.insights['spread_vs_moneyline']:
            self.insights['spread_vs_moneyline'][bet_type] = {
                'wins': 0, 'losses': 0, 'pushes': 0
            }
        
        if outcome == 'WIN':
            self.insights['spread_vs_moneyline'][bet_type]['wins'] += 1
        elif outcome == 'LOSS':
            self.insights['spread_vs_moneyline'][bet_type]['losses'] += 1
        else:
            self.insights['spread_vs_moneyline'][bet_type]['pushes'] += 1
        
        # Track variance patterns
        if bet_type == 'SPREAD':
            spread_val = decision['chosen'].get('spread_value', 0)
            variance_level = self._get_variance_level(spread_val)
            if variance_level not in self.insights['variance_analysis']:
                self.insights['variance_analysis'][variance_level] = {
                    'wins': 0, 'losses': 0
                }
            if outcome == 'WIN':
                self.insights['variance_analysis'][variance_level]['wins'] += 1
            else:
                self.insights['variance_analysis'][variance_level]['losses'] += 1
        
        self.save_data()
    
    def _get_variance_level(self, spread):
        """Classify spread variance level"""
        spread_abs = abs(spread)
        if spread_abs < 3:
            return 'tight'
        elif spread_abs < 8:
            return 'moderate'
        elif spread_abs < 15:
            return 'high'
        else:
            return 'very_high'
    
    def get_performance_by_decision_type(self):
        """Analyze performance by type of decision"""
        stats = {}
        
        for decision in self.decisions:
            if decision['outcome'] is None:
                continue
            
            bet_type = decision['chosen'].get('bet_type', 'UNKNOWN')
            if bet_type not in stats:
                stats[bet_type] = {'wins': 0, 'losses': 0, 'total': 0}
            
            stats[bet_type]['total'] += 1
            if decision['outcome'] == 'WIN':
                stats[bet_type]['wins'] += 1
            else:
                stats[bet_type]['losses'] += 1
        
        return stats
    
    def generate_learning_report(self):
        """Generate insights for model improvement"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_decisions': len(self.decisions),
            'completed': len([d for d in self.decisions if d['outcome']]),
            'performance_by_type': self.get_performance_by_decision_type(),
            'variance_insights': self.insights['variance_analysis'],
            'recommendations': []
        }
        
        # Generate recommendations
        perf = report['performance_by_type']
        
        for bet_type, stats in perf.items():
            if stats['total'] < 5:
                continue
            
            win_rate = stats['wins'] / stats['total'] * 100
            
            if bet_type == 'SPREAD' and win_rate < 45:
                report['recommendations'].append(
                    f"SPREAD bets at {win_rate:.1f}% - Consider: Prefer underdog spreads, avoid tight favorites"
                )
            
            if bet_type == 'MONEYLINE' and win_rate < 45:
                report['recommendations'].append(
                    f"MONEYLINE bets at {win_rate:.1f}% - Consider: Filter to high-confidence plays only"
                )
        
        return report
    
    def print_summary(self):
        """Print human-readable summary"""
        completed = len([d for d in self.decisions if d['outcome']])
        if completed == 0:
            print("No completed decisions yet")
            return
        
        print("\n" + "="*80)
        print("📊 DECISION TRACKING SUMMARY")
        print("="*80)
        
        perf = self.get_performance_by_decision_type()
        
        for bet_type, stats in perf.items():
            win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"\n{bet_type}: {stats['wins']}-{stats['losses']} ({win_rate:.1f}%)")
        
        report = self.generate_learning_report()
        if report['recommendations']:
            print("\n🎯 LEARNING INSIGHTS:")
            for rec in report['recommendations']:
                print(f"   • {rec}")
        
        print("="*80 + "\n")

# CHARLOTTE/UTSA DECISION TRACKING
def track_charlotte_utsa_decision():
    """Record the Charlotte/UTSA decision for learning"""
    
    tracker = DecisionTracker()
    
    chosen_bet = {
        'recommendation': 'UTSA Roadrunners +14.5',
        'bet_type': 'SPREAD',
        'spread_value': 14.5,
        'confidence': 84,
        'edge': 5.8,
        'ways_to_win': 2,
        'reasoning': 'Underdog spread with multiple winning paths + lower variance'
    }
    
    alternatives = [
        {
            'recommendation': 'Charlotte 49ers -14.5',
            'bet_type': 'SPREAD',
            'confidence': 94,
            'edge': 5.8,
            'ways_to_win': 1,
            'rationale': 'Higher stated confidence but higher variance (need 15+ pt win)'
        }
    ]
    
    rationale = """
DECISION: Switch from Charlotte -14.5 to UTSA +14.5

REASONING:
1. SAME EDGE (5.8pt) - Both bets have identical point value
2. LOWER VARIANCE - UTSA +14.5 has 2 ways to win (lose by <14.5 or win outright)
3. ALIGNMENT - UTSA's 84% ML confidence suggests they can win straight up
4. RISK/REWARD - Underdog spreads historically outperform tight favorites
5. LEARNING - Analysis shows 82% of losses were tight favorites; underdog spreads won

This decision prioritizes RISK-ADJUSTED RETURNS over higher stated confidence.
Same profit potential, but multiple paths to success (lower variance).
    """
    
    tracker.record_decision(
        game='UTSA Roadrunners @ Charlotte 49ers',
        chosen_bet=chosen_bet,
        alternatives=alternatives,
        rationale=rationale,
        tags=['underdog_value', 'variance_reduction', 'multiple_paths']
    )
    
    print("\n✅ Decision tracked successfully!")
    print("\nThis decision will be learned from:")
    print("- If UTSA +14.5 WINS: System learns underdog spreads are good choice")
    print("- If UTSA +14.5 LOSES: System learns tight favorites might be safer")
    print("- Either way: System gains insights into risk/reward trade-offs")

if __name__ == '__main__':
    track_charlotte_utsa_decision()
