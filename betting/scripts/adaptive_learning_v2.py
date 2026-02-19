#!/usr/bin/env python3
"""
Adaptive Learning System v2.0
Analyzes losses to find patterns and adjusts recommendations

Key insight: When we lose, we learn what the OPPOSITE side would have won
Example: UConn -12.5 LOSS (won by 4) → Georgetown +12.5 would WIN
This tells us: Our confidence in favorites is too high

Strategy:
1. Analyze each loss - what was the opposite bet?
2. Track patterns - are we consistently wrong on spreads? Moneylines? Favorites?
3. Adjust future picks - increase confidence on opposite sides that would have won
4. Build "confidence adjustments" to apply to similar future bets
"""

import json
from datetime import datetime
import glob

def analyze_loss_opposite(loss_bet):
    """
    For a losing bet, calculate what the OPPOSITE bet would have been
    
    Example loss:
    - Game: Georgetown @ UConn
    - Bet: UConn -12.5 (LOSS - score 75-79, UConn +4)
    - Opposite: Georgetown +12.5 (would WIN - 75 > 79-12.5=66.5)
    """
    
    bet_type = loss_bet.get('bet_type', '')
    recommendation = loss_bet.get('recommendation', '')
    final_score = loss_bet.get('final_score', '')
    away_score = loss_bet.get('away_score')
    home_score = loss_bet.get('home_score')
    
    if not final_score or (away_score is None and home_score is None):
        return None
    
    # Parse scores if not separate
    if away_score is None or home_score is None:
        try:
            parts = final_score.split('-')
            away_score = int(parts[0])
            home_score = int(parts[1])
        except:
            return None
    
    # Calculate actual margin (home_score - away_score)
    actual_margin = home_score - away_score  # Positive = home won
    
    analysis = {
        'game': loss_bet.get('game', ''),
        'original_bet': recommendation,
        'bet_type': bet_type,
        'final_score': f"{away_score}-{home_score}",
        'actual_margin': actual_margin,
        'away_score': away_score,
        'home_score': home_score,
    }
    
    # Determine opposite side
    if bet_type == 'SPREAD':
        try:
            # Extract line from recommendation (e.g., "UConn -12.5" -> -12.5)
            parts = recommendation.split()
            line_str = parts[-1]
            line = float(line_str)
            
            # Opposite would be the other team with opposite line
            team = ' '.join(parts[:-1])
            opposite_line = -line
            
            # Check if opposite would win
            # If we bet on favorite (negative line) and lost, opposite is underdog
            # Underdog covers if actual_margin < abs(line) and they won, or lost by less
            
            if line < 0:
                # We bet favorite to cover
                # Opposite is underdog (positive line)
                would_win = abs(actual_margin) < abs(line)
            else:
                # We bet underdog
                # Opposite is favorite
                would_win = actual_margin > line
            
            analysis['opposite_bet'] = f"{'Other team' if line < 0 else 'Favorite'} {opposite_line:+.1f}"
            analysis['opposite_would_win'] = would_win
            analysis['confidence_in_wrong_side'] = loss_bet.get('confidence', 0)
            
        except Exception as e:
            print(f"  Error analyzing SPREAD: {e}")
    
    elif bet_type == 'MONEYLINE':
        # If we bet Team A and they lost, Team B would win
        analysis['opposite_bet'] = "Other team ML"
        analysis['opposite_would_win'] = True  # Opposite always wins if this lost
        analysis['confidence_in_wrong_side'] = loss_bet.get('confidence', 0)
    
    elif bet_type == 'TOTAL':
        # If we bet UNDER and lost (total was high), OVER would win
        # If we bet OVER and lost (total was low), UNDER would win
        try:
            line = loss_bet.get('line', 0)
            total = away_score + home_score
            
            if 'UNDER' in recommendation:
                analysis['opposite_bet'] = f"OVER {line}"
                analysis['opposite_would_win'] = total > line
            else:
                analysis['opposite_bet'] = f"UNDER {line}"
                analysis['opposite_would_win'] = total < line
            
            analysis['confidence_in_wrong_side'] = loss_bet.get('confidence', 0)
        except:
            pass
    
    return analysis

def build_learning_insights():
    """Analyze all past bets to find patterns in losses"""
    
    print("\n" + "="*80)
    print("🧠 ADAPTIVE LEARNING ANALYSIS")
    print("="*80)
    
    all_bets = []
    
    # Load all bets from all sources
    for filepath in glob.glob('completed_bets_*.json'):
        with open(filepath, 'r') as f:
            data = json.load(f)
            all_bets.extend(data.get('bets', []))
    
    # Load from bet_tracker_input.json too
    try:
        with open('bet_tracker_input.json', 'r') as f:
            data = json.load(f)
            all_bets.extend(data.get('bets', []))
    except:
        pass
    
    # Separate wins and losses
    wins = [b for b in all_bets if b.get('result') == 'WIN']
    losses = [b for b in all_bets if b.get('result') == 'LOSS']
    
    print(f"\n📊 OVERALL RECORD")
    print(f"  Wins: {len(wins)}")
    print(f"  Losses: {len(losses)}")
    print(f"  Win Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%")
    
    # Analyze losses
    print(f"\n🔍 ANALYZING {len(losses)} LOSSES")
    print("-" * 80)
    
    loss_patterns = {
        'spread_favorites_losing': [],  # We bet favorites to cover and they didn't
        'moneyline_wrong': [],
        'underdog_value_misses': [],  # Opposite would have won
        'confidence_mismatches': [],  # High confidence but lost
    }
    
    for i, loss in enumerate(losses, 1):
        analysis = analyze_loss_opposite(loss)
        if not analysis:
            continue
        
        print(f"\n{i}. {loss.get('game', 'Unknown')[:50]}")
        print(f"   Our Bet: {loss.get('recommendation')}")
        print(f"   Score: {analysis['final_score']} (margin: {analysis['actual_margin']:+d})")
        print(f"   Confidence: {loss.get('confidence', 'N/A')}%")
        
        if analysis.get('opposite_would_win'):
            print(f"   💡 Opposite Would WIN: {analysis.get('opposite_bet')}")
            loss_patterns['underdog_value_misses'].append(analysis)
            
            # High confidence but wrong?
            if loss.get('confidence', 0) >= 80:
                loss_patterns['confidence_mismatches'].append(analysis)
        
        if loss.get('bet_type') == 'SPREAD':
            # Check if we were betting favorite
            if '-' in loss.get('recommendation', ''):
                loss_patterns['spread_favorites_losing'].append(analysis)
    
    # Generate insights
    print(f"\n\n{'='*80}")
    print("📈 LEARNING INSIGHTS")
    print("="*80)
    
    print(f"\n🎯 KEY FINDINGS:")
    print(f"  • Spread Favorites Losing: {len(loss_patterns['spread_favorites_losing'])} instances")
    print(f"    (We're betting favorites to cover too often)")
    
    print(f"  • Underdog Value Misses: {len(loss_patterns['underdog_value_misses'])} instances")
    print(f"    (Opposite side would have won)")
    
    print(f"  • High Confidence Wrong: {len(loss_patterns['confidence_mismatches'])} instances")
    print(f"    (80%+ confidence but still lost)")
    
    # Specific example
    print(f"\n💡 SPECIFIC EXAMPLE: Georgetown @ UConn")
    for loss in losses:
        if 'Georgetown' in loss.get('game', '') and 'UConn' in loss.get('game', ''):
            if loss.get('bet_type') == 'SPREAD':
                analysis = analyze_loss_opposite(loss)
                print(f"  • We bet: {loss.get('recommendation')}")
                print(f"  • Score: {loss.get('final_score')}")
                print(f"  • Opposite would have been: {analysis.get('opposite_bet')}")
                print(f"  • Would that have won? {analysis.get('opposite_would_win')}")
                print(f"  • Our confidence: {loss.get('confidence')}%")
                print(f"  • LESSON: Too confident in {loss.get('recommendation').split()[0]}")
                break
    
    # Recommendations
    print(f"\n🎓 RECOMMENDATIONS FOR IMPROVEMENT:")
    print(f"  1. Reduce confidence in favorites to cover (especially big lines)")
    print(f"  2. Give more consideration to underdog spreads")
    print(f"  3. For high-confidence bets (80%+), require higher edges")
    print(f"  4. Track when opposite side would have won - adjust model weights")
    print(f"  5. Consider suggesting BOTH sides when confidence is similar")
    
    # Save insights
    insights = {
        'generated_at': datetime.now().isoformat(),
        'total_bets': len(all_bets),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': (len(wins)/(len(wins)+len(losses))*100) if (len(wins)+len(losses))>0 else 0,
        'patterns': {
            'spread_favorites_losing': len(loss_patterns['spread_favorites_losing']),
            'underdog_value_misses': len(loss_patterns['underdog_value_misses']),
            'high_confidence_wrong': len(loss_patterns['confidence_mismatches']),
        },
        'example_losses': loss_patterns['underdog_value_misses'][:5]  # First 5 misses
    }
    
    with open('learning_insights.json', 'w') as f:
        json.dump(insights, f, indent=2)
    
    print(f"\n✅ Learning insights saved to learning_insights.json")
    return insights

if __name__ == '__main__':
    build_learning_insights()
