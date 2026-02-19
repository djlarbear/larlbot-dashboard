#!/usr/bin/env python3
"""
Generate today's smart picks for the dashboard
"""

from quick_betting_analyzer import QuickBettingAnalyzer
import json

# Today's games with FanDuel lines (from Feb 14, 2026)
todays_games = [
    {
        'away': 'Pittsburgh Panthers',
        'home': 'North Carolina Tar Heels',
        'market_spread': -10.5,
        'game_time': '2:00 PM EST'
    },
    {
        'away': 'Kansas Jayhawks',
        'home': 'Iowa State Cyclones',
        'market_spread': -7.5,
        'game_time': '1:00 PM EST'
    },
    {
        'away': 'Purdue Boilermakers',
        'home': 'Iowa Hawkeyes',
        'market_spread': -1.5,
        'game_time': '5:00 PM EST'
    },
    {
        'away': 'Texas Tech Red Raiders',
        'home': 'Arizona Wildcats',
        'market_spread': -9.5,
        'game_time': '6:30 PM EST'
    },
    {
        'away': 'Georgia Tech Yellow Jackets',
        'home': 'Notre Dame Fighting Irish',
        'market_spread': -7.5,
        'game_time': '12:00 PM EST'
    },
    {
        'away': 'UCLA Bruins',
        'home': 'Michigan Wolverines',
        'market_spread': -16.5,
        'game_time': '4:00 PM EST'
    }
]

print('🎰 LarlBot Smart Picks - Feb 14, 2026')
print('='*80)
print('Using data-driven analysis with real team performance metrics\n')

analyzer = QuickBettingAnalyzer()
recommendations = []

for game in todays_games:
    result = analyzer.predict_and_recommend(
        game['away'], 
        game['home'], 
        game['market_spread']
    )
    
    if result:
        # Only recommend if edge >= 2 points and confidence >= 45%
        if result['edge'] >= 2.0 and result['confidence'] >= 45:
            recommendations.append({
                'game': f"{game['away']} @ {game['home']}",
                'sport': 'NCAA Basketball',
                'bet_type': 'SPREAD',
                'recommendation': result['recommendation'],
                'confidence': result['confidence'],
                'edge': round(result['edge'], 1),
                'reason': result['reason'],
                'home_record': result['home_record'],
                'away_record': result['away_record'],
                'market_line': f"{game['home'].split()[0]} {game['market_spread']}",
                'fanduel_line': f"{game['home'].split()[0]} {game['market_spread']} (-110)",
                'game_time': game['game_time']
            })
            
            print(f"✅ {game['away']} @ {game['home']}")
            print(f"   Pick: {result['recommendation']}")
            print(f"   Edge: {result['edge']:.1f} pts | Confidence: {result['confidence']}%")
            print(f"   {result['reason']}")
            print()
    
    print()

print('='*80)
print(f'🎰 FINAL PICKS: {len(recommendations)} value bets')
print('='*80 + '\n')

# Display summary
for i, bet in enumerate(recommendations, 1):
    print(f"{i}. {bet['recommendation']} ({bet['confidence']}% confidence, {bet['edge']} pt edge)")

# Save to JSON for dashboard
with open('todays_smart_picks.json', 'w') as f:
    json.dump(recommendations, f, indent=2)

# Update the timestamp in daily_recommendations.py
from datetime import datetime
import pytz

est = pytz.timezone('America/New_York')
current_time = datetime.now(est).strftime('%I:%M %p').lstrip('0')
current_date = datetime.now(est).strftime('%Y-%m-%d')

# Read the file
with open('daily_recommendations.py', 'r') as f:
    content = f.read()

# Update the timestamp function
import re
content = re.sub(
    r'def get_odds_updated_time\(\):\s*""".*?"""\s*return ".*?"',
    f'def get_odds_updated_time():\n    """Get the timestamp when these picks were generated"""\n    return "{current_time}"',
    content,
    flags=re.DOTALL
)

# Update the generation comment
content = re.sub(
    r'# Generated \d{4}-\d{2}-\d{2} \d{1,2}:\d{2} (AM|PM) EST by smart analyzer',
    f'# Generated {current_date} {current_time} EST by smart analyzer',
    content
)

# Write back
with open('daily_recommendations.py', 'w') as f:
    f.write(content)

print(f'\n✅ Saved to todays_smart_picks.json')
print(f'✅ Updated daily_recommendations.py with timestamp: {current_time}')
