#!/usr/bin/env python3
"""
🎰 LarlBot Browser Result Checker v1.0
Uses browser automation to scrape ESPN scoreboard for accurate game results
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Browser control via OpenClaw
def get_espn_games(date_str: str) -> List[Dict]:
    """
    Scrape ESPN scoreboard for all games on a specific date
    Returns list of game dictionaries with teams and scores
    """
    print(f"[Browser] Opening ESPN scoreboard for {date_str}...")
    
    # Format date for ESPN URL (YYYYMMDD)
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    espn_date = date_obj.strftime("%Y%m%d")
    
    url = f"https://www.espn.com/mens-college-basketball/scoreboard/_/group/50/date/{espn_date}"
    
    # Use OpenClaw browser tool to scrape
    # For now, return a mock structure - we'll integrate browser API next
    print(f"[Browser] URL: {url}")
    print("[Browser] ⚠️  Browser integration needed - implement OpenClaw browser API calls")
    
    return []


def normalize_team_name(name: str) -> str:
    """Normalize team names for matching"""
    # Remove common variations
    name = name.lower()
    name = re.sub(r'\s+(rainbow\s+)?warriors?', '', name)
    name = re.sub(r'\s+matadors?', '', name)
    name = re.sub(r'\s+(49ers?|bulldogs?|wildcats?|eagles?)', '', name)
    name = name.strip()
    
    # Map common abbreviations
    mapping = {
        "csu northridge": "cal state northridge",
        "csun": "cal state northridge",
        "hawai'i": "hawaii",
        "uconn": "connecticut",
        "ohio st": "ohio state",
        "michigan st": "michigan state",
    }
    
    return mapping.get(name, name)


def match_teams(bet_game: str, espn_away: str, espn_home: str) -> bool:
    """Check if bet game matches ESPN game"""
    # Extract team names from bet game (format: "Team A @ Team B")
    if " @ " not in bet_game:
        return False
    
    away, home = bet_game.split(" @ ")
    away_norm = normalize_team_name(away)
    home_norm = normalize_team_name(home)
    
    espn_away_norm = normalize_team_name(espn_away)
    espn_home_norm = normalize_team_name(espn_home)
    
    # Check if both teams match
    return (away_norm in espn_away_norm or espn_away_norm in away_norm) and \
           (home_norm in espn_home_norm or espn_home_norm in home_norm)


def calculate_result(bet: Dict, away_score: int, home_score: int) -> Tuple[str, str]:
    """
    Calculate bet result (WIN/LOSS/PUSH)
    Returns (result, reason)
    """
    bet_type = bet.get("bet_type", "").upper()
    recommendation = bet.get("recommendation", "")
    
    # Determine which team was bet on
    game = bet["game"]
    if " @ " not in game:
        return ("PENDING", "Invalid game format")
    
    away_team, home_team = game.split(" @ ")
    
    # SPREAD bets
    if bet_type == "SPREAD":
        # Extract spread value from recommendation (e.g., "Team -12.5")
        spread_match = re.search(r'([-+]?\d+\.?\d*)', recommendation)
        if not spread_match:
            return ("PENDING", "Could not parse spread")
        
        spread = float(spread_match.group(1))
        
        # Check which team was bet on
        if away_team in recommendation:
            # Bet on away team
            adjusted_score = away_score + spread
            if adjusted_score > home_score:
                return ("WIN", f"{away_team} {away_score} + ({spread}) = {adjusted_score} > {home_team} {home_score}")
            elif adjusted_score < home_score:
                return ("LOSS", f"{away_team} {away_score} + ({spread}) = {adjusted_score} < {home_team} {home_score}")
            else:
                return ("PUSH", f"{away_team} {away_score} + ({spread}) = {adjusted_score} = {home_team} {home_score}")
        else:
            # Bet on home team
            adjusted_score = home_score + spread
            if adjusted_score > away_score:
                return ("WIN", f"{home_team} {home_score} + ({spread}) = {adjusted_score} > {away_team} {away_score}")
            elif adjusted_score < away_score:
                return ("LOSS", f"{home_team} {home_score} + ({spread}) = {adjusted_score} < {away_team} {away_score}")
            else:
                return ("PUSH", f"{home_team} {home_score} + ({spread}) = {adjusted_score} = {away_team} {away_score}")
    
    # MONEYLINE bets
    elif bet_type == "MONEYLINE":
        # Check which team was bet on
        if away_team in recommendation:
            # Bet on away team
            if away_score > home_score:
                return ("WIN", f"{away_team} won {away_score}-{home_score}")
            else:
                return ("LOSS", f"{away_team} lost {away_score}-{home_score}")
        else:
            # Bet on home team
            if home_score > away_score:
                return ("WIN", f"{home_team} won {home_score}-{away_score}")
            else:
                return ("LOSS", f"{home_team} lost {home_score}-{away_score}")
    
    # TOTAL (Over/Under) bets
    elif bet_type == "TOTAL":
        # Extract total value (e.g., "UNDER 154.5")
        total_match = re.search(r'(\d+\.?\d*)', recommendation)
        if not total_match:
            return ("PENDING", "Could not parse total")
        
        total = float(total_match.group(1))
        actual_total = away_score + home_score
        
        if "UNDER" in recommendation.upper():
            if actual_total < total:
                return ("WIN", f"Total {actual_total} UNDER {total}")
            elif actual_total > total:
                return ("LOSS", f"Total {actual_total} OVER {total}")
            else:
                return ("PUSH", f"Total {actual_total} = {total}")
        else:  # OVER
            if actual_total > total:
                return ("WIN", f"Total {actual_total} OVER {total}")
            elif actual_total < total:
                return ("LOSS", f"Total {actual_total} UNDER {total}")
            else:
                return ("PUSH", f"Total {actual_total} = {total}")
    
    return ("PENDING", f"Unknown bet type: {bet_type}")


def main():
    """Main execution"""
    print("=" * 70)
    print("🎰 LarlBot Browser Result Checker v1.0")
    print("=" * 70)
    
    # For now, test with manual data from the Hawaii @ CSU Northridge game
    print("\n[Test] Testing with Hawaii @ CSU Northridge game...")
    
    test_bet = {
        "game": "Hawai'i Rainbow Warriors @ CSU Northridge Matadors",
        "bet_type": "SPREAD",
        "recommendation": "CSU Northridge Matadors -24.5"
    }
    
    # Actual ESPN scores
    away_score = 60  # Hawaii
    home_score = 84  # Cal State Northridge
    
    result, reason = calculate_result(test_bet, away_score, home_score)
    
    print(f"\n📊 Test Result:")
    print(f"   Game: Hawaii 60 @ Cal State Northridge 84")
    print(f"   Bet: {test_bet['recommendation']}")
    print(f"   Result: {result}")
    print(f"   Reason: {reason}")
    
    if result == "LOSS":
        print("\n✅ Correct! Cal State won by 24 (not 25+), so -24.5 spread is a LOSS")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("1. Integrate OpenClaw browser API to scrape ESPN")
    print("2. Add batch processing for all active/completed bets")
    print("3. Update JSON files with results")
    print("=" * 70)


if __name__ == "__main__":
    main()
