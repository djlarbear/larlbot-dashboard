#!/usr/bin/env python3
"""Quick debug script to see API team names vs our bet names"""
import json
import requests

# Load active bets
with open('active_bets.json', 'r') as f:
    active = json.load(f)
    
print("=== OUR BET GAME NAMES ===")
for i, bet in enumerate(active['bets'][:5]):  # First 5
    print(f"{i+1}. {bet['game']}")

print("\n=== NCAA GAMES FROM API (Yesterday) ===")
api_key = '82865426fd192e243376eb4e51185f3b'
url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/scores"
params = {'api_key': api_key, 'daysFrom': 1}

response = requests.get(url, params=params, timeout=10)
if response.status_code == 200:
    games = response.json()
    completed = [g for g in games if g.get('completed') == True]
    
    print(f"Found {len(completed)} completed NCAA games")
    for i, game in enumerate(completed[:10]):  # First 10
        away = game.get('away_team', '')
        home = game.get('home_team', '')
        away_score = game.get('away_score', 0)
        home_score = game.get('home_score', 0)
        print(f"{i+1}. {away} @ {home} ({away_score}-{home_score})")
