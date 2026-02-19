#!/usr/bin/env python3
"""
Injury Processor v1.0 - Track Player Availability Impact
Fetches injury data and calculates impact on team strength

Impact calculations:
- Star player out: -5 to -10 points of strength
- Key rotation player out: -3 to -5 points
- Bench player out: -1 to -2 points
"""

import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

class InjuryProcessor:
    """Process and track player injuries"""
    
    def __init__(self):
        self.cache_file = 'injury_cache.json'
        self.injury_data = self.load_injury_data()
    
    def load_injury_data(self):
        """Load cached injury data"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_injury_data(self):
        """Save injury data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.injury_data, f, indent=2)
        except:
            pass
    
    def add_injury(self, team, player, status, impact_level='moderate'):
        """Track a player injury
        
        status: 'out', 'questionable', 'doubtful', 'day_to_day'
        impact_level: 'star' (5-10pt), 'key' (3-5pt), 'bench' (1-2pt)
        """
        if team not in self.injury_data:
            self.injury_data[team] = []
        
        injury = {
            'player': player,
            'status': status,
            'impact_level': impact_level,
            'timestamp': datetime.now().isoformat(),
            'impact_points': self.get_impact_value(impact_level, status)
        }
        
        # Remove if already exists
        self.injury_data[team] = [
            i for i in self.injury_data[team] 
            if i['player'].lower() != player.lower()
        ]
        
        # Add new injury
        self.injury_data[team].append(injury)
        self.save_injury_data()
    
    def get_impact_value(self, impact_level, status):
        """Get impact points for an injury"""
        impact_map = {
            'star': {'out': 8, 'doubtful': 5, 'questionable': 2, 'day_to_day': 1},
            'key': {'out': 5, 'doubtful': 3, 'questionable': 1, 'day_to_day': 0.5},
            'bench': {'out': 2, 'doubtful': 1, 'questionable': 0.5, 'day_to_day': 0.25}
        }
        
        return impact_map.get(impact_level, {}).get(status, 1)
    
    def get_team_injury_impact(self, team):
        """Get total injury impact for a team
        
        Returns:
        - total_impact_points: Points of strength reduction
        - out_players: List of players out
        - questionable_players: List of questionable players
        - severity: 'None', 'Minor', 'Moderate', 'Severe'
        """
        if team not in self.injury_data:
            return {
                'team': team,
                'total_impact_points': 0,
                'out_players': [],
                'questionable_players': [],
                'severity': 'None'
            }
        
        injuries = self.injury_data[team]
        out_players = [i for i in injuries if i['status'] == 'out']
        questionable = [i for i in injuries if i['status'] == 'questionable']
        
        total_impact = sum(i['impact_points'] for i in injuries)
        
        # Determine severity
        if total_impact >= 10:
            severity = 'Severe'
        elif total_impact >= 5:
            severity = 'Moderate'
        elif total_impact >= 2:
            severity = 'Minor'
        else:
            severity = 'None'
        
        return {
            'team': team,
            'total_impact_points': round(total_impact, 1),
            'out_players': [{'name': i['player'], 'impact': i['impact_level']} for i in out_players],
            'questionable_players': [{'name': i['player'], 'impact': i['impact_level']} for i in questionable],
            'all_injuries': injuries,
            'severity': severity
        }
    
    def compare_injury_impact(self, team1, team2):
        """Compare injury situation between two teams"""
        impact1 = self.get_team_injury_impact(team1)
        impact2 = self.get_team_injury_impact(team2)
        
        advantage = impact2['total_impact_points'] - impact1['total_impact_points']
        
        return {
            'team1': team1,
            'team2': team2,
            'team1_impact': impact1['total_impact_points'],
            'team2_impact': impact2['total_impact_points'],
            'team1_severity': impact1['severity'],
            'team2_severity': impact2['severity'],
            'advantage': advantage,  # Positive = team1 has injury advantage
            'team1_injuries': impact1,
            'team2_injuries': impact2
        }


if __name__ == '__main__':
    processor = InjuryProcessor()
    
    print("✅ Injury Processor v1.0 Ready")
    print("\nCapabilities:")
    print("  ✓ Track player injuries and status")
    print("  ✓ Calculate injury impact on team strength")
    print("  ✓ Compare injury situations between teams")
    print("  ✓ Cache injury data for fast lookups")
