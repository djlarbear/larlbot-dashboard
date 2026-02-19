#!/usr/bin/env python3
"""
🎰 LarlBot Browser Result Checker v2.0 - Full Integration
Uses browser automation to scrape ESPN scoreboard for accurate game results
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

WORKSPACE = "/Users/macmini/.openclaw/workspace"
ACTIVE_BETS_FILE = f"{WORKSPACE}/active_bets.json"
ESPN_CACHE_FILE = f"{WORKSPACE}/espn_scores_cache.json"


def load_json(filepath: str) -> Dict:
    """Load JSON file"""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(filepath: str, data: Dict):
    """Save JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def normalize_team_name(name: str) -> str:
    """Normalize team names for matching"""
    name = name.lower().strip()
    
    # Remove common suffixes (must preserve this for base matching)
    name = re.sub(r'\s+(rainbow\s+)?warriors?', '', name)
    name = re.sub(r'\s+matadors?', '', name)
    name = re.sub(r'\s+(49ers?|bulldogs?|wildcats?|eagles?|hoyas?|huskies?)', '', name)
    name = re.sub(r'\s+(tigers?|bears?|panthers?|jayhawks?|cyclones?)', '', name)
    name = re.sub(r'\s+(aggies?|gators?|crimson\s+tide|razorbacks?)', '', name)
    name = re.sub(r'\s+(roadrunners?|bearcats?|golden\s+eagles?|kangaroos?)', '', name)
    name = re.sub(r'\s+(tommies?|hornets?|anteaters?|titans?)', '', name)
    
    # Common abbreviations and variations
    mapping = {
        # CSU variations
        "csu northridge": "cal state northridge",
        "csun": "cal state northridge",
        "cal st northridge": "cal state northridge",
        "csu fullerton": "cal state fullerton",
        "cal st fullerton": "cal state fullerton",
        
        # State abbreviations
        "sacramento st": "sacramento state",
        "sac state": "sacramento state",
        "ohio st": "ohio state",
        "michigan st": "michigan state",
        "san diego st": "san diego state",
        
        # School variations
        "hawai'i": "hawaii",
        "uconn": "connecticut",
        "st. thomas (mn)": "st thomas-minnesota",
        "st thomas (mn)": "st thomas-minnesota",
        "umkc": "kansas city",
        
        # Other common
        "texas a&m": "texas am",
        "ta&m": "texas am",
        "st john's": "st johns",
        "st. john's": "st johns",
        "sju": "st johns",
    }
    
    return mapping.get(name, name)


def fuzzy_match_team(bet_team: str, espn_team: str) -> bool:
    """Fuzzy match between bet team and ESPN team"""
    bet_norm = normalize_team_name(bet_team)
    espn_norm = normalize_team_name(espn_team)
    
    # Exact match
    if bet_norm == espn_norm:
        return True
    
    # One contains the other
    if bet_norm in espn_norm or espn_norm in bet_norm:
        return True
    
    # Check individual words (for multi-word names)
    bet_words = set(bet_norm.split())
    espn_words = set(espn_norm.split())
    
    # If they share 2+ significant words, it's a match
    common_words = bet_words & espn_words
    if len(common_words) >= 2:
        return True
    
    # Special case: if one word matches and both names are short
    if len(bet_words) <= 2 and len(espn_words) <= 2 and len(common_words) >= 1:
        return True
    
    return False


def match_game(bet_game: str, espn_away: str, espn_home: str) -> bool:
    """Check if bet game matches ESPN game"""
    if " @ " not in bet_game:
        return False
    
    away, home = bet_game.split(" @ ")
    
    return fuzzy_match_team(away, espn_away) and fuzzy_match_team(home, espn_home)


def calculate_result(bet: Dict, away_score: int, home_score: int) -> Tuple[str, str, str]:
    """
    Calculate bet result (WIN/LOSS/PUSH)
    Returns (result, reason, final_score_str)
    """
    bet_type = bet.get("bet_type", "").upper()
    recommendation = bet.get("recommendation", "")
    game = bet["game"]
    
    if " @ " not in game:
        return ("PENDING", "Invalid game format", "N/A")
    
    away_team, home_team = game.split(" @ ")
    final_score = f"{away_score}-{home_score}"
    
    # SPREAD bets
    if bet_type == "SPREAD":
        spread_match = re.search(r'([-+]?\d+\.?\d*)', recommendation)
        if not spread_match:
            return ("PENDING", "Could not parse spread", final_score)
        
        spread = float(spread_match.group(1))
        
        if normalize_team_name(away_team) in normalize_team_name(recommendation):
            # Bet on away team
            adjusted_score = away_score + spread
            if adjusted_score > home_score:
                return ("WIN", f"Away {away_score} + ({spread}) = {adjusted_score} > {home_score}", final_score)
            elif adjusted_score < home_score:
                return ("LOSS", f"Away {away_score} + ({spread}) = {adjusted_score} < {home_score}", final_score)
            else:
                return ("PUSH", f"Away {away_score} + ({spread}) = {adjusted_score} = {home_score}", final_score)
        else:
            # Bet on home team
            adjusted_score = home_score + spread
            if adjusted_score > away_score:
                return ("WIN", f"Home {home_score} + ({spread}) = {adjusted_score} > {away_score}", final_score)
            elif adjusted_score < away_score:
                return ("LOSS", f"Home {home_score} + ({spread}) = {adjusted_score} < {away_score}", final_score)
            else:
                return ("PUSH", f"Home {home_score} + ({spread}) = {adjusted_score} = {away_score}", final_score)
    
    # MONEYLINE bets
    elif bet_type == "MONEYLINE":
        if normalize_team_name(away_team) in normalize_team_name(recommendation):
            # Bet on away team
            if away_score > home_score:
                return ("WIN", f"Away team won {away_score}-{home_score}", final_score)
            else:
                return ("LOSS", f"Away team lost {away_score}-{home_score}", final_score)
        else:
            # Bet on home team
            if home_score > away_score:
                return ("WIN", f"Home team won {home_score}-{away_score}", final_score)
            else:
                return ("LOSS", f"Home team lost {home_score}-{away_score}", final_score)
    
    # TOTAL (Over/Under) bets
    elif bet_type == "TOTAL":
        total_match = re.search(r'(\d+\.?\d*)', recommendation)
        if not total_match:
            return ("PENDING", "Could not parse total", final_score)
        
        total = float(total_match.group(1))
        actual_total = away_score + home_score
        
        if "UNDER" in recommendation.upper():
            if actual_total < total:
                return ("WIN", f"Total {actual_total} < {total} (UNDER)", final_score)
            elif actual_total > total:
                return ("LOSS", f"Total {actual_total} > {total} (not UNDER)", final_score)
            else:
                return ("PUSH", f"Total {actual_total} = {total}", final_score)
        else:  # OVER
            if actual_total > total:
                return ("WIN", f"Total {actual_total} > {total} (OVER)", final_score)
            elif actual_total < total:
                return ("LOSS", f"Total {actual_total} < {total} (not OVER)", final_score)
            else:
                return ("PUSH", f"Total {actual_total} = {total}", final_score)
    
    return ("PENDING", f"Unknown bet type: {bet_type}", final_score)


def process_bets(espn_scores: Dict, bets_file: str) -> Dict:
    """
    Process all bets against ESPN scores
    Returns stats dict
    """
    # Load bets
    active_data = load_json(bets_file)
    if not active_data or "bets" not in active_data:
        print("❌ No bets found")
        return {"processed": 0, "completed": 0, "pending": 0}
    
    bets = active_data["bets"]
    date = active_data.get("date", "unknown")
    
    print(f"\n📊 Processing {len(bets)} bets for {date}...")
    
    completed_count = 0
    pending_count = 0
    
    for bet in bets:
        game = bet["game"]
        
        # Try to find matching ESPN game
        matched = False
        for espn_game in espn_scores.get("games", []):
            espn_away = espn_game["away_team"]
            espn_home = espn_game["home_team"]
            
            if match_game(game, espn_away, espn_home):
                matched = True
                away_score = espn_game["away_score"]
                home_score = espn_game["home_score"]
                status = espn_game.get("status", "Final")
                
                # Only process if game is final
                if status.lower() in ["final", "final/ot", "final/2ot", "final/3ot"]:
                    result, reason, final_score = calculate_result(bet, away_score, home_score)
                    
                    # Update bet
                    bet["result"] = result
                    bet["final_score"] = final_score
                    bet["away_score"] = away_score
                    bet["home_score"] = home_score
                    bet["completed_at"] = datetime.now().isoformat()
                    
                    print(f"   ✅ {game}: {result} ({final_score}) - {reason}")
                    completed_count += 1
                else:
                    print(f"   ⏳ {game}: In progress ({status})")
                    pending_count += 1
                break
        
        if not matched:
            print(f"   ❓ {game}: No ESPN match found")
            pending_count += 1
    
    # Save updated bets
    save_json(bets_file, active_data)
    
    return {
        "processed": len(bets),
        "completed": completed_count,
        "pending": pending_count
    }


def main():
    """Main execution"""
    print("=" * 70)
    print("🎰 LarlBot Browser Result Checker v2.0")
    print("=" * 70)
    
    # Check for file argument
    bets_file = sys.argv[1] if len(sys.argv) > 1 else ACTIVE_BETS_FILE
    print(f"\n📂 Bets file: {bets_file}")
    
    # Check if ESPN cache exists
    if not os.path.exists(ESPN_CACHE_FILE):
        print(f"\n❌ ESPN scores cache not found: {ESPN_CACHE_FILE}")
        print("\n📋 Instructions:")
        print("1. Use OpenClaw browser tool to scrape ESPN scoreboard")
        print("2. Save results to espn_scores_cache.json")
        print("3. Run this script again")
        print("\nExpected format:")
        print("""{
  "date": "2026-02-14",
  "games": [
    {
      "away_team": "Hawaii",
      "home_team": "Cal State Northridge",
      "away_score": 60,
      "home_score": 84,
      "status": "Final"
    },
    ...
  ]
}""")
        return
    
    # Load ESPN scores
    espn_scores = load_json(ESPN_CACHE_FILE)
    print(f"✅ Loaded {len(espn_scores.get('games', []))} games from ESPN cache")
    
    # Process bets
    stats = process_bets(espn_scores, bets_file)
    
    print("\n" + "=" * 70)
    print(f"📊 Results:")
    print(f"   Total bets: {stats['processed']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Pending: {stats['pending']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
