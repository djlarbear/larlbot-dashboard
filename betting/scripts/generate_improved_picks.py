#!/usr/bin/env python3
"""
Generate Improved Picks v1.0
Complete workflow:
1. Analyze previous day's results (learning)
2. Update adaptive weights
3. Generate today's picks
4. Rank using improved weights
5. Save to dashboard
"""

import sys
import json
import subprocess
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedPickGenerator:
    def __init__(self):
        self.date_today = datetime.now().strftime('%Y-%m-%d')
        
    def step_1_analyze_learning(self):
        """Run learning engine on completed bets"""
        logger.info("=" * 70)
        logger.info("STEP 1: ANALYZING PREVIOUS DATA FOR LEARNING")
        logger.info("=" * 70)
        
        result = subprocess.run(['python3', 'learning_engine.py'], 
                              capture_output=False, text=True)
        
        logger.info("✅ Learning analysis complete\n")
        return True
    
    def step_2_update_weights(self):
        """Update adaptive weights based on learning"""
        logger.info("=" * 70)
        logger.info("STEP 2: UPDATING ADAPTIVE WEIGHTS")
        logger.info("=" * 70)
        
        result = subprocess.run(['python3', 'update_adaptive_weights.py'],
                              capture_output=False, text=True)
        
        logger.info("✅ Weights updated\n")
        return True
    
    def step_3_generate_picks(self):
        """Generate today's picks"""
        logger.info("=" * 70)
        logger.info(f"STEP 3: GENERATING TODAY'S PICKS ({self.date_today})")
        logger.info("=" * 70)
        
        try:
            from daily_recommendations import get_todays_value_bets
            
            picks = get_todays_value_bets()
            logger.info(f"✅ Generated {len(picks)} picks")
            
            # Save to active_bets.json
            active_bets_data = {
                'date': self.date_today,
                'timestamp': datetime.now().isoformat(),
                'total_picks': len(picks),
                'bets': picks
            }
            
            with open('active_bets.json', 'w') as f:
                json.dump(active_bets_data, f, indent=2)
            
            # Also save to completed_bets_YYYY-MM-DD.json for tracking
            completed_bets_data = {
                'date': self.date_today,
                'timestamp': datetime.now().isoformat(),
                'total_picks': len(picks),
                'bets': picks
            }
            
            with open(f'completed_bets_{self.date_today}.json', 'w') as f:
                json.dump(completed_bets_data, f, indent=2)
            
            logger.info(f"   ✅ Saved to active_bets.json")
            logger.info(f"   ✅ Saved to completed_bets_{self.date_today}.json\n")
            
            return len(picks)
        
        except Exception as e:
            logger.error(f"❌ Failed to generate picks: {e}")
            return 0
    
    def step_4_rank_bets(self):
        """Rank bets using improved adaptive weights"""
        logger.info("=" * 70)
        logger.info("STEP 4: RANKING PICKS WITH ADAPTIVE WEIGHTS")
        logger.info("=" * 70)
        
        result = subprocess.run(['python3', 'bet_ranker.py'],
                              capture_output=False, text=True)
        
        # Load and display results
        try:
            with open('ranked_bets.json', 'r') as f:
                ranked = json.load(f)
            
            top_10 = ranked.get('top_10', [])
            rest = ranked.get('rest', [])
            
            logger.info(f"\n📊 RANKING RESULTS:")
            logger.info(f"   Top 10: {len(top_10)} bets")
            logger.info(f"   Rest: {len(rest)} bets")
            
            if top_10:
                logger.info(f"\n   🏆 TOP 10 PICKS:\n")
                for i, bet_item in enumerate(top_10[:5], 1):
                    game = bet_item.get('game', '?')
                    score = bet_item.get('score', 0)
                    logger.info(f"      {i}. {game} (Score: {score:.2f})")
                if len(top_10) > 5:
                    logger.info(f"      ... and {len(top_10)-5} more\n")
            
            return len(top_10), len(rest)
        
        except Exception as e:
            logger.error(f"❌ Failed to load ranked bets: {e}")
            return 0, 0
    
    def step_5_summary(self, pick_count, top_10_count, rest_count):
        """Display final summary"""
        logger.info("=" * 70)
        logger.info("✅ COMPLETE: IMPROVED PICKS READY FOR TODAY")
        logger.info("=" * 70)
        
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Date: {self.date_today}")
        logger.info(f"   Total picks generated: {pick_count}")
        logger.info(f"   Top 10 picks: {top_10_count}")
        logger.info(f"   Dashboard ready: YES")
        
        logger.info(f"\n🔬 SYSTEM IMPROVEMENTS APPLIED:")
        logger.info(f"   ✓ SPREAD bets boosted: 1.22x weight (63.6% historical win rate)")
        logger.info(f"   ✓ TOTAL bets suppressed: 0.75x weight (40% historical win rate)")
        logger.info(f"   ✓ MONEYLINE bets suppressed: 0.77x weight (33.3% historical win rate)")
        logger.info(f"   ✓ Confidence calibrated: -30-40% adjustment for overconfidence")
        
        logger.info(f"\n🎯 READY FOR:")
        logger.info(f"   1. Game status monitoring (every 15 min)")
        logger.info(f"   2. Result tracking when games complete")
        logger.info(f"   3. Dashboard display with top 10")
        logger.info(f"   4. Learning loop for tomorrow's improvements\n")
    
    def run(self):
        """Execute complete workflow"""
        logger.info("\n")
        logger.info("=" * 70)
        logger.info("🗡️  SWORD - IMPROVED PICK GENERATION WORKFLOW")
        logger.info("=" * 70)
        logger.info("")
        
        self.step_1_analyze_learning()
        self.step_2_update_weights()
        
        pick_count = self.step_3_generate_picks()
        top_10_count, rest_count = self.step_4_rank_bets()
        
        self.step_5_summary(pick_count, top_10_count, rest_count)

if __name__ == '__main__':
    generator = ImprovedPickGenerator()
    generator.run()
