import sys
sys.path.insert(0, '/Users/macmini/.openclaw/workspace')
import json
from team_strength_calculator import TeamStrengthCalculator

# Load active bets
with open('/Users/macmini/.openclaw/workspace/active_bets.json', 'r') as f:
    data = json.load(f)

calc = TeamStrengthCalculator()

# Update all TOTAL bet reasons with actual predicted totals
for bet in data['bets']:
    if bet['bet_type'] == 'TOTAL':
        try:
            # Parse game to extract teams
            game_parts = bet['game'].split(' @ ')
            if len(game_parts) == 2:
                away = game_parts[0]
                home = game_parts[1]
                
                # Calculate actual expected total
                result = calc.calculate_pace_adjusted_total(away, home)
                expected = result['expected_total']
                market = float(bet['recommendation'].split()[-1])
                
                # Update reason with correct prediction
                lines = bet['reason'].split('\n')
                is_under = 'UNDER' in bet['recommendation']
                predicted = int(round(expected))
                
                if is_under:
                    lines[0] = f"• Model predicts game finishes around {predicted} points (under {market})"
                else:
                    lines[0] = f"• Model predicts game finishes around {predicted} points (over {market})"
                
                bet['reason'] = '\n'.join(lines)
        except Exception as e:
            pass

# Save updated bets
with open('/Users/macmini/.openclaw/workspace/active_bets.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Updated all TOTAL bet reasons with actual predicted totals")
