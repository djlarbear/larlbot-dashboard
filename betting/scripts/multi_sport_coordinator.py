#!/usr/bin/env python3
"""
Multi-Sport Coordinator
Orchestrates pick generation across all sports and updates dashboard
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

from sport_config import get_active_sports, get_sport_config
from multi_sport_dashboard_config import DASHBOARD_CONFIG

class MultiSportCoordinator:
    """Coordinates betting across all sports"""
    
    def __init__(self):
        self.workspace = Path('/Users/macmini/.openclaw/workspace')
        self.dashboard_dir = Path('/Users/macmini/.openclaw/agents/sword')
        
    def collect_all_picks(self, date_str):
        """
        Collect picks from all sports for a given date
        
        Returns:
            {
                'date': date_str,
                'sports': {
                    'ncaab': [...10 picks],
                    'nba': [...10 picks],
                    'nhl': [...10 picks (if available)]
                },
                'combined_top_10': [...],
            }
        """
        
        all_picks = {'date': date_str, 'sports': {}}
        
        # NCAA: Load from ranked_bets.json (today) 
        ncaab_file = self.workspace / 'ranked_bets.json'
        if ncaab_file.exists():
            try:
                with open(ncaab_file, 'r') as f:
                    data = json.load(f)
                # Get top 10
                ncaab_picks = data.get('top_10', [])[:10]
                all_picks['sports']['ncaab'] = ncaab_picks
                print(f"✅ Loaded {len(ncaab_picks)} NCAA picks")
            except Exception as e:
                print(f"⚠️ Error loading NCAA picks: {e}")
                all_picks['sports']['ncaab'] = []
        else:
            print(f"⏳ No NCAA picks file found")
            all_picks['sports']['ncaab'] = []
        
        # NBA: Load from nba_picks_DATE.json (for the requested date)
        nba_file = self.workspace / f"nba_picks_{date_str}.json"
        if nba_file.exists():
            try:
                with open(nba_file, 'r') as f:
                    nba_picks = json.load(f)[:10]
                all_picks['sports']['nba'] = nba_picks
                print(f"✅ Loaded {len(nba_picks)} NBA picks")
            except Exception as e:
                print(f"⚠️ Error loading NBA picks: {e}")
                all_picks['sports']['nba'] = []
        else:
            print(f"⏳ No NBA picks file yet for {date_str}")
            all_picks['sports']['nba'] = []
        
        # NHL: Load from nhl_picks_DATE.json (if available)
        nhl_file = self.workspace / f"nhl_picks_{date_str}.json"
        if nhl_file.exists():
            try:
                with open(nhl_file, 'r') as f:
                    nhl_picks = json.load(f)[:10]
                all_picks['sports']['nhl'] = nhl_picks
                print(f"✅ Loaded {len(nhl_picks)} NHL picks")
            except Exception as e:
                print(f"⚠️ Error loading NHL picks: {e}")
                all_picks['sports']['nhl'] = []
        else:
            print(f"⏳ No NHL picks file yet for {date_str}")
            all_picks['sports']['nhl'] = []
        
        # Generate combined top 10 across all sports
        all_picks['combined_top_10'] = self.get_combined_top_10(all_picks['sports'])
        
        return all_picks
    
    def get_combined_top_10(self, sports_picks):
        """Get top 10 picks across all sports, ranked by edge"""
        all_bets = []
        
        for sport_code, picks in sports_picks.items():
            for pick in picks:
                pick['sport'] = sport_code
                all_bets.append(pick)
        
        # Sort by edge descending
        all_bets.sort(key=lambda x: float(x.get('edge', 0)), reverse=True)
        
        # Return top 10
        return all_bets[:10]
    
    def update_dashboard_data(self, date_str):
        """Update dashboard with multi-sport picks"""
        all_picks = self.collect_all_picks(date_str)
        
        # Save to dashboard directory
        dashboard_file = self.dashboard_dir / 'multi_sport_picks.json'
        try:
            with open(dashboard_file, 'w') as f:
                json.dump(all_picks, f, indent=2)
            print(f"✅ Updated {dashboard_file}")
            return True
        except Exception as e:
            print(f"❌ Error updating dashboard: {e}")
            return False
    
    def get_status(self):
        """Get current status of all sports"""
        print("\n=== MULTI-SPORT COORDINATOR STATUS ===\n")
        
        for sport_code in get_active_sports():
            config = get_sport_config(sport_code)
            picks_file = self.workspace / f"{sport_code}_picks_2026-02-19.json"
            
            status = "✅ Ready" if picks_file.exists() else "⏳ In Progress"
            print(f"{config['display_name']:20} {status}")
        
        print("\n=== CURRENT DASHBOARD ===")
        dashboard_file = self.dashboard_dir / 'multi_sport_picks.json'
        if dashboard_file.exists():
            with open(dashboard_file, 'r') as f:
                data = json.load(f)
            print(f"Date: {data.get('date')}")
            print(f"Sports loaded: {list(data.get('sports', {}).keys())}")
            print(f"Combined top 10: {len(data.get('combined_top_10', []))}")
        else:
            print("Dashboard not yet created")

if __name__ == "__main__":
    coordinator = MultiSportCoordinator()
    
    # Check current status
    coordinator.get_status()
    
    # Try to update dashboard with available picks
    print("\n=== UPDATING DASHBOARD ===")
    coordinator.update_dashboard_data('2026-02-19')
