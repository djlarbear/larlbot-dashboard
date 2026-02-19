#!/usr/bin/env python3
"""
🎮 Game Status Checker - ESPN/OddsAPI Integration
Checks all active games for status (started/in-progress/finished)
Auto-detects when games have finished and marks WIN/LOSS
"""

import json
import os
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Optional

# Configuration
WORKSPACE = os.environ.get('WORKSPACE', os.getcwd())
ACTIVE_BETS_FILE = f"{WORKSPACE}/active_bets.json"
RANKED_BETS_FILE = f"{WORKSPACE}/ranked_bets.json"
COMPLETED_BETS_FILE = f"{WORKSPACE}/completed_bets_2026-02-16.json"
ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"

# Timezone
EST = pytz.timezone('America/Detroit')

def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST")
    print(f"[{timestamp}] {message}")

def load_json_file(filepath: str) -> Optional[Dict]:
    """Load JSON file safely"""
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        log(f"❌ Error loading {filepath}: {e}")
        return None

def save_json_file(filepath: str, data: Dict):
    """Save JSON file safely"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        log(f"❌ Error saving {filepath}: {e}")
        return False

def get_espn_score(game: str, sport: str = "basketball") -> Optional[Dict]:
    """
    Fetch game score from ESPN API
    Returns: {'home_team': str, 'away_team': str, 'home_score': int, 'away_score': int, 'status': str}
    """
    try:
        # Parse game string (format: "Team A @ Team B")
        if ' @ ' not in game:
            return None
        
        away_team, home_team = game.split(' @ ')
        away_team = away_team.strip()
        home_team = home_team.strip()
        
        # Map sport to ESPN league
        league_map = {
            'basketball': 'basketball/mens-college-basketball',
            'ncaab': 'basketball/mens-college-basketball',
            'nba': 'basketball/nba',
            'nfl': 'football/nfl',
            'nhl': 'hockey/nhl',
            'mlb': 'baseball/mlb'
        }
        
        league = league_map.get(sport.lower(), 'basketball/mens-college-basketball')
        
        # ESPN scoreboard API
        url = f"{ESPN_API_BASE}/{league}/scoreboard"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # Search for matching game
        for event in data.get('events', []):
            competitions = event.get('competitions', [])
            if not competitions:
                continue
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) < 2:
                continue
            
            # Find home and away teams
            home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
            
            if not home or not away:
                continue
            
            espn_home = home.get('team', {}).get('displayName', '')
            espn_away = away.get('team', {}).get('displayName', '')
            
            # Check if teams match (fuzzy match)
            if (home_team.lower() in espn_home.lower() or espn_home.lower() in home_team.lower()) and \
               (away_team.lower() in espn_away.lower() or espn_away.lower() in away_team.lower()):
                
                status = competition.get('status', {}).get('type', {}).get('name', 'Unknown')
                home_score = int(home.get('score', 0))
                away_score = int(away.get('score', 0))
                
                return {
                    'home_team': espn_home,
                    'away_team': espn_away,
                    'home_score': home_score,
                    'away_score': away_score,
                    'status': status,  # 'STATUS_SCHEDULED', 'STATUS_IN_PROGRESS', 'STATUS_FINAL'
                    'game_id': event.get('id'),
                }
        
        return None
    
    except Exception as e:
        log(f"⚠️ ESPN API error for {game}: {e}")
        return None

def calculate_bet_result(bet: Dict, score_data: Dict) -> Optional[str]:
    """
    Calculate if bet was WIN or LOSS based on final score
    Returns: 'WIN', 'LOSS', or None if can't determine
    """
    try:
        bet_type = bet.get('bet_type', '')
        recommendation = bet.get('recommendation', '')
        
        home_score = score_data['home_score']
        away_score = score_data['away_score']
        
        if bet_type == 'SPREAD':
            # Parse spread from recommendation (e.g., "Team A -5.5")
            if '-' in recommendation:
                parts = recommendation.split('-')
                if len(parts) >= 2:
                    spread = float(parts[-1].strip())
                    
                    # Determine if we bet on home or away
                    if score_data['home_team'].lower() in recommendation.lower():
                        # We bet on home team
                        adjusted_score = home_score - spread
                        return 'WIN' if adjusted_score > away_score else 'LOSS'
                    else:
                        # We bet on away team
                        adjusted_score = away_score - spread
                        return 'WIN' if adjusted_score > home_score else 'LOSS'
            
            elif '+' in recommendation:
                parts = recommendation.split('+')
                if len(parts) >= 2:
                    spread = float(parts[-1].strip())
                    
                    if score_data['home_team'].lower() in recommendation.lower():
                        adjusted_score = home_score + spread
                        return 'WIN' if adjusted_score > away_score else 'LOSS'
                    else:
                        adjusted_score = away_score + spread
                        return 'WIN' if adjusted_score > home_score else 'LOSS'
        
        elif bet_type == 'TOTAL':
            # Parse over/under (e.g., "OVER 150.5" or "UNDER 145")
            total_score = home_score + away_score
            
            if 'OVER' in recommendation.upper():
                target = float(recommendation.split()[-1])
                return 'WIN' if total_score > target else 'LOSS'
            
            elif 'UNDER' in recommendation.upper():
                target = float(recommendation.split()[-1])
                return 'WIN' if total_score < target else 'LOSS'
        
        elif bet_type == 'MONEYLINE':
            # Determine which team we bet on
            if score_data['home_team'].lower() in recommendation.lower():
                return 'WIN' if home_score > away_score else 'LOSS'
            elif score_data['away_team'].lower() in recommendation.lower():
                return 'WIN' if away_score > home_score else 'LOSS'
        
        return None
    
    except Exception as e:
        log(f"⚠️ Error calculating result: {e}")
        return None

def check_game_status(bet: Dict) -> Dict:
    """
    Check status of a single bet's game
    Returns: {'status': str, 'score_data': Dict, 'result': str, 'final_score': str}
    """
    game = bet.get('game', '')
    sport = bet.get('sport', 'basketball')
    
    log(f"🔍 Checking: {game}")
    
    score_data = get_espn_score(game, sport)
    
    if not score_data:
        log(f"   ⏳ No score data available (game not started or API error)")
        return {'status': 'PENDING', 'score_data': None, 'result': None, 'final_score': None}
    
    status = score_data['status']
    
    if 'FINAL' in status:
        log(f"   ✅ Game finished: {score_data['away_team']} {score_data['away_score']} @ {score_data['home_team']} {score_data['home_score']}")
        
        result = calculate_bet_result(bet, score_data)
        final_score = f"{score_data['away_score']}-{score_data['home_score']}"
        
        if result:
            log(f"   🎯 Result: {result}")
        else:
            log(f"   ⚠️ Could not determine result")
        
        return {
            'status': 'FINAL',
            'score_data': score_data,
            'result': result,
            'final_score': final_score
        }
    
    elif 'IN_PROGRESS' in status:
        log(f"   🏀 In progress: {score_data['away_score']}-{score_data['home_score']}")
        return {
            'status': 'IN_PROGRESS',
            'score_data': score_data,
            'result': None,
            'final_score': None
        }
    
    else:
        log(f"   ⏰ Scheduled")
        return {
            'status': 'SCHEDULED',
            'score_data': score_data,
            'result': None,
            'final_score': None
        }

def move_to_completed(bet: Dict, result: str, final_score: str):
    """Move a finished bet to completed_bets file"""
    try:
        # Update bet with result
        bet['result'] = result
        bet['final_score'] = final_score
        bet['completed_at'] = datetime.now(EST).isoformat()
        
        # Load completed bets file
        completed_data = load_json_file(COMPLETED_BETS_FILE)
        if not completed_data:
            completed_data = {
                'date': datetime.now(EST).strftime('%Y-%m-%d'),
                'bets': []
            }
        
        # Add to completed
        completed_data['bets'].append(bet)
        
        # Save
        save_json_file(COMPLETED_BETS_FILE, completed_data)
        
        log(f"   ✅ Moved to completed_bets: {bet['game']} - {result}")
        return True
    
    except Exception as e:
        log(f"   ❌ Failed to move to completed: {e}")
        return False

def update_all_game_statuses():
    """Check all active bets and update statuses"""
    log("=" * 70)
    log("🎮 Game Status Checker - Starting Update Cycle")
    log("=" * 70)
    
    # Load active bets
    active_data = load_json_file(ACTIVE_BETS_FILE)
    if not active_data or 'bets' not in active_data:
        log("⚠️ No active bets found")
        return
    
    all_bets = active_data.get('bets', [])
    log(f"📊 Checking {len(all_bets)} active bets")
    
    # Also load ranked bets to update
    ranked_data = load_json_file(RANKED_BETS_FILE)
    
    finished_count = 0
    in_progress_count = 0
    scheduled_count = 0
    
    remaining_bets = []
    
    for bet in all_bets:
        # Skip if already has result
        if bet.get('result') in ['WIN', 'LOSS']:
            log(f"⏭️ Skipping {bet.get('game')} - already has result: {bet.get('result')}")
            move_to_completed(bet, bet['result'], bet.get('final_score', 'N/A'))
            continue
        
        # Check game status
        status_info = check_game_status(bet)
        
        if status_info['status'] == 'FINAL' and status_info['result']:
            # Game finished - move to completed
            finished_count += 1
            move_to_completed(bet, status_info['result'], status_info['final_score'])
            
            # Update ranked_bets.json if this bet is in top 10
            if ranked_data and 'top_10' in ranked_data:
                for ranked_item in ranked_data['top_10']:
                    ranked_bet = ranked_item.get('full_bet', {})
                    if ranked_bet.get('game') == bet['game']:
                        ranked_bet['result'] = status_info['result']
                        ranked_bet['final_score'] = status_info['final_score']
                        ranked_bet['completed_at'] = datetime.now(EST).isoformat()
        
        elif status_info['status'] == 'IN_PROGRESS':
            in_progress_count += 1
            remaining_bets.append(bet)
        
        else:  # SCHEDULED or PENDING
            scheduled_count += 1
            remaining_bets.append(bet)
    
    # Update active_bets.json (remove finished games)
    active_data['bets'] = remaining_bets
    active_data['last_updated'] = datetime.now(EST).isoformat()
    save_json_file(ACTIVE_BETS_FILE, active_data)
    
    # Update ranked_bets.json
    if ranked_data:
        ranked_data['last_updated'] = datetime.now(EST).isoformat()
        save_json_file(RANKED_BETS_FILE, ranked_data)
    
    log("=" * 70)
    log("✅ Update Cycle Complete")
    log(f"   🏁 Finished: {finished_count}")
    log(f"   🏀 In Progress: {in_progress_count}")
    log(f"   ⏰ Scheduled: {scheduled_count}")
    log(f"   📊 Remaining Active: {len(remaining_bets)}")
    log("=" * 70)

if __name__ == "__main__":
    update_all_game_statuses()
