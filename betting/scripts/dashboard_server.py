#!/usr/bin/env python3
"""
LarlBot Dashboard Server - Complete Redesign
Flask + HTML/CSS/JS separation for ZERO spacing issues

v2.1: NUCLEAR SPACING OVERRIDE - AGGRESSIVE COMPRESSION
Deployed: 2026-02-14 19:20 EST
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import os
import sys

# Add workspace to path
sys.path.insert(0, '/Users/macmini/.openclaw/workspace')
from cache_manager import CacheManager

app = Flask(__name__, template_folder='templates', static_folder='static')

def load_bets():
    """Load bet data from active_bets.json (today's picks ONLY)"""
    try:
        from datetime import datetime
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Try to load active bets for today
        try:
            with open('active_bets.json', 'r') as f:
                active_data = json.load(f)
                
                # CRITICAL: Only return bets if they're for TODAY
                if active_data.get('date') == today and active_data.get('bets'):
                    bets = active_data.get('bets', [])
                    # Double-check: filter out any completed bets
                    bets = [b for b in bets if b.get('result') not in ['WIN', 'LOSS']]
                    print(f"✅ Loaded {len(bets)} active bets for {today}")
                    return bets
                else:
                    # Date mismatch - regenerate for today
                    print(f"⚠️ active_bets.json date mismatch. Expected {today}, got {active_data.get('date')}")
        except Exception as e:
            print(f"⚠️ Error reading active_bets.json: {e}")
        
        # Generate today's picks and save them
        from daily_recommendations import get_todays_value_bets
        bets = get_todays_value_bets()
        
        # Auto-save to active_bets.json
        active_data = {
            'date': today,
            'bets': bets
        }
        with open('active_bets.json', 'w') as f:
            json.dump(active_data, f, indent=2)
        
        print(f"✅ Generated and saved {len(bets)} new bets for {today}")
        return bets
    except Exception as e:
        print(f"❌ Error loading bets: {e}")
        return []

def load_stats():
    """Load statistics from all completed bets (with caching)"""
    # Check cache first
    cached = CacheManager.get_cache('bet_stats')
    if cached:
        return cached
    
    all_completed = []
    
    # Load from bet_tracker_input.json
    try:
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
            bets = tracker.get('bets', [])
            completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
            all_completed.extend(completed)
    except Exception as e:
        print(f"⚠️ Error loading bet_tracker_input.json: {e}")
    
    # Load from completed_bets_*.json files
    import glob
    for filename in glob.glob('completed_bets_*.json'):
        try:
            with open(filename, 'r') as f:
                completed_file = json.load(f)
                bets = completed_file.get('bets', [])
                completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
                all_completed.extend(completed)
        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")
    
    # Calculate stats (only WIN/LOSS, skip PENDING)
    if all_completed:
        wins = sum(1 for b in all_completed if b.get('result') == 'WIN')
        losses = sum(1 for b in all_completed if b.get('result') == 'LOSS')
        total = len(all_completed)
        win_rate = int((wins / total * 100)) if total > 0 else 0
        
        stats = {
            'win_rate': win_rate,
            'record': f"{wins}-{losses}",
            'total_bets': total
        }
    else:
        stats = {'win_rate': 0, 'record': '0-0', 'total_bets': 0}
    
    # Cache the result
    CacheManager.set_cache('bet_stats', stats)
    return stats

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/bets')
def api_bets():
    """API endpoint for bet data"""
    bets = load_bets()
    return jsonify(bets)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = load_stats()
    return jsonify(stats)

@app.route('/api/ranked-bets')
def api_ranked_bets():
    """API endpoint for ranked bets (Top 10 + rest)"""
    try:
        with open('ranked_bets.json', 'r') as f:
            ranked = json.load(f)
            return jsonify(ranked)
    except Exception as e:
        print(f"⚠️ Error loading ranked_bets.json: {e}")
        # Fallback: return unranked bets
        bets = load_bets()
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'performance_stats': {'by_type': {}},
            'top_10': [{'rank': i+1, 'score': 0, 'full_bet': b} for i, b in enumerate(bets[:10])],
            'rest': [{'rank': i+11, 'score': 0, 'full_bet': b} for i, b in enumerate(bets[10:])]
        })

@app.route('/api/previous-results')
def api_previous_results():
    """API endpoint for previous betting results (cached, ONLY completed bets, no PENDING)"""
    # Check cache first
    cached = CacheManager.get_cache('completed_bets')
    if cached:
        return jsonify(cached)
    
    all_completed = []
    
    # Load from bet_tracker_input.json (manual tracking)
    try:
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
            bets = tracker.get('bets', [])
            # ONLY include WIN/LOSS, exclude PENDING
            completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
            all_completed.extend(completed)
    except Exception as e:
        print(f"⚠️ Error loading bet_tracker_input.json: {e}")
    
    # Load from completed_bets_*.json files (auto-tracked via browser scraper)
    import glob
    for filename in glob.glob('completed_bets_*.json'):
        try:
            with open(filename, 'r') as f:
                completed_file = json.load(f)
                bets = completed_file.get('bets', [])
                # ONLY include WIN/LOSS, exclude PENDING
                completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
                all_completed.extend(completed)
        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")
    
    # Ensure all bets have a date field
    from datetime import datetime as dt
    for bet in all_completed:
        if not bet.get('date'):
            # Try to extract from completed_at ISO timestamp
            if bet.get('completed_at'):
                try:
                    completed_dt = dt.fromisoformat(bet['completed_at'].replace('Z', '+00:00'))
                    bet['date'] = completed_dt.strftime('%Y-%m-%d')
                except:
                    # Use date from filename if available
                    # Default to today if nothing else works
                    bet['date'] = dt.now().strftime('%Y-%m-%d')
            else:
                # Default to today
                bet['date'] = dt.now().strftime('%Y-%m-%d')
    
    # Sort by date (most recent first)
    all_completed.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Cache the result
    CacheManager.set_cache('completed_bets', all_completed)
    return jsonify(all_completed)

@app.route('/api/update-result', methods=['POST'])
def api_update_result():
    """Update a bet with final result and move to tracker"""
    try:
        from datetime import datetime
        data = request.get_json()
        game = data.get('game')
        result = data.get('result')  # WIN or LOSS
        final_score = data.get('final_score', '')
        
        # Load active bets
        with open('active_bets.json', 'r') as f:
            active_data = json.load(f)
        
        bets = active_data.get('bets', [])
        bet_to_move = None
        
        # Find and update the bet
        for bet in bets:
            if bet.get('game') == game:
                bet['result'] = result
                bet['final_score'] = final_score
                bet_to_move = bet
                break
        
        if not bet_to_move:
            return jsonify({'error': 'Bet not found'}), 404
        
        # Move to tracker
        with open('bet_tracker_input.json', 'r') as f:
            tracker = json.load(f)
        
        tracker['bets'].append(bet_to_move)
        
        # Save tracker
        with open('bet_tracker_input.json', 'w') as f:
            json.dump(tracker, f, indent=2)
        
        # Remove from active bets
        bets = [b for b in bets if b.get('game') != game]
        active_data['bets'] = bets
        
        with open('active_bets.json', 'w') as f:
            json.dump(active_data, f, indent=2)
        
        print(f"[{datetime.now()}] ✅ Moved {game} ({result}) to Previous Results")
        
        return jsonify({'success': True, 'message': f'Moved {game} to Previous Results'})
    except Exception as e:
        print(f"Error updating result: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bfr')
def api_bfr():
    """API endpoint for Big Fat Rodent of the Day"""
    import random
    rodents = [
        {
            'name': 'Richard the Rat',
            'image': 'https://images.unsplash.com/photo-1585110396000-c9fbe2915b6c?w=400',
            'caption': 'Blessed by the Rodent Gods 🐭✨'
        },
        {
            'name': 'Whisker McWhisk',
            'image': 'https://images.unsplash.com/photo-1615751072765-f0fccf45ae5d?w=400',
            'caption': 'Today\'s luck champion! 🍀'
        },
        {
            'name': 'Big Cheese',
            'image': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400',
            'caption': 'Living the cheddar dream 🧀'
        },
        {
            'name': 'Sneaky Steve',
            'image': 'https://images.unsplash.com/photo-1629217245884-73d1b9fb79ed?w=400',
            'caption': 'Master of the odds 🎯'
        },
        {
            'name': 'Velvet Paws',
            'image': 'https://images.unsplash.com/photo-1618826411640-d6df44dd3f7a?w=400',
            'caption': 'Smooth operator 😎'
        }
    ]
    
    # Use date as seed for consistent BFR per day
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    random.seed(hash(today) % 2**32)
    rodent = random.choice(rodents)
    return jsonify(rodent)

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Get port from environment (for Railway/Heroku deployment)
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    if debug or port == 5001:
        print("🎰 LarlBot Dashboard Server (NEW DESIGN)")
        print("Running on http://localhost:5001")
        print("Press CTRL+C to stop\n")
        app.run(debug=True, port=port, host='127.0.0.1')
    else:
        # Production mode (Railway/Heroku)
        app.run(debug=False, port=port, host='0.0.0.0')
