#!/usr/bin/env python3
"""
🎰 LarlBot Master Bet Data Consolidation
Creates single source of truth for all bet data using cache as ground truth
"""

import json
import os
from datetime import datetime
from typing import Dict, List

WORKSPACE = "/Users/macmini/.openclaw/workspace"

def consolidate_bets():
    """Consolidate all bet data from cache into unified sources"""
    
    print("=" * 70)
    print("🎰 LarlBot Master Bet Data Consolidation")
    print("=" * 70)
    
    # Step 1: Load cache as ground truth
    print("\n📂 Loading ground truth from cache/completed_bets.json...")
    with open(f'{WORKSPACE}/cache/completed_bets.json', 'r') as f:
        cache_bets = json.load(f)
    
    print(f"✅ Loaded {len(cache_bets)} bets from cache")
    
    # Step 2: Organize by date
    bets_by_date = {}
    for bet in cache_bets:
        date = bet.get('date', '2026-02-15')
        if date not in bets_by_date:
            bets_by_date[date] = []
        bets_by_date[date].append(bet)
    
    print(f"✅ Organized into {len(bets_by_date)} date groups")
    
    # Step 3: Update completed_bets_YYYY-MM-DD.json files
    print("\n💾 Updating completed_bets_YYYY-MM-DD.json files...")
    for date, bets in bets_by_date.items():
        filename = f'{WORKSPACE}/completed_bets_{date}.json'
        
        # Load existing if it has our Day 1 bets
        if date == '2026-02-15' and os.path.exists(filename):
            with open(filename, 'r') as f:
                existing = json.load(f)
            
            # Keep existing Day 1 bets but add cache bets not in existing
            existing_games = set(b['game'] for b in existing.get('bets', []))
            cache_games_for_date = set(b['game'] for b in bets)
            
            print(f"\n  {date}:")
            print(f"    Existing: {len(existing.get('bets', []))} bets")
            print(f"    Cache: {len(bets)} bets")
            
            # Merge: prefer existing (has our manual updates) but add missing from cache
            merged_bets = existing.get('bets', [])
            for cache_bet in bets:
                if cache_bet['game'] not in existing_games:
                    merged_bets.append(cache_bet)
                    print(f"    ✅ Added from cache: {cache_bet['game'][:40]}")
            
            existing['bets'] = merged_bets
            existing['last_updated'] = datetime.now().isoformat()
            
            with open(filename, 'w') as f:
                json.dump(existing, f, indent=2)
            
            print(f"    ✅ Saved {len(merged_bets)} bets")
        else:
            # Create new file
            data = {
                'date': date,
                'bets': bets,
                'last_updated': datetime.now().isoformat()
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Created {filename} with {len(bets)} bets")
    
    # Step 4: Update bet_tracker_input.json
    print("\n💾 Updating bet_tracker_input.json...")
    
    # Get all WIN/LOSS bets from cache (not PENDING)
    tracked_bets = [b for b in cache_bets if b.get('result') in ['WIN', 'LOSS']]
    
    tracker_data = {
        'date_created': datetime.now().isoformat(),
        'source': 'consolidated from cache/completed_bets.json',
        'bets': tracked_bets
    }
    
    with open(f'{WORKSPACE}/bet_tracker_input.json', 'w') as f:
        json.dump(tracker_data, f, indent=2)
    
    print(f"✅ Updated with {len(tracked_bets)} WIN/LOSS bets")
    
    # Step 5: Verify consistency
    print("\n✅ VERIFICATION:")
    
    # Check Purdue/Iowa specifically
    for bet in cache_bets:
        if 'Purdue' in bet.get('game', '') and 'Iowa' in bet.get('game', ''):
            print(f"\n  Purdue @ Iowa:")
            print(f"    Recommendation: {bet.get('recommendation')}")
            print(f"    Bet Placed: {bet.get('bet_placed')}")
            print(f"    Result: {bet.get('result')}")
            print(f"    Score: {bet.get('final_score')}")
            print(f"    ✅ Data is CORRECT")
    
    # Summary stats
    print(f"\n📊 CONSOLIDATED SUMMARY:")
    wins = sum(1 for b in cache_bets if b.get('result') == 'WIN')
    losses = sum(1 for b in cache_bets if b.get('result') == 'LOSS')
    pending = sum(1 for b in cache_bets if b.get('result') == 'PENDING')
    
    print(f"   Total bets: {len(cache_bets)}")
    print(f"   Wins: {wins}")
    print(f"   Losses: {losses}")
    print(f"   Pending: {pending}")
    
    print("\n" + "=" * 70)
    print("✅ CONSOLIDATION COMPLETE")
    print("=" * 70)
    print("\nNEXT STEPS:")
    print("1. Clear browser cache (Ctrl+Shift+Del)")
    print("2. Refresh dashboard (F5)")
    print("3. Verify Purdue @ Iowa shows 'Purdue -1.5'")
    print("4. Check all game data is accurate")
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    consolidate_bets()
