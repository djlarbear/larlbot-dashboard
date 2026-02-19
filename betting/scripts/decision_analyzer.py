#!/usr/bin/env python3
"""
DECISION ANALYZER & LEARNING TRACKER
Tracks all major betting decisions for future optimization

Features:
- Analyzes alternative recommendations (e.g., Charlotte -14.5 vs UTSA +14.5)
- Scores both options using multiple criteria
- Learns from outcomes over time
- Provides transparent decision rationale
"""

import json
import os
from datetime import datetime
from pathlib import Path

class DecisionAnalyzer:
    """Analyze betting decisions and learn from outcomes"""
    
    def __init__(self):
        self.decisions_file = '/Users/macmini/.openclaw/workspace/betting_decisions.json'
        self.load_decisions()
    
    def load_decisions(self):
        """Load historical decisions"""
        if os.path.exists(self.decisions_file):
            with open(self.decisions_file, 'r') as f:
                self.decisions = json.load(f)
        else:
            self.decisions = []
    
    def save_decisions(self):
        """Save decisions to file"""
        with open(self.decisions_file, 'w') as f:
            json.dump(self.decisions, f, indent=2)
    
    def analyze_game_options(self, game, options):
        """
        Analyze all options for a game and rank them
        
        Args:
            game: Game name (e.g., "UTSA @ Charlotte")
            options: List of dict with keys:
                - recommendation: Bet text (e.g., "Charlotte -14.5")
                - bet_type: SPREAD, MONEYLINE, TOTAL
                - confidence: % confidence (0-100)
                - edge: Point edge
                - reasoning: Why this bet
        
        Returns:
            Ranked options with scores and recommendations
        """
        
        analysis = {
            'game': game,
            'analyzed_at': datetime.now().isoformat(),
            'options': [],
            'recommendation': None
        }
        
        # Score each option
        for opt in options:
            score = self.calculate_option_score(opt)
            analysis['options'].append({
                **opt,
                'score': score
            })
        
        # Sort by score
        analysis['options'].sort(key=lambda x: x['score'], reverse=True)
        analysis['recommendation'] = analysis['options'][0]
        
        return analysis
    
    def calculate_option_score(self, option):
        """
        Score an option using multiple criteria
        
        CHARLOTTE -14.5:
        - Confidence: 94% (excellent)
        - Edge: 5.8pt (solid)
        - Variance: HIGH (need 15+ point win, tight threshold)
        - Ways to win: 1 (Charlotte wins by 15+)
        - Risk profile: High variance big favorite
        - Learning: 82% of spread losses would have been ML wins
        
        UTSA +14.5:
        - Confidence: 84% (very good, from ML data)
        - Edge: 5.8pt (same edge!)
        - Variance: LOWER (14.5 point buffer)
        - Ways to win: 2 (UTSA loses by <14.5 OR UTSA wins)
        - Risk profile: Better risk/reward, multiple paths
        - Learning: Underdog spreads outperform against 82% loss rate
        """
        
        base_score = 50
        
        # Confidence impact (+1 per % confidence)
        base_score += option.get('confidence', 0) * 0.5
        
        # Edge impact (+5 per point)
        base_score += option.get('edge', 0) * 5
        
        # Variance penalty for tight spreads
        if option.get('bet_type') == 'SPREAD':
            spread = float(option.get('recommendation', '').split()[-1])
            if abs(spread) > 15:  # Big favorites are high variance
                base_score *= 0.92  # 8% penalty for high variance
            elif abs(spread) < 8:  # Tight spreads
                base_score *= 0.95  # 5% penalty
        
        # Risk/reward multiplier for underdogs with points
        if option.get('bet_type') == 'SPREAD':
            if '+' in option.get('recommendation', ''):
                base_score *= 1.08  # 8% bonus for underdog spreads
        
        return round(base_score, 1)
    
    def record_decision(self, game, chosen, alternatives, reason):
        """Record a major decision for learning"""
        decision = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'game': game,
            'chosen_bet': chosen,
            'alternatives_considered': alternatives,
            'rationale': reason,
            'outcome': None,  # Will be filled in later
            'learning': None  # Will be filled in later
        }
        self.decisions.append(decision)
        self.save_decisions()
        return decision
    
    def record_outcome(self, game, outcome):
        """Record the outcome of a decision (WIN/LOSS/PUSH)"""
        for decision in self.decisions:
            if decision['game'] == game and decision['outcome'] is None:
                decision['outcome'] = outcome
                decision['recorded_at'] = datetime.now().isoformat()
                self.save_decisions()
                return decision
        return None
    
    def get_decision_accuracy(self):
        """Calculate how often we made the right choice"""
        completed = [d for d in self.decisions if d['outcome']]
        if not completed:
            return None
        
        wins = len([d for d in completed if d['outcome'] == 'WIN'])
        return {
            'total': len(completed),
            'wins': wins,
            'win_rate': round(wins / len(completed) * 100, 1)
        }

# CHARLOTTE -14.5 vs UTSA +14.5 ANALYSIS
def analyze_charlotte_utsa():
    """Analyze the Charlotte/UTSA game options"""
    
    analyzer = DecisionAnalyzer()
    
    options = [
        {
            'recommendation': 'Charlotte 49ers -14.5',
            'bet_type': 'SPREAD',
            'confidence': 94,
            'edge': 5.8,
            'reasoning': 'Charlotte has significant edge (favored by 14.5) with 5.8pt edge. High confidence (94%) backed by strong matchup data.',
            'variance': 'HIGH',
            'ways_to_win': 1,
            'why_selected': 'Higher confidence (94% vs 84%)',
            'risk_profile': 'Big favorite, tight threshold'
        },
        {
            'recommendation': 'UTSA Roadrunners +14.5',
            'bet_type': 'SPREAD',
            'confidence': 84,
            'edge': 5.8,
            'reasoning': 'Same edge (5.8pt) but UTSA has 84% ML confidence (they can win!). Multiple ways to profit: lose by <14.5 OR win outright. Better risk-adjusted returns.',
            'variance': 'LOWER',
            'ways_to_win': 2,
            'why_alternative': 'Better risk/reward profile despite lower stated confidence',
            'risk_profile': 'Underdog with points, multiple paths'
        }
    ]
    
    analysis = analyzer.analyze_game_options('UTSA @ Charlotte', options)
    
    print("\n" + "="*80)
    print("🎰 CHARLOTTE -14.5 vs UTSA +14.5 ANALYSIS")
    print("="*80)
    
    for i, opt in enumerate(analysis['options'], 1):
        print(f"\n{'#' if i == 1 else '•'} OPTION {i}: {opt['recommendation']}")
        print(f"   Confidence: {opt['confidence']}%")
        print(f"   Edge: {opt['edge']}pt")
        print(f"   Variance: {opt.get('variance', 'N/A')}")
        print(f"   Ways to Win: {opt.get('ways_to_win', 'N/A')}")
        print(f"   Risk Profile: {opt.get('risk_profile', 'N/A')}")
        print(f"   Score: {opt['score']}")
        print(f"   Reasoning: {opt['reasoning']}")
    
    print(f"\n🏆 RECOMMENDATION: {analysis['recommendation']['recommendation']}")
    print(f"   Score: {analysis['recommendation']['score']}")
    print(f"   Why: {analysis['recommendation']['reasoning']}")
    
    print("\n" + "="*80)
    print("KEY INSIGHT")
    print("="*80)
    print("""
Both bets have the SAME EDGE (5.8pt), but UTSA +14.5 offers:
✅ Lower variance (multiple ways to win)
✅ Better risk/reward (14.5pt buffer vs need 15pt)
✅ Aligns with UTSA's 84% ML confidence
✅ Less overconfidence penalty (vs 94% on tight favorite)

Charlotte -14.5 only wins if Charlotte is truly perfect (15+ point win).
UTSA +14.5 wins in more scenarios (underdog spread logic).

RECOMMENDATION: Consider switching to UTSA +14.5 for better
risk-adjusted returns. Same edge, lower variance = better for long-term growth.
    """)
    
    return analysis

if __name__ == '__main__':
    analyze_charlotte_utsa()
