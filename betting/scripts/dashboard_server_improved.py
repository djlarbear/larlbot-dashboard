#!/usr/bin/env python3
"""
🎰 LarlBot Dashboard Server v3.0
Improved version with better error handling and code quality

Key improvements:
- Robust error handling for missing files
- Clean function structure with single responsibility
- Better logging and debugging
- Caching for performance
- Type hints for clarity
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import sys
import glob
import hashlib

# Configuration
WORKSPACE = "/Users/macmini/.openclaw/workspace"
ACTIVE_BETS_FILE = f"{WORKSPACE}/active_bets.json"
COMPLETED_BETS_PATTERN = f"{WORKSPACE}/completed_bets_*.json"
BET_TRACKER_FILE = f"{WORKSPACE}/bet_tracker_input.json"

# Add workspace to path for imports
sys.path.insert(0, WORKSPACE)

try:
    from cache_manager import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("⚠️ CacheManager not available, caching disabled")

app = Flask(__name__, template_folder='templates', static_folder='static')

# ============================================================================
# CACHE-BUSTING & ANTI-CACHE MIDDLEWARE
# ============================================================================

@app.after_request
def add_no_cache_headers(response):
    """Add headers to prevent browser caching of dynamic content"""
    try:
        path = request.path
        
        # Prevent caching of API responses (CRITICAL for data freshness)
        if '/api/' in path:
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
            response.cache_control.max_age = 0
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        
        # Version HTML files with timestamp
        elif path.endswith('.html') or path == '/':
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
            response.cache_control.max_age = 0
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # Add timestamp header for debugging
        response.headers['X-Generated-At'] = datetime.now().isoformat()
        response.headers['X-Cache-Buster'] = str(int(__import__('time').time()))
    except Exception as e:
        print(f"Warning in cache headers: {e}")
    
    return response

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_json_file(filepath: str) -> Optional[Dict]:
    """
    Safely load a JSON file.
    Returns None if file doesn't exist or has invalid JSON.
    """
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return None

def get_cached(key: str) -> Optional[Dict]:
    """Get value from cache if available"""
    if CACHE_AVAILABLE:
        return CacheManager.get_cache(key)
    return None

def set_cached(key: str, value: Dict):
    """Set value in cache if available"""
    if CACHE_AVAILABLE:
        CacheManager.set_cache(key, value)

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_active_bets() -> List[Dict]:
    """
    Load active (non-finished) bets for today's dashboard.
    Returns: List of bet dictionaries
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Load active bets file
        active_data = load_json_file(ACTIVE_BETS_FILE)
        if not active_data:
            print(f"⚠️ No active bets file found")
            return []
        
        # Verify it's for today
        if active_data.get('date') != today:
            print(f"⚠️ Active bets are from {active_data.get('date')}, not today ({today})")
            return []
        
        # Get bets and filter out any completed ones
        bets = active_data.get('bets', [])
        active_bets = [b for b in bets if b.get('result') not in ['WIN', 'LOSS']]
        
        print(f"✅ Loaded {len(active_bets)} active bets for {today}")
        return active_bets
        
    except Exception as e:
        print(f"❌ Error loading active bets: {e}")
        return []

def load_completed_bets() -> List[Dict]:
    """
    Load all completed bets with WIN/LOSS results.
    Returns: List of bet dictionaries
    """
    all_completed = []
    
    # Load from bet_tracker_input.json if exists
    tracker = load_json_file(BET_TRACKER_FILE)
    if tracker:
        bets = tracker.get('bets', [])
        completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
        all_completed.extend(completed)
    
    # Load from completed_bets_*.json files
    for filepath in glob.glob(COMPLETED_BETS_PATTERN):
        data = load_json_file(filepath)
        if data:
            bets = data.get('bets', [])
            completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
            all_completed.extend(completed)
    
    return all_completed

def calculate_stats(completed_bets: List[Dict]) -> Dict:
    """
    Calculate statistics from completed bets.
    Returns: Dict with win_rate, record, total_bets
    """
    if not completed_bets:
        return {
            'win_rate': 0,
            'record': '0-0',
            'total_bets': 0
        }
    
    wins = sum(1 for b in completed_bets if b.get('result') == 'WIN')
    losses = sum(1 for b in completed_bets if b.get('result') == 'LOSS')
    total = len(completed_bets)
    win_rate = int((wins / total * 100)) if total > 0 else 0
    
    return {
        'win_rate': win_rate,
        'record': f"{wins}-{losses}",
        'total_bets': total,
        'wins': wins,
        'losses': losses
    }

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard HTML"""
    return render_template('index.html')

@app.route('/api/bets')
def api_bets():
    """API endpoint: Get active bets for Today's Bets tab"""
    bets = load_active_bets()
    return jsonify(bets)

@app.route('/api/stats')
def api_stats():
    """API endpoint: Get betting statistics"""
    # Check cache first
    cached_stats = get_cached('bet_stats')
    if cached_stats:
        return jsonify(cached_stats)
    
    # Load and calculate
    completed_bets = load_completed_bets()
    stats = calculate_stats(completed_bets)
    
    # Cache the result
    set_cached('bet_stats', stats)
    
    return jsonify(stats)

@app.route('/api/ranked-bets')
def api_ranked_bets():
    """API endpoint: Get ranked bets (Top 10 + rest)"""
    try:
        ranked = load_json_file(f'{WORKSPACE}/ranked_bets.json')
        if ranked:
            return jsonify(ranked)
    except Exception as e:
        print(f"⚠️ Error loading ranked_bets.json: {e}")
    
    # Fallback: return unranked bets
    bets = load_active_bets()
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'performance_stats': {'by_type': {}},
        'top_10': [{'rank': i+1, 'score': 0, 'full_bet': b} for i, b in enumerate(bets[:10])],
        'rest': [{'rank': i+11, 'score': 0, 'full_bet': b} for i, b in enumerate(bets[10:])]
    })

@app.route('/api/previous-results')
def api_previous_results():
    """API endpoint: Get previous betting results"""
    # Check cache first
    cached_results = get_cached('completed_bets')
    if cached_results:
        return jsonify(cached_results)
    
    # Load completed bets
    all_completed = load_completed_bets()
    
    # Add date field if missing
    for bet in all_completed:
        if not bet.get('date'):
            # Try to extract from completed_at timestamp
            if bet.get('completed_at'):
                try:
                    completed_dt = datetime.fromisoformat(
                        bet['completed_at'].replace('Z', '+00:00')
                    )
                    bet['date'] = completed_dt.strftime('%Y-%m-%d')
                except:
                    bet['date'] = datetime.now().strftime('%Y-%m-%d')
            else:
                bet['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Sort by date (most recent first)
    all_completed.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Cache the result
    set_cached('completed_bets', all_completed)
    
    return jsonify(all_completed)

@app.route('/api/health')
def api_health():
    """API endpoint: Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_bets_file': os.path.exists(ACTIVE_BETS_FILE),
        'workspace': WORKSPACE
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🎰 LarlBot Dashboard Server v3.0")
    print("=" * 70)
    print(f"\n📂 Workspace: {WORKSPACE}")
    print(f"🔧 Cache available: {CACHE_AVAILABLE}")
    print(f"🌐 Starting on http://0.0.0.0:5001")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
