#!/usr/bin/env python3
"""
🎰 Manual fix for Northern Iowa bet that wasn't moved correctly
"""

import json

# Load active bets
with open('active_bets.json', 'r') as f:
    active_data = json.load(f)

# Load completed bets
with open('completed_bets_2026-02-15.json', 'r') as f:
    completed_data = json.load(f)

# Find and move Northern Iowa bet
northern_iowa_bets = []
remaining_bets = []

for bet in active_data['bets']:
    if 'Northern Iowa' in bet['game']:
        print(f"Found Northern Iowa bet: {bet['game']}")
        northern_iowa_bets.append(bet)
    else:
        remaining_bets.append(bet)

# Update active bets
active_data['bets'] = remaining_bets
print(f"\n✅ Removed {len(northern_iowa_bets)} Northern Iowa bets from active")
print(f"   Remaining active bets: {len(remaining_bets)}")

# Mark as WIN and add to completed
for bet in northern_iowa_bets:
    bet['result'] = 'WIN'
    bet['status'] = 'FINISHED'
    completed_data['bets'].append(bet)
    print(f"✅ Added to completed as WIN: {bet['recommendation']}")

# Save both files
with open('active_bets.json', 'w') as f:
    json.dump(active_data, f, indent=2)

with open('completed_bets_2026-02-15.json', 'w') as f:
    json.dump(completed_data, f, indent=2)

# Summary
print(f"\n{'=' * 70}")
wins = sum(1 for b in completed_data['bets'] if b.get('result') == 'WIN')
losses = sum(1 for b in completed_data['bets'] if b.get('result') == 'LOSS')
print(f"✅ Final Results: {wins} WIN, {losses} LOSS (Target: 8-2)")
print(f"{'=' * 70}")
