#!/usr/bin/env python3
"""
Fetch today's game results from ESPN and update ranked_bets.json with WIN/LOSS
"""

import json
import requests
from datetime import datetime
import pytz
import re
import sys

def extract_teams(game_str):
    """Extract teams from game string like 'Team A @ Team B'"""
    parts = game_str.split(' @ ')
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None

def get_ncaa_basketball_scores():
    """Fetch NCAA basketball scores from ESPN"""
    scores = {}
    try:
        url = "https://www.espn.com/mens-college-basketball/scores"
        response = requests.get(url, timeout=10)
        
        # Simple regex-based parsing
        # Look for patterns like "Team1 Score - Score Team2"
        pattern = r'([A-Za-z\s]+?)\s+(\d+)\s*-\s*(\d+)\s+([A-Za-z\s]+)'
        
        # Try JSON API instead
        api_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
        api_response = requests.get(api_url, timeout=10)
        
        if api_response.status_code == 200:
            data = api_response.json()
            for event in data.get('events', []):
                try:
                    # Get teams and scores
                    competitors = event.get('competitions', [{}])[0].get('competitors', [])
                    if len(competitors) >= 2:
                        away_team = competitors[0].get('team', {}).get('displayName', '')
                        home_team = competitors[1].get('team', {}).get('displayName', '')
                        away_score = int(competitors[0].get('score', 0) or 0)
                        home_score = int(competitors[1].get('score', 0) or 0)
                        status = event.get('status', {}).get('type', {}).get('state', '')
                        
                        if away_team and home_team:
                            key = f"{away_team} @ {home_team}"
                            scores[key] = {
                                'away_score': away_score,
                                'home_score': home_score,
                                'final_score': f"{away_score}-{home_score}",
                                'status': status
                            }
                except Exception as e:
                    print(f"Error parsing event: {e}")
        
        return scores
    except Exception as e:
        print(f"Error fetching NCAA scores: {e}")
        return {}

def calculate_bet_result(game_result, bet_type, recommendation):
    """Calculate if bet won or lost"""
    try:
        away_score = game_result['away_score']
        home_score = game_result['home_score']
        margin = home_score - away_score
        
        if bet_type.upper() == 'SPREAD':
            # Extract spread from recommendation like "Team -11.5"
            match = re.search(r'([+-])(\d+\.?\d*)', recommendation)
            if not match:
                return None
            
            sign = match.group(1)
            spread = float(match.group(2))
            
            # Extract team name
            team_match = recommendation.split(sign)[0].strip()
            
            if sign == '-':
                # Favorite (negative spread)
                # Favorite covers if they win by MORE than the spread
                if margin > spread:
                    return 'WIN'
                else:
                    return 'LOSS'
            else:
                # Underdog (positive spread)
                # Underdog covers if they lose by LESS than the spread or win
                if margin < spread:
                    return 'WIN'
                else:
                    return 'LOSS'
        
        elif bet_type.upper() == 'TOTAL' or 'UNDER' in recommendation.upper() or 'OVER' in recommendation.upper():
            # Extract total from recommendation
            match = re.search(r'(\d+\.?\d*)', recommendation)
            if not match:
                return None
            
            total_line = float(match.group(1))
            actual_total = away_score + home_score
            
            is_under = 'UNDER' in recommendation.upper()
            
            if is_under:
                return 'WIN' if actual_total < total_line else 'LOSS'
            else:
                return 'WIN' if actual_total > total_line else 'LOSS'
        
        elif 'MONEYLINE' in bet_type.upper() or 'MONEYLINE' in recommendation.upper():
            # Extract team from recommendation
            team_match = recommendation.split('(Moneyline)')[0].strip() if '(Moneyline)' in recommendation else recommendation.strip()
            
            if margin > 0:
                # Home team won
                return 'WIN' if 'home' in team_match.lower() else 'LOSS'
            else:
                # Away team won
                return 'WIN' if 'away' in team_match.lower() else 'LOSS'
        
        return None
    except Exception as e:
        print(f"Error calculating result: {e}")
        return None

def update_ranked_bets_with_results():
    """Update ranked_bets.json with actual game results"""
    print("📊 Fetching today's results...")
    
    # Get today's scores
    scores = get_ncaa_basketball_scores()
    print(f"✅ Fetched {len(scores)} game results")
    
    # Load ranked bets
    with open('ranked_bets.json', 'r') as f:
        ranked = json.load(f)
    
    # Update top 10 with results
    for item in ranked.get('top_10', []):
        full_bet = item.get('full_bet', {})
        game = full_bet.get('game', '')
        
        # Try to find matching game result
        game_result = None
        for score_key, score_val in scores.items():
            # Fuzzy match game names
            if normalize_team_name(game.split(' @ ')[0]) in normalize_team_name(score_key):
                game_result = score_val
                break
        
        if game_result:
            # Calculate result
            bet_result = calculate_bet_result(
                game_result,
                full_bet.get('bet_type', ''),
                full_bet.get('recommendation', '')
            )
            
            if bet_result:
                full_bet['result'] = bet_result
                full_bet['final_score'] = game_result['final_score']
                full_bet['away_score'] = game_result['away_score']
                full_bet['home_score'] = game_result['home_score']
                print(f"  {full_bet.get('recommendation', 'BET')} → {bet_result} ({game_result['final_score']})")
    
    # Save updated ranked bets
    with open('ranked_bets.json', 'w') as f:
        json.dump(ranked, f, indent=2)
    
    print("✅ Updated ranked_bets.json")
    
    # Calculate stats
    wins = sum(1 for item in ranked.get('top_10', []) if item.get('full_bet', {}).get('result') == 'WIN')
    losses = sum(1 for item in ranked.get('top_10', []) if item.get('full_bet', {}).get('result') == 'LOSS')
    print(f"\n📈 Today's record: {wins}W - {losses}L ({len(ranked.get('top_10', []))} total)")

def normalize_team_name(name):
    """Normalize team name for comparison"""
    # Remove mascots and special characters
    name = name.lower().strip()
    # Remove common mascot words
    for mascot in ['bearcats', 'terrapins', 'utes', 'jaspers', 'pioneers', 'mavericks', 'hoosiers', 'fighting illini', 'bulldogs', 'panthers', 'broncs', 'scarlet knights', '49ers', 'golden griffins']:
        name = name.replace(mascot, '')
    return ' '.join(name.split())

if __name__ == '__main__':
    update_ranked_bets_with_results()
