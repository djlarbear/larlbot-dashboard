#!/usr/bin/env python3
"""
Auto Result Tracker v3.0 - Complete Automated Bet Tracking
Features:
- Fetches completed games from OddsAPI
- Matches active bets to game results
- Handles: Spreads, Moneylines, Over/Unders
- Moves completed bets to Previous Results
- Sends Telegram notifications
- Updates win/loss tracking
"""

import json
import requests
from datetime import datetime, timezone, timedelta
import sys
import re
import os

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

class AutoResultTracker:
    def __init__(self):
        self.api_key = '82865426fd192e243376eb4e51185f3b'
        self.base_url = "https://api.the-odds-api.com/v4"
        self.active_bets_file = 'active_bets.json'
        self.tracker_file = 'bet_tracker_input.json'
        self.log_file = 'bet_tracking.log'
        
        self.sports = [
            {'key': 'basketball_ncaab', 'display': 'NCAA Basketball'},
            {'key': 'basketball_nba', 'display': 'NBA'},
            {'key': 'americanfootball_nfl', 'display': 'NFL'},
            {'key': 'baseball_mlb', 'display': 'MLB'},
            {'key': 'americanfootball_ncaaf', 'display': 'College Football'},
            {'key': 'ice_hockey_nhl', 'display': 'NHL'},
            {'key': 'soccer_epl', 'display': 'Premier League'},
        ]
    
        """Load Telegram credentials if available"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
        except:
            pass
    
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
        """Send Telegram notification"""
            return
        
        try:
            data = {
                'text': message,
                'parse_mode': 'HTML'
            }
            requests.post(url, json=data, timeout=5)
        except Exception as e:
            self.log(f"⚠️  Telegram error: {e}")
    
    def normalize_team_name(self, name):
        """Normalize team names for matching"""
        if not name:
            return ""
        
        # Common abbreviations
        replacements = {
            "north carolina state": "nc state",
            "southern california": "usc",
            "mississippi": "ole miss",
            "brigham young": "byu",
            "north carolina": "unc",
            "texas am": "texas a&m",
            "penn state": "psu",
            "ohio state": "osu",
            "alabama crimson tide": "alabama",
            "arkansas razorbacks": "arkansas",
            "iowa state cyclones": "iowa state",
            "kansas jayhawks": "kansas",
            "michigan wolverines": "michigan",
            "ucla bruins": "ucla",
            "uconn huskies": "uconn",
        }
        
        name_lower = name.lower().strip()
        for long_form, short_form in replacements.items():
            if long_form in name_lower:
                name_lower = name_lower.replace(long_form, short_form)
        
        return name_lower
    
    def fetch_completed_games(self, sport_key):
        """Fetch completed games from OddsAPI"""
        try:
            url = f"{self.base_url}/sports/{sport_key}/scores"
            params = {
                'api_key': self.api_key,
                'daysFrom': 1,  # Last 1 day
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                games = response.json()
                # Filter for completed games only
                completed = [g for g in games if g.get('completed') == True]
                return completed
            elif response.status_code == 429:
                self.log(f"⚠️  Rate limited")
                return []
            else:
                return []
        except Exception as e:
            self.log(f"⚠️  Error fetching {sport_key}: {e}")
            return []
    
    def match_bet_to_game(self, bet, game):
        """Match a bet to a completed game"""
        bet_game = self.normalize_team_name(bet.get('game', ''))
        game_away = self.normalize_team_name(game.get('away_team', ''))
        game_home = self.normalize_team_name(game.get('home_team', ''))
        
        # Check if teams match
        if not (game_away in bet_game or game_home in bet_game):
            return None
        
        # Get scores - only if game is actually completed
        try:
            away_score = int(game.get('away_score', -1))
            home_score = int(game.get('home_score', -1))
            
            # Skip games with 0-0 or invalid scores (likely incomplete)
            if away_score < 0 or home_score < 0:
                return None
            
            # NCAA basketball games should have scores > 50
            # NFL/NHL/MLB would be different, but 0-0 is always incomplete
            if away_score == 0 and home_score == 0:
                return None
        except:
            return None
        
        return {
            'away_score': away_score,
            'home_score': home_score,
            'final_score': f"{away_score}-{home_score}",
            'away_team': game_away,
            'home_team': game_home
        }
    
    def calculate_bet_result(self, bet, game_match):
        """Calculate if bet was WIN or LOSS"""
        bet_type = bet.get('bet_type', '').upper()
        recommendation = bet.get('recommendation', '').upper()
        
        away_score = game_match['away_score']
        home_score = game_match['home_score']
        away_team = game_match['away_team']
        home_team = game_match['home_team']
        
        try:
            if bet_type == 'SPREAD':
                # Extract spread value
                numbers = re.findall(r'[-+]?\d+\.?\d*', recommendation)
                if not numbers:
                    return None
                
                spread = float(numbers[0])
                
                # Determine which team was bet on
                if any(team_part in recommendation for team_part in away_team.split()):
                    # Bet on away team with spread
                    if away_score + spread > home_score:
                        return 'WIN'
                    else:
                        return 'LOSS'
                else:
                    # Bet on home team with spread
                    if home_score + spread > away_score:
                        return 'WIN'
                    else:
                        return 'LOSS'
            
            elif bet_type == 'MONEYLINE':
                # Determine which team was bet on
                if any(team_part in recommendation for team_part in away_team.split()):
                    # Bet on away team to win
                    return 'WIN' if away_score > home_score else 'LOSS'
                else:
                    # Bet on home team to win
                    return 'WIN' if home_score > away_score else 'LOSS'
            
            elif bet_type == 'TOTAL':
                # Extract total value
                numbers = re.findall(r'\d+\.?\d*', recommendation)
                if not numbers:
                    return None
                
                total = float(numbers[-1])
                combined = away_score + home_score
                
                if 'UNDER' in recommendation:
                    return 'WIN' if combined < total else 'LOSS'
                else:  # OVER
                    return 'WIN' if combined > total else 'LOSS'
        
        except Exception as e:
            self.log(f"⚠️  Error calculating result for {bet.get('game')}: {e}")
            return None
        
        return None
    
    def process_active_bets(self):
        """Process active bets and move completed ones to tracker"""
        try:
            # Load active bets
            with open(self.active_bets_file, 'r') as f:
                active_data = json.load(f)
            
            active_bets = active_data.get('bets', [])
            
            if not active_bets:
                self.log("✅ No active bets to check")
                return
            
            self.log(f"📊 Processing {len(active_bets)} active bets...")
            
            # Fetch completed games from all sports
            all_games = []
            for sport in self.sports:
                games = self.fetch_completed_games(sport['key'])
                all_games.extend(games)
            
            if not all_games:
                self.log(f"⏳ No completed games found yet ({len(active_bets)} bets still active)")
                return
            
            self.log(f"🔍 Found {len(all_games)} completed games")
            
            # Load tracker for historical bets
            with open(self.tracker_file, 'r') as f:
                tracker = json.load(f)
            
            completed_bets = []
            remaining_bets = []
            
            # Match each active bet to completed games
            for bet in active_bets:
                matched = False
                
                for game in all_games:
                    game_match = self.match_bet_to_game(bet, game)
                    
                    if game_match:
                        # Calculate result
                        result = self.calculate_bet_result(bet, game_match)
                        
                        if result:
                            # Add result to bet
                            bet['result'] = result
                            bet['final_score'] = game_match['final_score']
                            
                            # Add date if not present
                            if 'date' not in bet:
                                bet['date'] = datetime.now().strftime('%Y-%m-%d')
                            
                            # Move to tracker
                            tracker['bets'].append(bet)
                            completed_bets.append(bet)
                            
                            msg = f"✅ {bet.get('game')} → <b>{result}</b> ({game_match['final_score']})"
                            self.log(msg)
                            
                            matched = True
                            break
                
                if not matched:
                    remaining_bets.append(bet)
            
            # Save updated files
            if completed_bets:
                # Update tracker
                with open(self.tracker_file, 'w') as f:
                    json.dump(tracker, f, indent=2)
                
                # Update active bets
                active_data['bets'] = remaining_bets
                with open(self.active_bets_file, 'w') as f:
                    json.dump(active_data, f, indent=2)
                
                self.log(f"\n✅ MOVED {len(completed_bets)} BETS TO PREVIOUS RESULTS")
                
                # Show summary
                wins = sum(1 for b in completed_bets if b.get('result') == 'WIN')
                losses = sum(1 for b in completed_bets if b.get('result') == 'LOSS')
                self.log(f"   {wins}W - {losses}L from this round")
                self.log(f"   {len(remaining_bets)} bets still active\n")
                
                # Calculate overall stats
                all_completed = [b for b in tracker['bets'] if b.get('result') in ['WIN', 'LOSS']]
                if all_completed:
                    total_wins = sum(1 for b in all_completed if b.get('result') == 'WIN')
                    total_losses = sum(1 for b in all_completed if b.get('result') == 'LOSS')
                    total_rate = int((total_wins / len(all_completed) * 100))
                    
                    stats = f"📈 TOTAL STATS: {len(all_completed)} bets | {total_wins}W-{total_losses}L | {total_rate}% win rate"
                    self.log(stats)
            else:
                self.log(f"⏳ No new completed games | {len(remaining_bets)} bets still active")
        
        except Exception as e:
            self.log(f"❌ ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
    
    def run(self):
        """Main entry point"""
        self.log("=" * 70)
        self.log("🎰 LarlBot Auto Result Tracker v3.0")
        self.log("=" * 70)
        
        self.process_active_bets()
        
        self.log("=" * 70)
        self.log("✅ Auto check complete")
        self.log("=" * 70)

if __name__ == '__main__':
    tracker = AutoResultTracker()
    tracker.run()
