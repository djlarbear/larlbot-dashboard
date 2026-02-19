#!/usr/bin/env python3
"""
SWORD: ESPN Hidden API Result Fetcher
Fetches college basketball scores and updates bet results
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import re

ESPN_SCOREBOARD_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

def fetch_espn_scores(date_str=None):
    """
    Fetch ESPN scoreboard for college basketball
    date_str: 'YYYY-MM-DD' or None for today
    Returns: list of games with scores
    """
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Convert to YYYYMMDD format for ESPN
    espn_date = date_str.replace('-', '')
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏀 Fetching ESPN scores for {date_str}...")
    
    try:
        # Fetch scoreboard
        params = {'dates': espn_date}
        response = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        games = []
        
        # Parse events (games)
        for event in data.get('events', []):
            game_info = {
                'name': event.get('name', ''),
                'date': event.get('date', ''),
                'status': event.get('status', {}).get('type', ''),
                'competitions': []
            }
            
            for comp in event.get('competitions', []):
                # Get team info and scores
                competitors = comp.get('competitors', [])
                if len(competitors) >= 2:
                    away = competitors[1]  # Away team (typically listed second)
                    home = competitors[0]  # Home team
                    
                    away_team = away.get('team', {}).get('displayName', 'Unknown')
                    home_team = home.get('team', {}).get('displayName', 'Unknown')
                    away_score = away.get('score', 'TBD')
                    home_score = home.get('score', 'TBD')
                    
                    game_info['competitors'] = {
                        'away': {'team': away_team, 'score': away_score},
                        'home': {'team': home_team, 'score': home_score},
                        'matchup': f"{away_team} @ {home_team}"
                    }
                    
                    games.append(game_info)
            
            if game_info['competitors']:
                games.append(game_info)
        
        print(f"✅ Found {len(games)} games on {date_str}")
        return games
    
    except Exception as e:
        print(f"❌ Error fetching ESPN scores: {e}")
        return []

def match_game_to_bet(espn_matchup, bet_game):
    """
    Try to match ESPN game to our bet game
    Returns: True if matched, False otherwise
    """
    
    # Extract school names (first word before first space usually)
    def extract_schools(s):
        # Handle "Team Name @ Team Name" format
        if '@' in s:
            away, home = s.split('@')
        else:
            return []
        
        # Get first significant word from each
        def get_school_name(team):
            # Handle special cases
            team = team.strip()
            if 'State' in team:
                # e.g., "North Carolina State" or "Florida State"
                parts = team.split()
                if len(parts) >= 2:
                    return parts[0] + ' ' + parts[1]
            # Just get first word for most teams
            return team.split()[0] if team else ''
        
        away_school = get_school_name(away)
        home_school = get_school_name(home)
        return {away_school.lower(), home_school.lower()}
    
    espn_schools = extract_schools(espn_matchup)
    bet_schools = extract_schools(bet_game)
    
    # If we found both sets of schools, compare
    if espn_schools and bet_schools and espn_schools == bet_schools:
        return True
    
    # Fallback: check if names contain the same key words
    espn_lower = espn_matchup.lower()
    bet_lower = bet_game.lower()
    
    # Check if major school names appear in both
    for word in bet_lower.split():
        if len(word) > 3 and word in espn_lower:
            # Found a matching word, might be the same game
            # Try to confirm with a second school name
            for word2 in bet_lower.split():
                if word2 != word and len(word2) > 3 and word2 in espn_lower:
                    return True
    
    return False

def determine_win_loss(bet, espn_game):
    """
    Determine if bet WON or LOST based on final score and our pick
    """
    
    away_score = espn_game['competitors']['away']['score']
    home_score = espn_game['competitors']['home']['score']
    
    # Can't determine if scores aren't final numbers
    if away_score == 'TBD' or home_score == 'TBD':
        return 'PENDING', None
    
    try:
        away_score = int(away_score)
        home_score = int(home_score)
    except:
        return 'PENDING', None
    
    bet_type = bet.get('bet_type', '').upper()
    recommendation = bet.get('recommendation', '')
    
    # Determine winner
    if home_score > away_score:
        winner = 'home'
        margin = home_score - away_score
    else:
        winner = 'away'
        margin = away_score - home_score
    
    final_score = f"{away_score}-{home_score}"
    
    if bet_type == 'SPREAD':
        # Extract spread from recommendation
        # Example: "Duke Blue Devils -19.5" or "Syracuse Orange 19.5"
        spread_match = re.search(r'([+-]?\d+\.?\d*)', recommendation)
        if spread_match:
            spread = float(spread_match.group(1))
            
            # Determine if our pick covers the spread
            if 'home' in recommendation.lower() or recommendation.split()[-1].startswith('-'):
                # We're betting on home team
                if winner == 'home' and margin >= abs(spread):
                    return 'WIN', final_score
                else:
                    return 'LOSS', final_score
            else:
                # We're betting on away team
                if winner == 'away' and margin >= abs(spread):
                    return 'WIN', final_score
                else:
                    return 'LOSS', final_score
    
    elif bet_type == 'TOTAL':
        # Extract total from recommendation
        # Example: "Over 150.5" or "Under 135"
        if 'Over' in recommendation or 'over' in recommendation:
            total_match = re.search(r'\d+\.?\d*', recommendation)
            if total_match:
                total = float(total_match.group())
                combined = away_score + home_score
                return ('WIN', final_score) if combined > total else ('LOSS', final_score)
        elif 'Under' in recommendation or 'under' in recommendation:
            total_match = re.search(r'\d+\.?\d*', recommendation)
            if total_match:
                total = float(total_match.group())
                combined = away_score + home_score
                return ('WIN', final_score) if combined < total else ('LOSS', final_score)
    
    return 'PENDING', final_score

def update_completed_bets(date_str, espn_games):
    """
    Update completed_bets file with ESPN results
    """
    
    workspace = Path('/Users/macmini/.openclaw/workspace')
    bets_file = workspace / f'completed_bets_{date_str}.json'
    
    if not bets_file.exists():
        print(f"⚠️ {bets_file} not found - skipping")
        return 0
    
    with open(bets_file) as f:
        data = json.load(f)
    
    updated = 0
    for bet in data.get('bets', []):
        if bet.get('result') in ['WIN', 'LOSS']:
            # Already has a result
            continue
        
        bet_game = bet.get('game', '')
        
        # Try to find matching ESPN game
        for espn_game in espn_games:
            if match_game_to_bet(espn_game['competitors']['matchup'], bet_game):
                result, final_score = determine_win_loss(bet, espn_game)
                
                if result in ['WIN', 'LOSS']:
                    bet['result'] = result
                    bet['final_score'] = final_score
                    bet['completed_at'] = datetime.now().isoformat()
                    updated += 1
                    print(f"  ✓ {bet_game} → {result} ({final_score})")
                
                break
    
    if updated > 0:
        data['last_updated'] = datetime.now().isoformat()
        with open(bets_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✅ Updated {updated} bets in {bets_file}")
    
    return updated

def run_fetch(date_str=None):
    """Main entry point"""
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 70)
    print(f"SWORD ESPN Result Fetcher - {date_str}")
    print("=" * 70)
    
    # Fetch scores
    espn_games = fetch_espn_scores(date_str)
    
    if not espn_games:
        print("No games found or API error")
        return
    
    # Show summary
    print(f"\n📊 ESPN Games Summary:")
    for game in espn_games[:5]:
        comp = game.get('competitors', {})
        if comp:
            away = comp.get('away', {})
            home = comp.get('home', {})
            print(f"  {away.get('team', '?')} {away.get('score', '?')} @ {home.get('team', '?')} {home.get('score', '?')}")
    
    # Update bets
    print(f"\n🎯 Updating bet results...")
    updated = update_completed_bets(date_str, espn_games)
    
    if updated == 0:
        print("  (no new results matched)")

if __name__ == '__main__':
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else None
    run_fetch(date)
