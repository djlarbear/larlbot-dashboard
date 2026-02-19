#!/usr/bin/env python3
"""
Get live betting opportunities with real FanDuel odds
"""

from odds_collector import OddsCollector
import sqlite3
from datetime import datetime, timedelta

def get_live_value_bets():
    """Get today's games with real FanDuel odds"""
    
    # Get games from database
    conn = sqlite3.connect('sports_betting.db')
    query = """
        SELECT * FROM games 
        WHERE date >= datetime('now') 
        AND date < datetime('now', '+1 day')
        AND sport = 'ncb'
        AND status != 'Final'
        ORDER BY date
    """
    cursor = conn.cursor()
    cursor.execute(query)
    games = cursor.fetchall()
    conn.close()
    
    if not games:
        return []
    
    # Get real odds
    collector = OddsCollector()
    odds_data = collector.get_sports_odds('basketball_ncaab')
    parsed_odds = collector.parse_odds_data(odds_data)
    
    # Match games with odds
    value_bets = []
    
    for game in games:
        game_id, sport, date_str, home_team, away_team, home_score, away_score, spread, total, status, venue, created_at = game
        
        # Normalize team names for matching
        home_norm = home_team.lower().replace(' spartans', '').replace(' tar heels', '').replace(' blue devils', '').strip()
        away_norm = away_team.lower().replace(' panthers', '').replace(' jayhawks', '').replace(' wildcats', '').strip()
        
        # Find odds
        for odds in parsed_odds:
            odds_home_norm = odds['home_team'].lower().replace(' spartans', '').replace(' tar heels', '').replace(' blue devils', '').strip()
            odds_away_norm = odds['away_team'].lower().replace(' panthers', '').replace(' jayhawks', '').replace(' wildcats', '').strip()
            
            # Match teams
            if (home_norm in odds_home_norm or odds_home_norm in home_norm) and \
               (away_norm in odds_away_norm or odds_away_norm in away_norm):
                
                spreads = odds.get('spreads', {})
                totals = odds.get('totals', {})
                
                # Get actual lines
                home_spread = spreads.get('home_spread', 0)
                away_spread = spreads.get('away_spread', 0)
                total = totals.get('over_total', 0)
                bookmaker = odds.get('bookmaker', 'unknown')
                
                # Parse game time and convert from UTC to EST (UTC-5)
                game_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Convert to EST (subtract 5 hours from UTC)
                from datetime import timezone, timedelta
                est = timezone(timedelta(hours=-5))
                game_time_est = game_time.astimezone(est)
                game_time_str = game_time_est.strftime('%I:%M %p EST')
                
                # Only add games that haven't started or just started
                if status == 'Scheduled' or status == 'In Progress':
                    value_bets.append({
                        'game': f"{away_team} @ {home_team}",
                        'sport': 'NCAA Basketball',
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_spread': home_spread,
                        'away_spread': away_spread,
                        'total': total,
                        'bookmaker': bookmaker.title(),
                        'game_time': game_time_str,
                        'status': status
                    })
                break
    
    return value_bets

if __name__ == "__main__":
    bets = get_live_value_bets()
    print(f"Found {len(bets)} games with live odds:\n")
    for bet in bets:
        print(f"{bet['game']}")
        print(f"  {bet['home_team']}: {bet['home_spread']:+.1f} (-110)")
        print(f"  O/U: {bet['total']:.1f} (-110)")
        print(f"  Time: {bet['game_time']}")
        print(f"  Book: {bet['bookmaker']}")
        print()
