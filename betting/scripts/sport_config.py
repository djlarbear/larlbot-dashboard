#!/usr/bin/env python3
"""
Sport Configuration - Defines metric mappings for all sports
Allows betting model to adapt to different sports while learning from all
"""

SPORTS_CONFIG = {
    "ncaab": {
        "display_name": "NCAA Basketball",
        "api_endpoint": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
        "metrics": ["pace", "offensive_efficiency", "defensive_efficiency"],
        "model_type": "pace_efficiency",
        "bet_types": ["SPREAD", "TOTAL", "MONEYLINE"],
        "data_source": "espn",
        "active": True,
        "start_date": "2025-11-01",
        "end_date": "2026-04-15",
    },
    
    "nba": {
        "display_name": "NBA Basketball",
        "api_endpoint": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "metrics": ["pace", "offensive_efficiency", "defensive_efficiency"],
        "model_type": "pace_efficiency",
        "bet_types": ["SPREAD", "TOTAL", "MONEYLINE"],
        "data_source": "espn",
        "active": True,
        "start_date": "2025-10-01",
        "end_date": "2026-06-30",
    },
    
    "nhl": {
        "display_name": "NHL Hockey",
        "api_endpoint": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
        "metrics": ["shots_for", "shots_against", "save_pct", "gaa"],
        "model_type": "shot_based",
        "bet_types": ["SPREAD", "TOTAL", "MONEYLINE"],
        "data_source": "espn",
        "active": True,
        "start_date": "2025-10-01",
        "end_date": "2026-06-15",
    },
    
    "nfl": {
        "display_name": "NFL Football",
        "api_endpoint": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
        "metrics": ["yards_per_game", "yards_per_play", "pass_yards", "rush_yards"],
        "model_type": "yardage_based",
        "bet_types": ["SPREAD", "TOTAL", "MONEYLINE"],
        "data_source": "espn",
        "active": False,  # Offseason
        "start_date": "2025-09-01",
        "end_date": "2026-02-15",
    },
}

def get_sport_config(sport_code):
    """Get configuration for a specific sport"""
    return SPORTS_CONFIG.get(sport_code)

def get_active_sports():
    """Get all currently active sports"""
    return [code for code, config in SPORTS_CONFIG.items() if config["active"]]

def get_model_type(sport_code):
    """Get the model type for a sport"""
    config = get_sport_config(sport_code)
    return config["model_type"] if config else None

if __name__ == "__main__":
    print("Active Sports:", get_active_sports())
    for sport in get_active_sports():
        config = get_sport_config(sport)
        print(f"\n{config['display_name']}:")
        print(f"  Model: {config['model_type']}")
        print(f"  Metrics: {', '.join(config['metrics'])}")
