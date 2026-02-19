#!/usr/bin/env python3
"""
Auto Result Tracker v4.0 - ESPN-Powered Real Scores
Features:
- Uses ESPN API for REAL final scores (not OddsAPI 0-0 placeholders)
- Handles: Spreads, Moneylines, Over/Unders
- Moves completed bets to completed_bets_YYYY-MM-DD.json
- Sends Telegram notifications
- Multi-sport support (NCAA, NBA, NFL, MLB, NHL, CFB, Soccer)
"""

import json
import requests
from datetime import datetime, timezone, timedelta
import sys
import re
import os

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

class AutoResultTrackerV2:
    def __init__(self):
        self.active_bets_file = 'active_bets.json'
        self.log_file = 'bet_tracking.log'
        
        # ESPN API endpoints by sport
        self.espn_endpoints = {
            'NCAA Basketball': 'basketball/mens-college-basketball',
            'NBA': 'basketball/nba',
            'NFL': 'football/nfl',
            'MLB': 'baseball/mlb',
            'NHL': 'hockey/nhl',
            'College Football': 'football/college-football',
            'Premier League': 'soccer/eng.1'
        }
    
        """Load Telegram credentials if available"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
        except:
            pass
    
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        print(f"{timestamp} {message}")
    
    def fetch_espn_scores(self, sport, date_str):
        """Fetch completed games from ESPN for a specific date"""
        endpoint = self.espn_endpoints.get(sport)
        if not endpoint:
            return []
        
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/{endpoint}/scoreboard"
            params = {
                'limit': 300,
                'dates': date_str.replace('-', '')  # ESPN wants YYYYMMDD
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                scores = []
                
                for event in data.get('events', []):
                    status = event.get('status', {})
                    if status.get('type', {}).get('completed') == True:
                        competitors = event.get('competitions', [{}])[0].get('competitors', [])
                        if len(competitors) == 2:
                            away = competitors[1] if competitors[1].get('homeAway') == 'away' else competitors[0]
                            home = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]
                            
                            away_score = int(away.get('score', 0))
                            home_score = int(home.get('score', 0))
                            
                            # Skip games with 0-0 scores (incomplete data)
                            if away_score > 0 or home_score > 0:
                                scores.append({
                                    'away_team': away.get('team', {}).get('displayName', ''),
                                    'home_team': home.get('team', {}).get('displayName', ''),
                                    'away_score': away_score,
                                    'home_score': home_score,
                                    'completed': True
                                })
                
                return scores
        except Exception as e:
            self.log(f"⚠️  ESPN error for {sport}: {e}")
            return []
    
    def normalize_team_name(self, name):
        """Normalize team name for matching"""
        # Remove common suffixes
        name = re.sub(r'\s+(Tigers|Bears|Eagles|Wildcats|Bulldogs|Aggies|Huskies|Cougars|Panthers|Rams|Lions|Trojans|Warriors|Cardinals|Cyclones|Jayhawks|Hoyas|Horned Frogs|Cowboys|Yellow Jackets|Fighting Irish|Blue Devils|Wolverines|Red Storm|Friars|Boilermakers|Hawkeyes|Red Raiders|Gators|Gamecocks|Crimson Tide|Highlanders|Tritons|Hornets|Lumberjacks|Jackrabbits|Golden Eagles|Wolf Pack|Aztecs|Titans|Anteaters|Gaels|Blue Raiders|Hilltoppers|Golden Gophers|Matadors|Tommies|Kangaroos|Thundering Herd|Rainbow Warriors)\s*$', '', name, flags=re.IGNORECASE)
        
        # Team name replacements
        replacements = {
            'Hawai\'i': 'Hawaii',
            'CSU Northridge': 'Cal St Northridge',
            'Cal State Northridge': 'Cal St Northridge',
            'St. Thomas (MN)': 'St Thomas',
            'UMKC': 'Missouri Kansas City',
            'UC San Diego': 'UC San Diego',
            'UC Riverside': 'UC Riverside',
            'UC Irvine': 'UC Irvine',
            'CSU Fullerton': 'Cal St Fullerton',
            'Cal State Fullerton': 'Cal St Fullerton',
            'Saint Mary\'s': 'Saint Marys',
            'South Dakota St': 'South Dakota State',
            'Sacramento St': 'Sacramento State',
            'San Diego St': 'San Diego State',
            'Utah State': 'Utah St',
            'Middle Tennessee': 'Middle Tennessee',
            'Western Kentucky': 'Western Kentucky',
        }
        
        for old, new in replacements.items():
            if old.lower() in name.lower():
                name = re.sub(old, new, name, flags=re.IGNORECASE)
        
        return name.strip().lower()
    
    def match_bet_to_score(self, bet_game, sport, scores):
        """Match bet to ESPN score"""
        bet_normalized = self.normalize_team_name(bet_game)
        
        for score in scores:
            away_norm = self.normalize_team_name(score['away_team'])
            home_norm = self.normalize_team_name(score['home_team'])
            
            # Check if both teams appear in bet string
            if (away_norm in bet_normalized or bet_normalized.find(away_norm) >= 0) and \
               (home_norm in bet_normalized or bet_normalized.find(home_norm) >= 0):
                return score
        
        return None
    
    def calculate_bet_result(self, bet, score):
        """Calculate WIN/LOSS for bet"""
        bet_type = bet.get('bet_type', '').upper()
        recommendation = bet.get('recommendation', '')
        away_score = score['away_score']
        home_score = score['home_score']
        
        if bet_type == 'SPREAD':
            # Extract spread and team
            numbers = re.findall(r'[-+]?\d+\.?\d*', recommendation)
            if not numbers:
                return 'UNKNOWN'
            
            spread = float(numbers[0])
            
            # Determine which team was bet on
            if score['away_team'].split()[0].lower() in recommendation.lower():
                # Bet on away team
                final_margin = away_score + spread - home_score
            else:
                # Bet on home team  
                final_margin = home_score + spread - away_score
            
            return 'WIN' if final_margin > 0 else 'LOSS'
        
        elif bet_type == 'TOTAL':
            total = float(re.findall(r'\d+\.?\d*', recommendation)[0])
            actual_total = away_score + home_score
            
            if 'OVER' in recommendation.upper():
                return 'WIN' if actual_total > total else 'LOSS'
            else:  # UNDER
                return 'WIN' if actual_total < total else 'LOSS'
        
        elif bet_type == 'MONEYLINE':
            # Extract team from recommendation
            if score['away_team'].split()[0].lower() in recommendation.lower():
                return 'WIN' if away_score > home_score else 'LOSS'
            else:
                return 'WIN' if home_score > away_score else 'LOSS'
        
        return 'UNKNOWN'
    
    def process_bets(self):
        """Main processing loop"""
        self.log("=" * 70)
        self.log("🎰 LarlBot Auto Result Tracker v4.0 (ESPN-Powered)")
        self.log("=" * 70)
        
        # Load active bets
        try:
            with open(self.active_bets_file, 'r') as f:
                active_data = json.load(f)
        except:
            self.log("⚠️  No active bets found")
            return
        
        bets = active_data.get('bets', [])
        bet_date = active_data.get('date', '')
        
        if not bets:
            self.log("⏳ No active bets to check")
            return
        
        self.log(f"📊 Processing {len(bets)} active bets from {bet_date}...")
        
        # Fetch ESPN scores for each sport
        sport_scores = {}
        for sport_key in self.espn_endpoints.keys():
            scores = self.fetch_espn_scores(sport_key, bet_date)
            if scores:
                sport_scores[sport_key] = scores
                self.log(f"✅ {sport_key}: {len(scores)} completed games")
        
        # Match and process each bet
        completed_bets = []
        active_bets = []
        
        for bet in bets:
            sport = bet.get('sport', '').replace('🏀 ', '').replace('🏈 ', '').replace('⚾ ', '').replace('🏒 ', '').replace('⚽ ', '').strip()
            
            scores = sport_scores.get(sport, [])
            if not scores:
                active_bets.append(bet)
                continue
            
            score = self.match_bet_to_score(bet['game'], sport, scores)
            
            if score:
                result = self.calculate_bet_result(bet, score)
                bet['result'] = result
                bet['final_score'] = f"{score['away_score']}-{score['home_score']}"
                bet['away_score'] = score['away_score']
                bet['home_score'] = score['home_score']
                bet['completed_at'] = datetime.now(timezone.utc).isoformat()
                completed_bets.append(bet)
                
                emoji = '✅' if result == 'WIN' else '❌' if result == 'LOSS' else '❓'
                self.log(f"{emoji} {bet['game'][:50]} | {result} | {bet['final_score']}")
                
                # Send Telegram notification
                msg = f"{emoji} <b>{result}</b>\n{bet['game']}\n{bet['recommendation']}\nScore: {bet['final_score']}"
            else:
                active_bets.append(bet)
        
        # Save completed bets to dated file
        if completed_bets:
            completed_file = f"completed_bets_{bet_date}.json"
            
            # Load existing completed bets if file exists
            try:
                with open(completed_file, 'r') as f:
                    existing = json.load(f)
                    existing_bets = existing.get('bets', [])
            except:
                existing_bets = []
            
            # Merge and deduplicate
            all_completed = existing_bets + completed_bets
            seen = set()
            unique_bets = []
            for bet in all_completed:
                key = (bet['game'], bet.get('bet_type'), bet.get('recommendation'))
                if key not in seen:
                    seen.add(key)
                    unique_bets.append(bet)
            
            completed_data = {
                'date': bet_date,
                'bets': unique_bets,
                'stats': {
                    'total_bets': len(unique_bets),
                    'wins': len([b for b in unique_bets if b.get('result') == 'WIN']),
                    'losses': len([b for b in unique_bets if b.get('result') == 'LOSS']),
                    'pending': len([b for b in unique_bets if b.get('result') == 'PENDING']),
                }
            }
            
            with open(completed_file, 'w') as f:
                json.dump(completed_data, f, indent=2)
            
            self.log(f"💾 Saved {len(completed_bets)} new results to {completed_file}")
        
        # Update active bets file
        active_data['bets'] = active_bets
        with open(self.active_bets_file, 'w') as f:
            json.dump(active_data, f, indent=2)
        
        self.log("=" * 70)
        self.log(f"✅ Completed: {len(completed_bets)} | Active: {len(active_bets)}")
        self.log("=" * 70)

if __name__ == '__main__':
    tracker = AutoResultTrackerV2()
    tracker.process_bets()
