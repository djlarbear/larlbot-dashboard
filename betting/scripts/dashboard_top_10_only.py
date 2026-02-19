#!/usr/bin/env python3
"""
Dashboard Top 10 Only Filter
Shows only the 10 best bets based on LarlScore
Tracks all 23 internally for learning
"""

import json
from datetime import datetime

class Top10DashboardFilter:
    """Filters bets to show only top 10 on dashboard"""
    
    def __init__(self):
        self.all_bets = []
        self.top_10 = []
        self.tracked_23 = []
    
    def load_and_score_bets(self, bets_file='active_bets.json'):
        """Load all bets and calculate LarlScore"""
        
        with open(bets_file, 'r') as f:
            data = json.load(f)
            self.all_bets = data.get('bets', [])
        
        # Score all bets
        for bet in self.all_bets:
            confidence = bet.get('confidence', 0) / 100.0
            edge = bet.get('edge', 0)
            bet_type = bet.get('bet_type', '')
            
            # Historical win rates by type
            win_rates = {
                'TOTAL': 0.778,
                'SPREAD': 0.467,
                'MONEYLINE': 0.400
            }
            win_rate = win_rates.get(bet_type, 0.5)
            
            # LarlScore = Edge × Confidence × Win Rate
            larlscore = edge * confidence * win_rate
            bet['larlscore'] = round(larlscore, 2)
        
        return self.all_bets
    
    def get_top_10(self):
        """Get top 10 bets by LarlScore"""
        
        # Sort by LarlScore
        sorted_bets = sorted(self.all_bets, key=lambda x: x.get('larlscore', 0), reverse=True)
        
        # Keep top 10
        self.top_10 = sorted_bets[:10]
        
        # Keep all 23 for internal tracking
        self.tracked_23 = sorted_bets
        
        return self.top_10
    
    def generate_dashboard_data(self):
        """Generate data for dashboard (top 10 only)"""
        
        dashboard_data = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'timestamp': datetime.now().isoformat(),
            'total_tracked': len(self.tracked_23),
            'showing_on_dashboard': len(self.top_10),
            'bets': self.top_10,
            'note': f'Showing top 10 of {len(self.tracked_23)} tracked bets'
        }
        
        return dashboard_data
    
    def save_top_10_for_dashboard(self, output_file='dashboard_bets_top10.json'):
        """Save top 10 bets for dashboard display"""
        
        dashboard_data = self.generate_dashboard_data()
        
        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        return output_file
    
    def save_all_tracked_for_learning(self, output_file='all_bets_tracked.json'):
        """Save all 23 bets for learning system"""
        
        learning_data = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'timestamp': datetime.now().isoformat(),
            'total_tracked': len(self.tracked_23),
            'bets': self.tracked_23,
            'note': 'All bets tracked for learning (including those not shown on dashboard)'
        }
        
        with open(output_file, 'w') as f:
            json.dump(learning_data, f, indent=2)
        
        return output_file
    
    def identify_losses(self, completed_bets_file='completed_bets_2026-02-15.json'):
        """Identify which top 10 bets lost so we can learn from them"""
        
        try:
            with open(completed_bets_file, 'r') as f:
                completed = json.load(f).get('bets', [])
        except FileNotFoundError:
            print(f"⚠️  No completed bets file found: {completed_bets_file}")
            return []
        
        losses = []
        
        for top_bet in self.top_10:
            game = top_bet.get('game', '')
            bet_type = top_bet.get('bet_type', '')
            
            # Find matching completed bet
            for completed_bet in completed:
                if (completed_bet.get('game') == game and 
                    completed_bet.get('bet_type') == bet_type):
                    
                    if completed_bet.get('result', {}).get('outcome') == 'LOSS':
                        losses.append({
                            'rank': self.top_10.index(top_bet) + 1,
                            'game': game,
                            'bet_type': bet_type,
                            'recommendation': top_bet.get('recommendation', ''),
                            'larlscore': top_bet.get('larlscore', 0),
                            'confidence': top_bet.get('confidence', 0),
                            'edge': top_bet.get('edge', 0),
                            'completed_bet': completed_bet
                        })
        
        return losses

def demo():
    """Demo: Load bets, score them, get top 10, save for dashboard"""
    
    filter_obj = Top10DashboardFilter()
    
    print("=" * 80)
    print("🎯 TOP 10 ONLY DASHBOARD FILTER")
    print("=" * 80)
    
    # Load and score
    print("\n📊 Loading and scoring all bets...")
    all_bets = filter_obj.load_and_score_bets()
    print(f"✅ Loaded {len(all_bets)} bets")
    
    # Get top 10
    print("\n🏆 Calculating top 10 by LarlScore...")
    top_10 = filter_obj.get_top_10()
    
    print(f"\nTop 10 Bets for Dashboard:\n")
    for i, bet in enumerate(top_10, 1):
        game = bet.get('game', '')
        rec = bet.get('recommendation', '')
        score = bet.get('larlscore', 0)
        
        print(f"{i}. {game}")
        print(f"   {rec} | LarlScore: {score}")
    
    # Save for dashboard
    print(f"\n💾 Saving top 10 for dashboard...")
    filter_obj.save_top_10_for_dashboard()
    print(f"✅ Saved: dashboard_bets_top10.json")
    
    # Save all 23 for learning
    print(f"\n📚 Saving all 23 for internal learning...")
    filter_obj.save_all_tracked_for_learning()
    print(f"✅ Saved: all_bets_tracked.json")
    
    print("\n" + "=" * 80)
    print("✅ SYSTEM STATUS")
    print("=" * 80)
    
    print(f"""
Dashboard Display:
  ✅ Shows only top 10 bets
  ✅ Ranked by LarlScore
  ✅ Cleanest, best picks only

Internal Tracking:
  ✅ All 23 bets tracked
  ✅ Full metadata recorded
  ✅ Ready for learning from all outcomes

Benefits:
  • Users see clearest recommendations (top 10)
  • System learns from ALL outcomes (23)
  • Focuses action on best bets
  • Maintains comprehensive learning data
""")

if __name__ == '__main__':
    demo()
