#!/usr/bin/env python3
"""
Analyze Larry's bets from today using smart analyzer
"""

from smart_betting_analyzer import SmartBettingAnalyzer

# Larry's bets from Feb 14
todays_bets = [
    {
        'away': 'Pittsburgh Panthers',
        'home': 'North Carolina Tar Heels',
        'market_spread': -10.5,  # UNC favored by 10.5
        'your_bet': 'Pitt +10.5'
    },
    {
        'away': 'Kansas Jayhawks',
        'home': 'Iowa State Cyclones',
        'market_spread': -7.5,  # Iowa St favored by 7.5
        'your_bet': 'Kansas +7.5',
        'result': 'LOSS - Iowa St won by 18'
    },
    {
        'away': 'Purdue Boilermakers',
        'home': 'Iowa Hawkeyes',
        'market_spread': -1.5,  # Purdue favored by 1.5
        'your_bet': 'Purdue -1.5'
    },
    {
        'away': 'Texas Tech Red Raiders',
        'home': 'Arizona Wildcats',
        'market_spread': -9.5,  # Arizona favored by 9.5
        'your_bet': 'TTU +9.5'
    },
    {
        'away': 'Kentucky Wildcats',
        'home': 'Florida Gators',
        'market_spread': None,  # Total bet, not spread
        'your_bet': 'Under 154.5'
    }
]

analyzer = SmartBettingAnalyzer()

print("🎰 ANALYZING LARRY'S BETS FROM FEB 14")
print("="*80)
print()

for i, bet in enumerate(todays_bets, 1):
    if bet['market_spread'] is None:
        print(f"{i}. {bet['away']} @ {bet['home']}")
        print(f"   Your bet: {bet['your_bet']}")
        print(f"   ⚠️ Total bets not analyzed yet (spread analysis only)")
        print()
        continue
    
    analysis = analyzer.analyze_bet(bet['away'], bet['home'], bet['market_spread'], sport='ncb')
    
    if not analysis:
        print(f"{i}. {bet['away']} @ {bet['home']}")
        print(f"   ❌ Could not analyze (team data unavailable)")
        print()
        continue
    
    print(f"{i}. {bet['away']} ({analysis['away_record']}) @ {bet['home']} ({analysis['home_record']})")
    print(f"   Market: {bet['home'].split()[0]} {bet['market_spread']}")
    print(f"   Our prediction: {bet['home'].split()[0]} {analysis['predicted_spread']}")
    print(f"   Edge: {analysis['edge']} points")
    print()
    print(f"   YOUR BET: {bet['your_bet']}")
    print(f"   OUR REC:  {analysis['recommendation']}")
    
    # Compare
    your_team = bet['your_bet'].split()[0]
    our_team = analysis['recommendation'].split()[0]
    
    if your_team.lower() in our_team.lower() or our_team.lower() in your_team.lower():
        print(f"   ✅ MATCH - We agree")
    else:
        print(f"   ❌ DIFFERENT - We disagree!")
    
    if 'result' in bet:
        print(f"   Result: {bet['result']}")
    
    print()

print("="*80)
print("SUMMARY:")
print("="*80)
print("The old system was making GUESSES based on 'feelings'")
print("The new system uses REAL team records and statistical analysis")
print("Kansas bet was BACKWARDS - we should have bet Iowa State!")
print()
