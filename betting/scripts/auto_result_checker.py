#!/usr/bin/env python3
"""
Autonomous Result Checker
Automatically monitors games, fetches results, and updates bets
Runs on schedule (cron) without any manual intervention
"""

import json
import requests
from datetime import datetime, timedelta
import sys
import re

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

class AutoResultChecker:
    def __init__(self):
        self.log_file = '/tmp/larlbot_auto_update.log'
        self.active_bets_file = 'active_bets.json'
        self.tracker_file = 'bet_tracker_input.json'
        
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def fetch_ncaa_results(self):
        """Fetch NCAA Basketball results from ESPN"""
        try:
            self.log("🔍 Fetching NCAA Basketball results...")
            
            # Fetch from ESPN API
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            }
            
            # Get today's and yesterday's games
            dates = [
                (datetime.now() - timedelta(days=1)).strftime('%Y%m%d'),
                datetime.now().strftime('%Y%m%d'),
            ]
            
            results = {}
            for date in dates:
                url = f"https://www.espn.com/mens-college-basketball/scoreboard/_/date/{date}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Parse scores from response (simplified)
                    results[date] = self.parse_espn_scores(response.text)
            
            return results
        except Exception as e:
            self.log(f"⚠️  Error fetching NCAA results: {e}")
            return {}
    
    def parse_espn_scores(self, html_content):
        """Parse ESPN HTML for scores"""
        scores = []
        try:
            # Look for score patterns in HTML
            import re
            
            # Pattern: Team1 Score - Team2 Score (Final/Live)
            pattern = r'(\w+[\w\s]*?)\s+(\d+)\s*-\s*(\d+)\s+(\w+[\w\s]*?)\s+(Final|Live)'
            
            matches = re.findall(pattern, html_content)
            for match in matches:
                away_team, away_score, home_score, home_team, status = match
                if status == 'Final':
                    scores.append({
                        'away': away_team.strip(),
                        'away_score': int(away_score),
                        'home': home_team.strip(),
                        'home_score': int(home_score),
                        'final': True
                    })
        except Exception as e:
            self.log(f"⚠️  Error parsing ESPN scores: {e}")
        
        return scores
    
    def match_bet_with_result(self, bet, game_result):
        """Match a bet with game result and determine WIN/LOSS"""
        try:
            bet_game = bet.get('game', '').lower().strip()
            result_away = game_result.get('away', '').lower().strip()
            result_home = game_result.get('home', '').lower().strip()
            
            # Check if game names match
            if not (result_away in bet_game or result_home in bet_game):
                return None
            
            away_score = game_result.get('away_score', 0)
            home_score = game_result.get('home_score', 0)
            final_score = f"{away_score}-{home_score}"
            
            recommendation = bet.get('recommendation', '').upper()
            bet_type = bet.get('bet_type', '').upper()
            
            result = None
            
            # SPREAD bets
            if 'SPREAD' in bet_type:
                # Extract team name from recommendation
                if any(team in recommendation for team in result_away.split()):
                    # Betting away team
                    line = float(re.findall(r'[-+]?\d+\.?\d*', recommendation)[0])
                    if away_score + line > home_score:
                        result = 'WIN'
                    else:
                        result = 'LOSS'
                elif any(team in recommendation for team in result_home.split()):
                    # Betting home team
                    line = float(re.findall(r'[-+]?\d+\.?\d*', recommendation)[0])
                    if home_score + line > away_score:
                        result = 'WIN'
                    else:
                        result = 'LOSS'
            
            # UNDER/OVER bets
            elif 'UNDER' in bet_type or 'OVER' in bet_type:
                total = float(re.findall(r'\d+\.?\d*', recommendation)[-1])
                combined_score = away_score + home_score
                if 'UNDER' in recommendation or 'Under' in recommendation:
                    result = 'WIN' if combined_score < total else 'LOSS'
                elif 'OVER' in recommendation or 'Over' in recommendation:
                    result = 'WIN' if combined_score > total else 'LOSS'
            
            if result:
                return {
                    'result': result,
                    'final_score': final_score,
                    'away_score': away_score,
                    'home_score': home_score
                }
        except Exception as e:
            self.log(f"⚠️  Error matching bet: {e}")
        
        return None
    
    def update_completed_bets(self):
        """Check for completed games and update bets automatically"""
        try:
            self.log("📊 Checking for completed games...")
            
            # Load active bets
            with open(self.active_bets_file, 'r') as f:
                active_data = json.load(f)
            
            active_bets = active_data.get('bets', [])
            
            if not active_bets:
                self.log("✅ No active bets to check")
                return
            
            # Fetch game results
            game_results = self.fetch_ncaa_results()
            if not game_results:
                self.log("⚠️  Could not fetch game results")
                return
            
            # Load tracker for completed bets
            with open(self.tracker_file, 'r') as f:
                tracker = json.load(f)
            
            completed = []
            remaining = []
            updated_count = 0
            
            # Check each active bet
            for bet in active_bets:
                matched = False
                
                # Search through all game results
                for date, results_list in game_results.items():
                    for game_result in results_list:
                        match = self.match_bet_with_result(bet, game_result)
                        
                        if match:
                            # Update bet with result
                            bet['result'] = match['result']
                            bet['final_score'] = match['final_score']
                            
                            # Add to tracker
                            tracker['bets'].append(bet)
                            self.log(f"✅ AUTO-UPDATE: {bet.get('game')} → {match['result']} ({match['final_score']})")
                            
                            updated_count += 1
                            matched = True
                            break
                    
                    if matched:
                        break
                
                if not matched:
                    remaining.append(bet)
            
            # Save updated files
            if updated_count > 0:
                # Save tracker with new completed bets
                with open(self.tracker_file, 'w') as f:
                    json.dump(tracker, f, indent=2)
                
                # Save remaining active bets
                active_data['bets'] = remaining
                with open(self.active_bets_file, 'w') as f:
                    json.dump(active_data, f, indent=2)
                
                self.log(f"✅ Updated {updated_count} bet(s) | {len(remaining)} still active")
                
                # Log statistics update
                completed_all = [b for b in tracker['bets'] if b.get('result') in ['WIN', 'LOSS']]
                wins = len([b for b in completed_all if b['result'] == 'WIN'])
                losses = len([b for b in completed_all if b['result'] == 'LOSS'])
                win_rate = int((wins / len(completed_all) * 100)) if completed_all else 0
                
                self.log(f"📈 STATS: {len(completed_all)} bets | {wins}W-{losses}L | {win_rate}% win rate")
            else:
                self.log(f"⏳ No completed games found | {len(remaining)} bets still active")
        
        except Exception as e:
            self.log(f"❌ ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
    
    def run(self):
        """Main entry point"""
        self.log("=" * 60)
        self.log("🎰 LarlBot Auto Result Checker Started")
        self.log("=" * 60)
        
        self.update_completed_bets()
        
        self.log("=" * 60)
        self.log("✅ Check complete")
        self.log("=" * 60)

if __name__ == '__main__':
    checker = AutoResultChecker()
    checker.run()
