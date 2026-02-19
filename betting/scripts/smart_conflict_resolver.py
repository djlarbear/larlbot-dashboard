#!/usr/bin/env python3
"""
Smart Conflict Resolution

Detects contradictory bets and suggests OPPOSITE SPREAD as alternative

Logic:
- If we recommend: Charlotte -14.5 (confident)
- AND moneyline: UTSA wins (also confident)
- CONFLICT! These can't both be true

Smart solution:
- Remove conflicting moneyline
- Consider flipping to: UTSA +14.5 (get 14.5 points + underdog team)
- This gives user the BETTER play

Example analysis:
  Recommend: Charlotte -14.5 @ 94%
  Moneyline: UTSA @ 84%
  
  Analysis: 
    If UTSA has 84% moneyline confidence, they're a strong team
    UTSA +14.5 means you get 14.5 points AND a team that might win
    This is better value than Charlotte needing to win by 15+
    
  Suggestion: "Consider UTSA +14.5 instead - better value with moneyline confidence"
"""

import json
from collections import defaultdict

def suggest_opposite_spread(spread_rec):
    """Generate opposite spread recommendation"""
    # Example: "Charlotte 49ers -14.5" -> suggest underdog +14.5
    parts = spread_rec.rsplit(' ', 1)
    if len(parts) == 2:
        team = parts[0]
        line = float(parts[1])
        opposite_line = -line
        return f"{team} {opposite_line:+.1f}"
    return None

def extract_teams(game_str):
    """Extract away and home team from game string"""
    # Format: "Away Team @ Home Team"
    if ' @ ' in game_str:
        parts = game_str.split(' @ ')
        return parts[0].strip(), parts[1].strip()
    return None, None

def analyze_spread_vs_moneyline(spread_bet, ml_bet, game):
    """
    Analyze if spread and moneyline conflict
    Return: (has_conflict, analysis_text, suggestion)
    """
    
    spread_rec = spread_bet.get('recommendation', '')
    ml_rec = ml_bet.get('recommendation', '').replace(' (Moneyline)', '')
    spread_conf = spread_bet.get('confidence', 0)
    ml_conf = ml_bet.get('confidence', 0)
    
    # Extract teams
    away_team, home_team = extract_teams(game)
    
    # Which team is recommended in spread?
    spread_team = spread_rec.rsplit(' ', 1)[0] if ' -' in spread_rec or ' +' in spread_rec else spread_rec
    
    # Do they conflict?
    if spread_team != ml_rec:
        # CONFLICT: Different teams recommended
        opposite_spread = suggest_opposite_spread(spread_rec)
        
        analysis = f"""
CONFLICT DETECTED:
  Spread: {spread_rec} ({spread_conf}%)
  Moneyline: {ml_rec} ({ml_conf}%)
  
WHY THIS IS WRONG:
  • {spread_team} must win by 15+ points
  • BUT {ml_rec} is predicted to win straight up
  • These contradict each other
  
BETTER ALTERNATIVE:
  • Instead of {spread_rec}
  • Consider: {opposite_spread}
  • Why: You get the underdog + 14.5 points, AND the team that might win
  • This is higher probability of winning
"""
        
        return True, analysis, opposite_spread
    
    return False, "", None

def analyze_all_conflicts():
    """Analyze all conflicts and suggest alternatives"""
    
    with open('active_bets.json', 'r') as f:
        data = json.load(f)
    
    bets = data.get('bets', [])
    
    # Group by game
    games = defaultdict(list)
    for bet in bets:
        games[bet.get('game', '')].append(bet)
    
    print("\n" + "="*80)
    print("🧠 SMART CONFLICT ANALYSIS")
    print("="*80)
    
    suggestions = []
    
    for game, game_bets in sorted(games.items()):
        spreads = [b for b in game_bets if b.get('bet_type') == 'SPREAD']
        moneylines = [b for b in game_bets if b.get('bet_type') == 'MONEYLINE']
        
        if spreads and moneylines:
            spread_bet = spreads[0]
            ml_bet = moneylines[0]
            
            has_conflict, analysis, suggestion = analyze_spread_vs_moneyline(
                spread_bet, ml_bet, game
            )
            
            if has_conflict:
                print(f"\n🔍 {game}")
                print(analysis)
                suggestions.append({
                    'game': game,
                    'original_spread': spread_bet.get('recommendation'),
                    'conflicting_ml': ml_bet.get('recommendation'),
                    'suggested_opposite': suggestion
                })
    
    # Summary
    print("\n" + "="*80)
    print("💡 ALTERNATIVE SUGGESTIONS FOR SMARTER BETTING")
    print("="*80)
    
    if suggestions:
        print(f"\nFound {len(suggestions)} conflicting pairs:")
        for i, sugg in enumerate(suggestions, 1):
            print(f"\n{i}. {sugg['game']}")
            print(f"   ❌ Original: {sugg['original_spread']}")
            print(f"   💡 Better: {sugg['suggested_opposite']}")
            print(f"   Why: Get the underdog + points + team that can win")
    else:
        print("✅ No conflicting spread/moneyline pairs found")
    
    return suggestions

if __name__ == '__main__':
    analyze_all_conflicts()
