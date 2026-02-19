#!/usr/bin/env python3
"""
Multi-Sport Dashboard Configuration
Extends dashboard to show 10 picks per sport + 10 combined top picks
"""

DASHBOARD_CONFIG = {
    "views": [
        {
            "name": "All Sports Combined",
            "type": "combined_top_10",
            "picks": 10,
            "filters": None,
            "sort_by": "edge",
        },
        {
            "name": "NCAA Basketball",
            "type": "sport_specific",
            "sport": "ncaab",
            "picks": 10,
            "filters": {"bet_type": "TOTAL"},  # Prioritize TOTAL (70% win rate)
            "sort_by": "edge",
        },
        {
            "name": "NBA Basketball",
            "type": "sport_specific",
            "sport": "nba",
            "picks": 10,
            "filters": {"bet_type": "TOTAL"},
            "sort_by": "edge",
            "active_from": "2026-02-19",
        },
        {
            "name": "NHL Hockey",
            "type": "sport_specific",
            "sport": "nhl",
            "picks": 10,
            "filters": None,
            "sort_by": "edge",
            "active_from": "2026-02-25",
        },
    ],
    
    "performance_view": {
        "by_sport": True,
        "by_bet_type": True,
        "by_confidence": True,
        "display": [
            "win_rate",
            "total_bets",
            "recent_performance",
            "confidence_trend",
        ],
    },
    
    "learning_display": {
        "best_performing_sport": True,
        "worst_performing_sport": True,
        "recommendations": True,
        "sample_sizes": True,
    },
}

def get_sport_view(sport_code):
    """Get view config for a specific sport"""
    for view in DASHBOARD_CONFIG["views"]:
        if view.get("sport") == sport_code:
            return view
    return None

def is_sport_active(sport_code, current_date="2026-02-18"):
    """Check if sport is active on given date"""
    view = get_sport_view(sport_code)
    if not view:
        return False
    
    if "active_from" in view:
        return current_date >= view["active_from"]
    
    return True

if __name__ == "__main__":
    print("Dashboard Views:")
    for view in DASHBOARD_CONFIG["views"]:
        print(f"  - {view['name']} ({view['type']})")
    
    print("\nActive Sports on Feb 19:")
    for view in DASHBOARD_CONFIG["views"]:
        if view["type"] == "sport_specific":
            active = is_sport_active(view["sport"], "2026-02-19")
            print(f"  - {view['name']}: {'ACTIVE' if active else 'INACTIVE'}")
