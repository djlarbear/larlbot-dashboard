#!/usr/bin/env python3
"""
🎰 LarlBot ESPN Scraper v1.0
Automated browser-based scraping of ESPN scoreboard for accurate game results
"""

import json
import os
import sys
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List

WORKSPACE = "/Users/macmini/.openclaw/workspace"
ESPN_CACHE_FILE = f"{WORKSPACE}/espn_scores_cache.json"


def normalize_team_name_for_display(name: str) -> str:
    """Clean up team name for consistency"""
    # Just strip extra whitespace and standardize case
    return name.strip().title()


def extract_games_from_text(text: str) -> List[Dict]:
    """
    Extract games from ESPN scoreboard page text
    Pattern: Team (record) H1 H2 [OT] Total | Team (record) H1 H2 [OT] Total
    """
    games = []
    
    # Split by Final/Final/OT markers
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for status lines (Final, Final/OT, etc)
        if line in ['FINAL', 'FINAL/OT', 'FINAL/2OT', 'FINAL/3OT'] or line.startswith('FINAL'):
            status = line
            i += 1
            
            # Skip header row if present
            if i < len(lines) and any(x in lines[i].lower() for x in ['1', '2', 'ot', 'total']):
                i += 1
            
            # Look for team data in next ~20 lines
            away_team = None
            away_h1 = None
            home_team = None
            
            for j in range(i, min(i + 20, len(lines))):
                curr = lines[j].strip()
                
                # Skip empty lines
                if not curr:
                    continue
                
                # Look for pattern: Team (Record) | H1 | H2 | [OT] | Total
                if '(' in curr and ')' in curr and curr[0].isalpha():
                    # This is a team line
                    team_part = curr.split('(')[0].strip()
                    
                    if not away_team:
                        away_team = team_part
                    else:
                        # This is the home team
                        # Collect next few lines for scores
                        scores = []
                        for k in range(j, min(j + 10, len(lines))):
                            score_line = lines[k].strip()
                            if score_line and score_line[0].isdigit():
                                scores.append(int(score_line))
                            elif score_line.isdigit():
                                scores.append(int(score_line))
                            elif scores and not score_line[0].isdigit():
                                break
                        
                        if len(scores) >= 4:  # At least H1, H2, H1, H2 (4 numbers)
                            # Find the totals (should be near end)
                            away_total = scores[-2] if len(scores) % 2 == 0 else scores[-2]
                            home_total = scores[-1]
                            
                            game = {
                                "away_team": normalize_team_name_for_display(away_team),
                                "home_team": normalize_team_name_for_display(curr),
                                "away_score": away_total,
                                "home_score": home_total,
                                "status": status
                            }
                            
                            # Validate scores are reasonable (0-200 range)
                            if 0 <= away_total <= 200 and 0 <= home_total <= 200:
                                games.append(game)
                                away_team = None
                        break
        
        i += 1
    
    return games


def scrape_espn_date(date_str: str) -> Dict:
    """
    Scrape ESPN scoreboard for a specific date
    Returns dict with date and list of games
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        {
            "date": "2026-02-14",
            "games": [
                {"away_team": "...", "home_team": "...", "away_score": X, "home_score": Y, "status": "Final"},
                ...
            ]
        }
    """
    print(f"\n🌐 ESPN Scraper - {date_str}")
    print("=" * 70)
    print(f"📅 Target date: {date_str}")
    print(f"⏳ Requires OpenClaw browser tool to be run via CLI")
    print(f"\nSteps:")
    print(f"1. Open ESPN scoreboard:")
    print(f"   https://www.espn.com/mens-college-basketball/scoreboard/_/group/50/date/{date_str.replace('-', '')}")
    print(f"\n2. In browser console, run:")
    print(f"""
(() => {{
  const games = [];
  const text = document.body.innerText;
  const lines = text.split('\\n');
  
  for (let i = 0; i < lines.length; i++) {{
    if (lines[i].match(/^(FINAL|Final)/)) {{
      // Found a game, collect context
      const context = lines.slice(i, i+30).join('|');
      // Log it
      console.log(context);
    }}
  }}
}})()
    """)
    print(f"\n3. Copy all console output and save to: {ESPN_CACHE_FILE}")
    print("=" * 70)
    
    return {
        "date": date_str,
        "games": [],
        "manual_scrape_required": True
    }


def load_cached_scores(date_str: str) -> Dict:
    """Load cached ESPN scores if available"""
    if os.path.exists(ESPN_CACHE_FILE):
        with open(ESPN_CACHE_FILE) as f:
            data = json.load(f)
            if data.get('date') == date_str:
                return data
    return None


def save_scores(date_str: str, games: List[Dict]):
    """Save scores to cache file"""
    data = {
        "date": date_str,
        "source": "ESPN Division I Scoreboard",
        "scraped_at": datetime.now().isoformat(),
        "games": games
    }
    
    with open(ESPN_CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Saved {len(games)} games to {ESPN_CACHE_FILE}")


def main():
    """Main execution"""
    print("=" * 70)
    print("🎰 LarlBot ESPN Scraper v1.0")
    print("=" * 70)
    
    # Get date from argument or use today
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n📅 Scraping date: {date_str}")
    
    # Check if cached
    cached = load_cached_scores(date_str)
    if cached:
        print(f"✅ Using cached data ({len(cached.get('games', []))} games)")
        return
    
    # Show instructions for manual scraping
    scrape_espn_date(date_str)
    
    print(f"\n❓ After manually scraping and saving to {ESPN_CACHE_FILE}:")
    print(f"   Run: python3 browser_result_checker_full.py [bet_file.json]")


if __name__ == "__main__":
    main()
