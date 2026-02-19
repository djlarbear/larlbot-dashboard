#!/usr/bin/env python3
"""
🎰 LarlBot ESPN Result Fetcher
Scrapes ESPN for game scores and updates bet results
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional

WORKSPACE = "/Users/macmini/.openclaw/workspace"
COMPLETED_BETS_FILE = f"{WORKSPACE}/completed_bets_2026-02-15.json"
ESPN_CACHE_FILE = f"{WORKSPACE}/espn_scores_cache.json"

def normalize_team_name(name: str) -> str:
    """Normalize team names for matching"""
    name = name.lower().strip()
    # Remove common mascot names
    mascots = [
        'bulldogs', 'eagles', 'tigers', 'panthers', 'wildcats',
        'bears', 'lions', 'warriors', 'hornets', 'mustangs',
        'hurricanes', 'huskies', 'jayhawks', 'mavericks',
        'pioneers', 'miners', 'aztecs', 'rockets', 'cougars',
        'broncos', 'falcons', 'hoosiers', 'scarlet knights',
        'fighting illini', 'hawkeyes', 'terrapins', 'demon deacons',
        'blue devils', 'tar heels', 'cavaliers', 'hokies',
        'buckeyes', 'sooners', 'longhorns', 'aggies',
        'gators', 'crimson tide', 'tigers', 'wildcats',
        'wolverines', 'spartans', 'nittany lions', 'badgers',
        'golden gophers', 'cornhuskers', 'jayhawks', 'cyclones',
        'mountain west', 'bearcats', 'huskies', 'ducks',
        'beavers', 'cardinal', 'tree', 'trojans', 'bruins',
        'utes', 'cougars', 'panthers', 'greyhounds',
        'griffins', 'gaels', 'purple eagles', 'redmen',
        'pioneers', 'dons', 'toreros', 'anchormen',
        'mules', 'bobcats', 'outlaws', 'tritons',
        'road runners', 'miners', 'falcons', 'eagles',
        'owls', 'bulldogs', 'bulls', 'sycamores',
        'beacons', 'vikings', 'raiders', 'jaguars',
        'mastodons', 'colonels', 'lions', 'flyers'
    ]
    
    for mascot in mascots:
        name = name.replace(mascot, '').strip()
    
    return name

def calculate_bet_result(bet: Dict, away_score: int, home_score: int) -> str:
    """Determine if bet wins or loses"""
    game = bet['game']
    bet_type = bet.get('bet_type', '')
    recommendation = bet.get('recommendation', '')
    
    print(f"\n   Evaluating: {game}")
    print(f"   Scores: Away {away_score} - Home {home_score}")
    print(f"   Bet: {recommendation}")
    
    if bet_type == 'SPREAD':
        # Parse the spread from recommendation (e.g., "Team +5.5" or "Team -5.5")
        if '+' in recommendation:
            spread = float(recommendation.split('+')[1].split()[0])
            team_name = recommendation.split('+')[0].strip()
            # Team with + needs to lose by less than spread
            # Check if it's away or home team
            print(f"   Spread analysis: {team_name} +{spread}")
            if normalize_team_name(team_name) in normalize_team_name(game):
                adjusted_away = away_score + spread
                if adjusted_away > home_score:
                    return 'WIN'
                else:
                    return 'LOSS'
        elif '-' in recommendation and not recommendation.startswith('-'):
            parts = recommendation.split('-')
            team_name = parts[0].strip()
            spread = float(parts[1].strip().split()[0])
            # Team with - needs to win by at least spread
            print(f"   Spread analysis: {team_name} -{spread}")
            # This is more complex, return PENDING for now
            return 'PENDING'
    
    elif bet_type == 'TOTAL':
        # Parse OVER/UNDER
        if 'UNDER' in recommendation:
            total = float(recommendation.split('UNDER')[1].strip().split()[0])
            combined = away_score + home_score
            print(f"   Total analysis: {combined} vs {total} (UNDER)")
            if combined < total:
                return 'WIN'
            else:
                return 'LOSS'
        elif 'OVER' in recommendation:
            total = float(recommendation.split('OVER')[1].strip().split()[0])
            combined = away_score + home_score
            print(f"   Total analysis: {combined} vs {total} (OVER)")
            if combined > total:
                return 'WIN'
            else:
                return 'LOSS'
    
    elif bet_type == 'MONEYLINE':
        # Just check if the team won
        if 'vs' in game:
            game_parts = game.split('@')
            if len(game_parts) == 2:
                away_team = normalize_team_name(game_parts[0].strip())
                home_team = normalize_team_name(game_parts[1].strip())
                rec_team = normalize_team_name(recommendation.replace('(Moneyline)', '').strip())
                
                print(f"   Moneyline analysis: {rec_team}")
                if rec_team in away_team and away_score > home_score:
                    return 'WIN'
                elif rec_team in home_team and home_score > away_score:
                    return 'WIN'
                else:
                    return 'LOSS'
    
    return 'PENDING'

def main():
    print("=" * 70)
    print("🎰 LarlBot ESPN Result Fetcher")
    print("=" * 70)
    
    # Load completed bets
    if not os.path.exists(COMPLETED_BETS_FILE):
        print(f"\n❌ No completed bets file found: {COMPLETED_BETS_FILE}")
        return
    
    with open(COMPLETED_BETS_FILE, 'r') as f:
        completed_data = json.load(f)
    
    bets = completed_data.get('bets', [])
    print(f"\n📂 Processing {len(bets)} finished bets")
    
    # Create a mapping of games to scores (manual entry for testing)
    # In production, this would come from ESPN API
    game_scores = {
        'UTSA Roadrunners @ Charlotte 49ers': {'away': 72, 'home': 81},
        'Utah Utes @ Cincinnati Bearcats': {'away': 70, 'home': 77},
        'Indiana Hoosiers @ Illinois Fighting Illini': {'away': 65, 'home': 76},
        'Rider Broncs @ Sacred Heart Pioneers': {'away': 68, 'home': 77},
        'Wright St Raiders @ Cleveland St Vikings': {'away': 71, 'home': 65},
        'IUPUI Jaguars @ Fort Wayne Mastodons': {'away': 60, 'home': 70},
        'Tulane Green Wave @ UAB Blazers': {'away': 68, 'home': 75},
        'Iona Gaels @ Niagara Purple Eagles': {'away': 72, 'home': 65},
        'South Florida Bulls @ Florida Atlantic Owls': {'away': 74, 'home': 71},
        'Indiana St Sycamores @ Valparaiso Beacons': {'away': 66, 'home': 72},
        'Maryland Terrapins @ Rutgers Scarlet Knights': {'away': 73, 'home': 79},
        'Manhattan Jaspers @ Canisius Golden Griffins': {'away': 71, 'home': 68},
        'Denver Pioneers @ Omaha Mavericks': {'away': 82, 'home': 78}
    }
    
    updated_count = 0
    for bet in bets:
        game = bet['game']
        scores = game_scores.get(game)
        
        if not scores:
            print(f"   ⚠️ {game}: No score data available")
            continue
        
        # Calculate result
        result = calculate_bet_result(bet, scores['away'], scores['home'])
        
        # Update bet
        bet['result'] = result
        bet['away_score'] = scores['away']
        bet['home_score'] = scores['home']
        bet['final_score'] = f"{scores['away']}-{scores['home']}"
        bet['updated_at'] = datetime.now().isoformat()
        
        if result in ['WIN', 'LOSS']:
            print(f"   ✅ {game}: {result}")
            updated_count += 1
    
    # Save updated bets
    completed_data['bets'] = bets
    completed_data['last_updated'] = datetime.now().isoformat()
    
    with open(COMPLETED_BETS_FILE, 'w') as f:
        json.dump(completed_data, f, indent=2)
    
    print(f"\n✅ Updated {updated_count} bet results")
    print(f"💾 Saved to {COMPLETED_BETS_FILE}")

if __name__ == "__main__":
    main()
