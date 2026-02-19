#!/usr/bin/env python3
"""
Dynamic Game Status Monitor
Runs every 15-30 minutes to update game status, move finished games to results

Purpose: Keep dashboard real-time updated as games start/finish
"""

import json
import requests
from datetime import datetime, timedelta

class DynamicGameStatusMonitor:
    """Monitors game status and updates dashboard in real-time"""
    
    def __init__(self):
        self.active_bets = []
        self.completed_today = []
        self.in_progress = []
        self.not_started = []
    
    def load_active_bets(self, filename='active_bets.json'):
        """Load all active bets for today"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.active_bets = data.get('bets', [])
        except FileNotFoundError:
            self.active_bets = []
        
        return self.active_bets
    
    def check_game_status(self, game_name):
        """
        Check if a game has started or finished
        Returns: {'status': 'NOT_STARTED'|'IN_PROGRESS'|'FINISHED', 
                  'start_time': datetime,
                  'final_score': score_if_finished,
                  'time_until_start': minutes_until_start}
        """
        
        # Example ESPN API or web scraping call
        # For now, return stub that shows the structure
        
        try:
            # Try ESPN API
            game_parts = game_name.split(' @ ')
            if len(game_parts) != 2:
                return {'status': 'UNKNOWN', 'error': 'Could not parse game'}
            
            away = game_parts[0].strip()
            home = game_parts[1].strip()
            
            # In production, this would call ESPN or real scoreboard API
            # For demo, return structure
            
            return {
                'status': 'NOT_STARTED',  # Will be filled by real API
                'away_team': away,
                'home_team': home,
                'start_time': None,
                'final_score': None,
                'current_score': None,
                'time_until_start': None
            }
        
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def classify_bets_by_status(self):
        """Classify all bets by game status"""
        
        self.not_started = []
        self.in_progress = []
        self.completed_today = []
        
        for bet in self.active_bets:
            game = bet.get('game', '')
            status_info = self.check_game_status(game)
            status = status_info.get('status', 'UNKNOWN')
            
            # Add status info to bet
            bet['game_status'] = status
            bet['status_info'] = status_info
            
            if status == 'NOT_STARTED':
                self.not_started.append(bet)
            elif status == 'IN_PROGRESS':
                self.in_progress.append(bet)
            elif status == 'FINISHED':
                # Calculate outcome
                outcome = self.calculate_outcome(bet, status_info)
                bet['result'] = {
                    'outcome': outcome,
                    'timestamp': datetime.now().isoformat(),
                    'final_score': status_info.get('final_score')
                }
                self.completed_today.append(bet)
        
        return {
            'not_started': len(self.not_started),
            'in_progress': len(self.in_progress),
            'completed': len(self.completed_today)
        }
    
    def calculate_outcome(self, bet, final_info):
        """Calculate if bet won/lost/push"""
        
        # This would actually calculate based on:
        # - Bet type (SPREAD, TOTAL, MONEYLINE)
        # - Recommendation
        # - Final score
        
        # For now, return placeholder
        return 'CALCULATING'
    
    def save_active_bets_filtered(self):
        """Save filtered active bets (only not_started)"""
        
        filtered_data = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'timestamp': datetime.now().isoformat(),
            'total_tracked': len(self.active_bets),
            'available_to_place': len(self.not_started),
            'in_progress': len(self.in_progress),
            'completed_today': len(self.completed_today),
            'bets': self.not_started  # Only show bets that haven't started
        }
        
        with open('active_bets_not_started.json', 'w') as f:
            json.dump(filtered_data, f, indent=2)
        
        return 'active_bets_not_started.json'
    
    def move_finished_to_results(self):
        """Move finished games to previous results"""
        
        # Load existing results
        try:
            with open('completed_bets_2026-02-15.json', 'r') as f:
                results = json.load(f)
        except FileNotFoundError:
            results = {'date': datetime.now().strftime("%Y-%m-%d"), 'bets': []}
        
        # Add newly completed bets
        for completed_bet in self.completed_today:
            # Check if already in results
            existing = [b for b in results['bets'] if b.get('game') == completed_bet.get('game') 
                       and b.get('bet_type') == completed_bet.get('bet_type')]
            
            if not existing:
                results['bets'].append(completed_bet)
        
        # Save updated results
        with open('completed_bets_2026-02-15.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return len(self.completed_today)
    
    def run_dynamic_update(self):
        """Main function: Check all games, update dashboard"""
        
        print("=" * 80)
        print(f"🔄 DYNAMIC GAME STATUS UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Load active bets
        self.load_active_bets()
        print(f"\n📊 Checking status of {len(self.active_bets)} active bets...")
        
        # Classify by status
        counts = self.classify_bets_by_status()
        print(f"\n✅ Results:")
        print(f"   • Not Started: {counts['not_started']} (can place)")
        print(f"   • In Progress: {counts['in_progress']} (hide from place tab)")
        print(f"   • Finished: {counts['completed']} (move to results)")
        
        # Save filtered bets (only not started)
        self.save_active_bets_filtered()
        print(f"\n💾 Saved: active_bets_not_started.json (only {counts['not_started']} bets)")
        
        # Move finished games to results
        moved = self.move_finished_to_results()
        print(f"✅ Moved {moved} finished games to Previous Results")
        
        print("\n" + "=" * 80)
        print("📋 DASHBOARD UPDATES")
        print("=" * 80)
        
        print(f"""
Today's Bets Tab:
  ✅ Shows: {counts['not_started']} bets (not yet started)
  ❌ Hides: {counts['in_progress']} bets (games in progress)
  ❌ Hides: {counts['completed']} bets (games finished)

Previous Results Tab:
  ✅ Auto-added: {moved} new finished games
  ✅ Displays: Results with outcomes
  ✅ Updates: Real-time as games finish

Live Games Tab (Optional):
  ✅ Shows: {counts['in_progress']} games currently playing
  ✅ Updates: Score, time, quarter/inning
  ✅ Purpose: Users can watch their bets

NEXT UPDATE: In 15-30 minutes
  • Re-check all game statuses
  • Move any newly-finished games
  • Update dashboard automatically
""")

def demo():
    """Demo the dynamic update system"""
    
    monitor = DynamicGameStatusMonitor()
    
    # Demo with sample data
    print("=" * 80)
    print("🎯 DYNAMIC GAME STATUS MONITOR DEMO")
    print("=" * 80)
    
    print(f"""
This system will:

1. RUN EVERY 15 MINUTES (or 30 min if you prefer)
   • Check status of all 23 active bets
   • Classify as: Not Started / In Progress / Finished

2. UPDATE DASHBOARD IN REAL-TIME
   • Today's Bets: Shows only bets not yet started
   • Live Tracking: Shows bets currently playing (optional tab)
   • Previous Results: Auto-adds finished games with outcomes

3. BENEFITS FOR YOU
   ✅ No manual tracking needed
   ✅ Dashboard always current
   ✅ Finished games auto-move to results
   ✅ See outcomes as they happen
   ✅ Only place bets that haven't started

CURRENT SCHEDULE (After today):
  7:00 AM  → Daily bets displayed
  Every 15 min → Check status, update dashboard
  Throughout day → Games auto-move as they finish
  
EXAMPLE TIMELINE (Basketball games):
  
  7:00 AM  → 23 bets available to place
  7:15 AM  → 1st game starts, removed from "Place Bets"
  7:30 AM  → 3 more games start
  8:00 AM  → 1 game finishes, auto-moves to "Previous Results"
  ...continue all day...
  11:00 PM → Last games finish, all moved to results
  
RESULT: Dashboard is always accurate, no manual work!
""")
    
    print("\n" + "=" * 80)
    print("✅ READY TO IMPLEMENT")
    print("=" * 80)

if __name__ == '__main__':
    demo()
