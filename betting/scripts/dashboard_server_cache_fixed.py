#!/usr/bin/env python3
"""
🎰 LarlBot Dashboard Server - Cache-Fixed Version
Production-ready with reliable cache-busting
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import sys
import glob
import time
import pytz

# Configuration
# Use environment variable or default to current directory
WORKSPACE = os.environ.get('WORKSPACE', '/Users/macmini/.openclaw/workspace')
DATA_DIR = os.path.join(WORKSPACE, 'betting/data')
ACTIVE_BETS_FILE = f"{DATA_DIR}/active_bets.json"
COMPLETED_BETS_PATTERN = f"{DATA_DIR}/completed_bets_*.json"
BET_TRACKER_FILE = f"{DATA_DIR}/bet_tracker_input.json"

# Add workspace to path
sys.path.insert(0, WORKSPACE)

try:
    from cache_manager import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

app = Flask(__name__, 
            template_folder=os.path.join(WORKSPACE, 'templates'),
            static_folder=os.path.join(WORKSPACE, 'static'))

# ============================================================================
# GLOBAL STATE - Used for cache-busting
# ============================================================================
CACHE_BUSTER = int(time.time() * 1000)

# Timezone setup - CRITICAL for proper timestamp handling
EST_TIMEZONE = pytz.timezone('America/Detroit')

def get_est_now():
    """
    Get current time in EST timezone (America/Detroit)
    Returns ISO format string that includes timezone info
    CRITICAL: This ensures Railway UTC times get converted to EST
    """
    now_utc = datetime.now(pytz.UTC)
    now_est = now_utc.astimezone(EST_TIMEZONE)
    return now_est.isoformat()

# ============================================================================
# CACHE CONTROL MIDDLEWARE
# ============================================================================

@app.after_request
def set_cache_headers(response):
    """
    CRITICAL: Set cache headers on EVERY response to prevent stale data
    This runs AFTER every endpoint returns
    ENHANCED: Even stricter cache control for 15-minute refresh system
    """
    # For ALL responses: Prevent browser caching (STRICTEST POSSIBLE)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Vary'] = '*'
    
    # Add unique cache-busting token (changes every request)
    response.headers['X-Cache-Buster'] = str(int(time.time() * 1000))
    response.headers['X-Generated-At'] = get_est_now()
    response.headers['X-Refresh-Cycle'] = '15-minutes'
    
    # For API endpoints: Extra strict + CORS for Railway
    if '/api/' in request.path:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '0'
    
    return response

# ============================================================================
# DATA LOADING
# ============================================================================

def load_json_file(filepath: str) -> Optional[Dict]:
    """Load JSON file safely"""
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def load_active_bets() -> List[Dict]:
    """Load today's active bets"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        active_data = load_json_file(ACTIVE_BETS_FILE)
        
        if not active_data or active_data.get('date') != today:
            return []
        
        bets = active_data.get('bets', [])
        active_bets = [b for b in bets if b.get('result') not in ['WIN', 'LOSS']]
        print(f"✅ Loaded {len(active_bets)} active bets")
        return active_bets
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_top_10_recommendations_for_date(date_str: str) -> List[Dict]:
    """
    Get the list of top 10 recommended bets for a specific date.
    Each recommendation includes: game, bet_type, recommendation text.
    
    Uses corrected LARLScore formula v2.0:
    LARLScore = (confidence/100) × edge × (historical_win_rate / 0.5)
    
    Tries to load from ranked_bets_YYYY-MM-DD.json first.
    Falls back to ranking completed bets by edge score if dated file doesn't exist.
    
    Returns: List of dicts with 'game', 'bet_type', 'recommendation' for each top 10 pick
    """
    # Try to load dated ranked_bets file (e.g., ranked_bets_2026-02-16.json)
    dated_ranked_file = f"{DATA_DIR}/ranked_bets_{date_str}.json"
    ranked_data = load_json_file(dated_ranked_file)
    
    if ranked_data and 'top_10' in ranked_data:
        # Extract top 10 recommendations with corrected formula info
        top_10_items = ranked_data.get('top_10', [])
        recommendations = []
        for item in top_10_items[:10]:  # Ensure exactly 10
            recommendations.append({
                'game': item.get('game', ''),
                'bet_type': item.get('bet_type', ''),
                'recommendation': item.get('recommendation', ''),
                'score': item.get('score', 0),
                'confidence': item.get('confidence', 0),
                'edge': item.get('edge', 0),
                'rank': item.get('rank', 0),
                'larlescore_version': ranked_data.get('larlescore_version', '2.0'),
                'larlescore_formula': ranked_data.get('larlescore_formula', 'LARLScore = (confidence/100) × edge × (win_rate / 0.5)')
            })
        return recommendations
    
    # Fallback: Load completed bets for this date and rank them by edge
    completed_file = f"{DATA_DIR}/completed_bets_{date_str}.json"
    completed_data = load_json_file(completed_file)
    
    if not completed_data or not completed_data.get('bets'):
        return []
    
    # Rank bets by edge score (descending) and take top 10
    bets = completed_data.get('bets', [])
    # Deduplicate by game to get one per game (highest edge)
    seen_games = {}
    for bet in sorted(bets, key=lambda b: b.get('edge', 0), reverse=True):
        game = bet.get('game', '')
        if game and game not in seen_games:
            seen_games[game] = bet
    
    # Take top 10 by edge
    sorted_bets = sorted(seen_games.values(), key=lambda b: b.get('edge', 0), reverse=True)[:10]
    
    recommendations = []
    for bet in sorted_bets:
        recommendations.append({
            'game': bet.get('game', ''),
            'bet_type': bet.get('bet_type', ''),
            'recommendation': bet.get('recommendation', ''),
            'score': bet.get('edge', 0)
        })
    return recommendations

def load_completed_bets() -> List[Dict]:
    """Load all completed bets - includes PENDING (awaiting ESPN scores)"""
    all_completed = []
    
    # Load from tracker
    tracker = load_json_file(BET_TRACKER_FILE)
    if tracker:
        bets = tracker.get('bets', [])
        # Include WIN, LOSS, and PENDING (awaiting scores)
        all_completed.extend([b for b in bets if b.get('result') in ['WIN', 'LOSS', 'PENDING']])
    
    # Load from glob pattern - includes all dates
    for filepath in glob.glob(COMPLETED_BETS_PATTERN):
        data = load_json_file(filepath)
        if data:
            bets = data.get('bets', [])
            # Include WIN, LOSS, and PENDING (awaiting scores)
            all_completed.extend([b for b in bets if b.get('result') in ['WIN', 'LOSS', 'PENDING']])
    
    return all_completed

def calculate_stats(completed_bets: List[Dict]) -> Dict:
    """Calculate win rate and record"""
    if not completed_bets:
        return {'win_rate': 0, 'record': '0-0', 'total_bets': 0}
    
    wins = sum(1 for b in completed_bets if b.get('result') == 'WIN')
    losses = sum(1 for b in completed_bets if b.get('result') == 'LOSS')
    total = len(completed_bets)
    win_rate = int((wins / total * 100)) if total > 0 else 0
    
    return {
        'win_rate': win_rate,
        'record': f"{wins}-{losses}",
        'total_bets': total,
        'wins': wins,
        'losses': losses,
        'timestamp': get_est_now()
    }

def get_top_10_recommended_bets() -> List[Dict]:
    """
    Get top 10 UNIQUE GAMES (not duplicate bets) from each date (for public display stats)
    When a game has multiple bets (SPREAD + TOTAL), select the one with highest edge
    Returns only completed (WIN/LOSS) bets from the top 10 unique games per date
    """
    top_10_bets = []
    
    # Process each date's completed bets
    for filepath in sorted(glob.glob(COMPLETED_BETS_PATTERN)):
        data = load_json_file(filepath)
        if not data:
            continue
        
        bets = data.get('bets', [])
        
        # Group bets by game
        games_dict = {}
        for bet in bets:
            game = bet.get('game', '')
            edge = bet.get('edge', 0)
            
            if game not in games_dict:
                games_dict[game] = []
            
            games_dict[game].append((bet, edge))
        
        # For each unique game, pick the bet with highest edge
        unique_game_bets = []
        for game, variants in games_dict.items():
            best_bet, best_edge = max(variants, key=lambda x: x[1])
            unique_game_bets.append((best_bet, best_edge))
        
        # Sort by edge descending, take top 10 unique games
        unique_game_bets.sort(key=lambda x: x[1], reverse=True)
        top_10_for_date = [bet for bet, edge in unique_game_bets[:10]]
        
        # Add to list
        top_10_bets.extend(top_10_for_date)
    
    return top_10_bets

def calculate_todays_stats() -> Dict:
    """
    Calculate stats from TOP 10 RECOMMENDED BETS ONLY (public-facing display)
    Shows historical performance of the daily recommendations
    Counts only WIN/LOSS bets, excludes PENDING
    
    Backend (Sword) keeps all 38+ bets for internal learning/auditing
    Frontend (Dashboard) shows only top 10 per day recommendations
    """
    # ALWAYS return timestamp - frontend requires it
    default_response = {
        'win_rate': 0, 
        'record': '0-0', 
        'total_bets': 0,
        'wins': 0,
        'losses': 0,
        'completed': 0,
        'timestamp': get_est_now()
    }
    
    # Get only the top 10 recommended bets from each date
    top_10_bets = get_top_10_recommended_bets()
    
    if not top_10_bets:
        return default_response
    
    # Filter to only count bets with WIN or LOSS results
    # Ignore bets with PENDING or no result (games not finished yet)
    completed_bets = [b for b in top_10_bets if b.get('result') in ['WIN', 'LOSS']]
    
    if not completed_bets:
        return default_response
    
    # Count wins and losses
    wins = sum(1 for b in completed_bets if b.get('result') == 'WIN')
    losses = sum(1 for b in completed_bets if b.get('result') == 'LOSS')
    total = wins + losses
    
    # Calculate win rate
    win_rate = int((wins / total * 100)) if total > 0 else 0
    
    return {
        'win_rate': win_rate,
        'record': f"{wins}-{losses}",
        'total_bets': total,
        'wins': wins,
        'losses': losses,
        'completed': total,
        'timestamp': get_est_now()
    }

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    Explicit static file serving for Railway compatibility
    Ensures CSS/JS files are served with correct MIME types
    """
    from flask import send_from_directory
    response = send_from_directory('static', filename)
    
    # Set proper MIME types
    if filename.endswith('.css'):
        response.headers['Content-Type'] = 'text/css; charset=utf-8'
    elif filename.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    
    # Add cache-busting headers (same as API)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/api/bets')
def api_bets():
    """Get active bets (TOP 10 ONLY) - ALWAYS FRESH"""
    # Load ranked bets to get top 10 - try dated file first (TODAY's picks)
    today_str = get_est_now()[:10]  # YYYY-MM-DD
    dated_ranked_file = f'{DATA_DIR}/ranked_bets_{today_str}.json'
    ranked = load_json_file(dated_ranked_file)
    
    # Fallback to main ranked_bets.json if dated file not found
    if not ranked:
        ranked = load_json_file(f'{DATA_DIR}/ranked_bets.json')
    
    if not ranked or 'top_10' not in ranked:
        return jsonify({
            'bets': [],
            'count': 0,
            'timestamp': get_est_now(),
            'error': 'No ranked bets found',
            'cache_buster': int(time.time() * 1000)
        })
    
    # Extract only the top 10 bets (active ones - not finished)
    top_10_items = ranked.get('top_10', [])
    active_bets = []
    
    for item in top_10_items:
        full_bet = item.get('full_bet', {})
        # Only include if not finished (result not WIN/LOSS)
        if full_bet.get('result') not in ['WIN', 'LOSS']:
            active_bets.append(full_bet)
    
    return jsonify({
        'bets': active_bets,
        'count': len(active_bets),
        'top_10_total': len(top_10_items),
        'timestamp': get_est_now(),
        'cache_buster': int(time.time() * 1000)
    })

@app.route('/api/stats')
def api_stats():
    """Get statistics - ONLY for today's recommended bets (top 10) - ALWAYS FRESH"""
    stats = calculate_todays_stats()
    stats['cache_buster'] = int(time.time() * 1000)
    return jsonify(stats)

@app.route('/api/ranked-bets')
def api_ranked_bets():
    """Get ranked bets - returns BOTH active and completed games"""
    # Load today's ranked bets (try dated file first)
    today_str = get_est_now()[:10]  # YYYY-MM-DD
    dated_ranked_file = f'{DATA_DIR}/ranked_bets_{today_str}.json'
    ranked = load_json_file(dated_ranked_file)
    
    # Fallback to main ranked_bets.json if dated file not found
    if not ranked:
        ranked = load_json_file(f'{DATA_DIR}/ranked_bets.json')
    if not ranked:
        return jsonify({'top_10': [], 'active_top10': [], 'completed_top10': [], 'timestamp': get_est_now()})
    
    # Separate active and completed games based on result field
    # If bet has 'result' (WIN/LOSS), it's completed
    # If bet has no result, it's active
    
    def is_game_completed(game_item):
        """Check if game has a result (WIN/LOSS)"""
        full_bet = game_item.get('full_bet', {})
        result = full_bet.get('result')
        # If result is WIN or LOSS, it's completed
        return result in ['WIN', 'LOSS']
    
    all_top10 = ranked.get('top_10', [])
    completed_top10 = [item for item in all_top10 if is_game_completed(item)]
    active_top10 = [item for item in all_top10 if not is_game_completed(item)]
    
    return jsonify({
        'timestamp': get_est_now(),  # Always use current EST time, not file timestamp
        'top_10': all_top10,  # ALL top 10 (for stats calculation)
        'active_top10': active_top10,  # Only active games (for Today's Bets tab)
        'completed_top10': completed_top10,  # Only completed games (for Previous Results tab)
        'total_top10': len(all_top10),
        'active_count': len(active_top10),
        'completed_count': len(completed_top10)
    })

@app.route('/api/previous-results')
def api_previous_results():
    """
    Get previous results - ONLY top 10 recommended bets per day
    Returns results grouped by date with record header
    Matches each recommendation to its exact completed bet (by game, bet_type, recommendation)
    """
    results_by_date = {}
    
    # Load from completed_bets files and filter to top 10 only
    for filepath in glob.glob(COMPLETED_BETS_PATTERN):
        data = load_json_file(filepath)
        if not data:
            continue
            
        date = data.get('date', 'unknown')
        bets = data.get('bets', [])
        
        # Get the top 10 recommendations for this date
        top_10_recommendations = get_top_10_recommendations_for_date(date)
        
        if not top_10_recommendations:
            # No top 10 found for this date, skip
            continue
        
        # For each recommendation, find the exact matching bet in completed_bets
        top_10_bets = []
        for rec in top_10_recommendations:
            # Match by game and bet_type
            matching_bet = None
            for bet in bets:
                if (bet.get('game', '') == rec['game'] and 
                    bet.get('bet_type', '').upper() == rec['bet_type'].upper()):
                    matching_bet = bet
                    break
            
            # If found and has a result, add it
            if matching_bet and matching_bet.get('result') in ['WIN', 'LOSS', 'PENDING']:
                top_10_bets.append(matching_bet)
        
        if top_10_bets:
            results_by_date[date] = top_10_bets
    
    # Build response as flat array with date field in each bet
    # Frontend groups by date client-side, and expects array format
    response = []
    for date in sorted(results_by_date.keys(), reverse=True):
        bets = results_by_date[date]
        
        # CRITICAL: Sort bets consistently within each date
        # This ensures the same order on local and Railway
        # Sort by: 1) Result (WIN first, LOSS second, PENDING last)
        #          2) Confidence (highest first) for secondary ordering
        def sort_key(bet):
            result = bet.get('result', 'PENDING')
            # Map result to sort priority: WIN=0, LOSS=1, PENDING=2
            result_priority = {'WIN': 0, 'LOSS': 1, 'PENDING': 2}.get(result, 2)
            # Get confidence for secondary sort (higher first = negative)
            confidence = -float(bet.get('confidence', 0))
            return (result_priority, confidence)
        
        bets_sorted = sorted(bets, key=sort_key)
        
        # Add date field to each bet so frontend can group them
        for bet in bets_sorted:
            bet['date'] = date
        
        response.extend(bets_sorted)
    
    print(f"✅ Previous results: {len(response)} bets across {len(results_by_date)} dates (sorted consistently)")
    
    return jsonify(response)

@app.route('/api/update-bet-result/<int:rank>', methods=['POST'])
def api_update_bet_result(rank):
    """Update a specific bet's result (rank 1-10)"""
    try:
        data = request.json
        result = data.get('result')  # 'WIN' or 'LOSS'
        final_score = data.get('final_score', '')
        
        if result not in ['WIN', 'LOSS']:
            return jsonify({'error': 'Invalid result. Must be WIN or LOSS'}), 400
        
        if rank < 1 or rank > 10:
            return jsonify({'error': 'Rank must be 1-10'}), 400
        
        ranked = load_json_file(f'{DATA_DIR}/ranked_bets.json')
        if not ranked or not ranked.get('top_10'):
            return jsonify({'error': 'No ranked bets found'}), 404
        
        # Update the bet at the specified rank
        bet_item = ranked['top_10'][rank - 1]
        bet_item['full_bet']['result'] = result
        if final_score:
            bet_item['full_bet']['final_score'] = final_score
        
        # Save updated ranked bets
        with open(f'{DATA_DIR}/ranked_bets.json', 'w') as f:
            json.dump(ranked, f, indent=2)
        
        print(f"✅ Updated bet #{rank}: {result}")
        
        return jsonify({
            'success': True,
            'rank': rank,
            'result': result,
            'timestamp': get_est_now()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug')
def api_debug():
    """Debug endpoint - show what files are available"""
    import os
    files = {
        'ranked_bets': os.path.exists(f'{DATA_DIR}/ranked_bets.json'),
        'active_bets': os.path.exists(f'{WORKSPACE}/active_bets.json'),
        'completed_bets_2026_02_15': os.path.exists(f'{WORKSPACE}/completed_bets_2026-02-15.json'),
        'tracker': os.path.exists(f'{WORKSPACE}/bet_tracker_input.json'),
    }
    
    # Try to load ranked bets to see content
    ranked = load_json_file(f'{DATA_DIR}/ranked_bets.json')
    ranked_count = len(ranked.get('top_10', [])) if ranked else 0
    
    return jsonify({
        'workspace': WORKSPACE,
        'files': files,
        'ranked_bets_count': ranked_count,
        'timestamp': get_est_now()
    })

@app.route('/api/health')
def api_health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': get_est_now(),
        'cache_buster': CACHE_BUSTER,
        'files_available': {
            'active_bets': os.path.exists(ACTIVE_BETS_FILE),
            'tracker': os.path.exists(BET_TRACKER_FILE)
        }
    })

@app.route('/api/formula-info')
def api_formula_info():
    """Get LARLScore formula and historical win rates"""
    try:
        # Load ranked bets to get formula info and win rates
        ranked = load_json_file(f'{DATA_DIR}/ranked_bets.json')
        
        if not ranked:
            ranked = load_json_file(f'{DATA_DIR}/ranked_bets_2026-02-16.json')
        
        if not ranked:
            return jsonify({
                'error': 'No ranked bets found',
                'timestamp': get_est_now()
            }), 404
        
        return jsonify({
            'larlescore_version': ranked.get('larlescore_version', '2.0'),
            'larlescore_formula': ranked.get('larlescore_formula', 'LARLScore = (confidence/100) × edge × (historical_win_rate / 0.5)'),
            'performance_stats': ranked.get('performance_stats', {}),
            'timestamp': get_est_now(),
            'notes': 'Formula v2.0: Properly weights confidence, edge, and historical win rates'
        })
    except Exception as e:
        print(f"Error in /api/formula-info: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    # Railway uses PORT environment variable, default to 5001 for local
    port = int(os.environ.get('PORT', 5001))
    
    print("=" * 70)
    print("🎰 LarlBot Dashboard Server - Cache-Fixed + Timezone-Aware")
    print("=" * 70)
    print(f"📂 Workspace: {WORKSPACE}")
    print(f"🌐 Starting: http://0.0.0.0:{port}")
    print(f"🚫 Cache Control: STRICT (all API responses)")
    print(f"⏰ Server Time (EST): {get_est_now()}")
    print(f"🌍 Timezone: America/Detroit (UTC-5/-4)")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
