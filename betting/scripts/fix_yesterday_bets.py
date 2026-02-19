#!/usr/bin/env python3
"""
Emergency fix: Move yesterday's completed bets to Previous Results
Uses ESPN API for real scores
"""
import json
import requests
from datetime import datetime, timezone
import re

def get_espn_scores():
    """Fetch yesterday's NCAA basketball scores from ESPN"""
    # ESPN scoreboard API
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    params = {
        'limit': 300,
        'dates': '20260214'  # Yesterday's date
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            scores = []
            
            for event in data.get('events', []):
                if event.get('status', {}).get('type', {}).get('completed') == True:
                    competitors = event.get('competitions', [{}])[0].get('competitors', [])
                    if len(competitors) == 2:
                        away = competitors[1] if competitors[1].get('homeAway') == 'away' else competitors[0]
                        home = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]
                        
                        scores.append({
                            'away_team': away.get('team', {}).get('displayName', ''),
                            'home_team': home.get('team', {}).get('displayName', ''),
                            'away_score': int(away.get('score', 0)),
                            'home_score': int(home.get('score', 0)),
                            'completed': True
                        })
            
            return scores
    except Exception as e:
        print(f"❌ ESPN API error: {e}")
        return []

def normalize_name(name):
    """Normalize team name for matching"""
    # Remove common suffixes
    name = re.sub(r'\s+(Tigers|Bears|Eagles|Wildcats|Bulldogs|Aggies|Huskies|Cougars|Panthers|Rams|Lions|Trojans|Warriors|Cardinals|Cyclones|Jayhawks|Hoyas|Horned Frogs|Cowboys|Yellow Jackets|Fighting Irish|Blue Devils|Wolverines|Red Storm|Friars|Boilermakers|Hawkeyes|Red Raiders|Gators|Gamecocks|Crimson Tide|Highlanders|Tritons|Hornets|Lumberjacks|Jackrabbits|Golden Eagles|Wolf Pack|Aztecs|Titans|Anteaters|Gaels|Blue Raiders|Hilltoppers|Golden Gophers|Matadors|Tommies|Kangaroos|Thundering Herd|Rainbow Warriors)\s*$', '', name, flags=re.IGNORECASE)
    
    # Team name replacements
    replacements = {
        'Hawai\'i': 'Hawaii',
        'CSU Northridge': 'Cal St Northridge',
        'St. Thomas (MN)': 'St Thomas',
        'UMKC': 'Missouri Kansas City',
        'UC San Diego': 'UC San Diego',
        'UC Riverside': 'UC Riverside',
        'UC Irvine': 'UC Irvine',
        'CSU Fullerton': 'Cal St Fullerton',
        'Saint Mary\'s': 'Saint Marys',
        'South Dakota St': 'South Dakota State',
        'Sacramento St': 'Sacramento State',
        'San Diego St': 'San Diego State',
        'Utah State': 'Utah St',
    }
    
    for old, new in replacements.items():
        if old.lower() in name.lower():
            name = re.sub(old, new, name, flags=re.IGNORECASE)
    
    return name.strip().lower()

def match_bet_to_score(bet_game, scores):
    """Match bet to ESPN score"""
    bet_normalized = normalize_name(bet_game)
    
    for score in scores:
        away_norm = normalize_name(score['away_team'])
        home_norm = normalize_name(score['home_team'])
        
        # Check if both teams appear in bet string
        if (away_norm in bet_normalized or bet_normalized in away_norm) and \
           (home_norm in bet_normalized or bet_normalized in home_norm):
            return score
    
    return None

def calculate_result(bet, score):
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

def main():
    print("🎰 LarlBot Yesterday's Bets Fixer")
    print("=" * 60)
    
    # Load active bets
    with open('active_bets.json', 'r') as f:
        active_data = json.load(f)
    
    yesterday_bets = active_data.get('bets', [])
    print(f"📊 Found {len(yesterday_bets)} bets from yesterday (2026-02-14)")
    
    # Get ESPN scores
    print("🏀 Fetching scores from ESPN...")
    scores = get_espn_scores()
    print(f"✅ Found {len(scores)} completed games")
    
    # Match and calculate results
    completed_bets = []
    unmatched_bets = []
    
    for bet in yesterday_bets:
        score = match_bet_to_score(bet['game'], scores)
        
        if score:
            result = calculate_result(bet, score)
            bet['result'] = result
            bet['final_score'] = f"{score['away_score']}-{score['home_score']}"
            bet['away_score'] = score['away_score']
            bet['home_score'] = score['home_score']
            bet['completed_at'] = datetime.now(timezone.utc).isoformat()
            completed_bets.append(bet)
            
            status_emoji = '✅' if result == 'WIN' else '❌' if result == 'LOSS' else '❓'
            print(f"{status_emoji} {bet['game'][:50]:50} | {result:6} | {bet['final_score']}")
        else:
            unmatched_bets.append(bet)
            print(f"⚠️  Could not match: {bet['game']}")
    
    print("\n" + "=" * 60)
    print(f"✅ Matched: {len(completed_bets)}")
    print(f"⚠️  Unmatched: {len(unmatched_bets)}")
    
    # Save completed bets
    if completed_bets:
        completed_file = {
            'date': '2026-02-14',
            'bets': completed_bets,
            'stats': {
                'total_bets': len(completed_bets),
                'wins': len([b for b in completed_bets if b.get('result') == 'WIN']),
                'losses': len([b for b in completed_bets if b.get('result') == 'LOSS']),
            }
        }
        
        with open('completed_bets_2026-02-14.json', 'w') as f:
            json.dump(completed_file, f, indent=2)
        
        print(f"\n💾 Saved to: completed_bets_2026-02-14.json")
        print(f"📊 Record: {completed_file['stats']['wins']}-{completed_file['stats']['losses']}")
    
    # Clear active_bets.json
    empty_active = {
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'bets': unmatched_bets if unmatched_bets else []
    }
    
    with open('active_bets.json', 'w') as f:
        json.dump(empty_active, f, indent=2)
    
    print("✅ Cleared active_bets.json")
    print("🎉 Dashboard should now show today's bets only!")

if __name__ == '__main__':
    main()
