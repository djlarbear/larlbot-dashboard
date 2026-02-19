#!/usr/bin/env python3
"""
🎰 LarlBot Dashboard Server FINAL
Production-ready with comprehensive cache-busting
"""

from flask import Flask, render_template, jsonify, request, make_response
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import sys
import glob

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

app = Flask(__name__, template_folder='templates', static_folder='static')

# ============================================================================
# CACHE BUSTING - Critical for preventing stale data
# ============================================================================

def add_cache_busting_headers(response):
    """Add cache-busting headers to EVERY response"""
    # CRITICAL: Tell browsers NOT to cache API responses
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    
    # Add unique identifiers so browser knows content changed
    import time
    response.headers['X-Cache-Buster'] = str(int(time.time() * 1000))
    response.headers['X-Generated-At'] = datetime.now().isoformat()
    
    return response

@app.after_request
def apply_cache_headers(response):
    """Apply cache-busting to all responses"""
    return add_cache_busting_headers(response)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_json_file(filepath: str) -> Optional[Dict]:
    """Safely load a JSON file"""
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return None

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_active_bets() -> List[Dict]:
    """Load active (non-finished) bets for today's dashboard"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        active_data = load_json_file(ACTIVE_BETS_FILE)
        
        if not active_data:
            return []
        
        if active_data.get('date') != today:
            return []
        
        bets = active_data.get('bets', [])
        active_bets = [b for b in bets if b.get('result') not in ['WIN', 'LOSS']]
        
        print(f"✅ Loaded {len(active_bets)} active bets for {today}")
        return active_bets
    except Exception as e:
        print(f"❌ Error loading active bets: {e}")
        return []

def load_completed_bets() -> List[Dict]:
    """Load all completed bets with WIN/LOSS results"""
    all_completed = []
    
    # Load from bet_tracker_input.json
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
    """Calculate statistics from completed bets"""
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
    """API endpoint: Get active bets"""
    bets = load_active_bets()
    response = make_response(jsonify(bets))
    return add_cache_busting_headers(response)

@app.route('/api/stats')
def api_stats():
    """API endpoint: Get betting statistics"""
    completed_bets = load_completed_bets()
    stats = calculate_stats(completed_bets)
    response = make_response(jsonify(stats))
    return add_cache_busting_headers(response)

@app.route('/api/ranked-bets')
def api_ranked_bets():
    """API endpoint: Get ranked bets"""
    try:
        ranked = load_json_file(f'{WORKSPACE}/ranked_bets.json')
        if ranked:
            response = make_response(jsonify(ranked))
            return add_cache_busting_headers(response)
    except:
        pass
    
    # Fallback
    bets = load_active_bets()
    response = make_response(jsonify({
        'timestamp': datetime.now().isoformat(),
        'performance_stats': {'by_type': {}},
        'top_10': [{'rank': i+1, 'score': 0, 'full_bet': b} for i, b in enumerate(bets[:10])],
        'rest': [{'rank': i+11, 'score': 0, 'full_bet': b} for i, b in enumerate(bets[10:])]
    }))
    return add_cache_busting_headers(response)

@app.route('/api/previous-results')
def api_previous_results():
    """API endpoint: Get previous betting results"""
    # Load completed bets (NO caching)
    all_completed = load_completed_bets()
    
    # Add date field if missing
    for bet in all_completed:
        if not bet.get('date'):
            if bet.get('completed_at'):
                try:
                    completed_dt = datetime.fromisoformat(bet['completed_at'].replace('Z', '+00:00'))
                    bet['date'] = completed_dt.strftime('%Y-%m-%d')
                except:
                    bet['date'] = datetime.now().strftime('%Y-%m-%d')
            else:
                bet['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Sort by date (most recent first)
    all_completed.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Return with cache-busting headers
    response = make_response(jsonify(all_completed))
    return add_cache_busting_headers(response)

@app.route('/api/health')
def api_health():
    """API endpoint: Health check"""
    response = make_response(jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_bets_file': os.path.exists(ACTIVE_BETS_FILE),
        'workspace': WORKSPACE
    }))
    return add_cache_busting_headers(response)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    response = make_response(jsonify({'error': 'Not found'}), 404)
    return add_cache_busting_headers(response)

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    response = make_response(jsonify({'error': 'Internal server error'}), 500)
    return add_cache_busting_headers(response)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🎰 LarlBot Dashboard Server FINAL")
    print("=" * 70)
    print(f"\n📂 Workspace: {WORKSPACE}")
    print(f"🔧 Cache available: {CACHE_AVAILABLE}")
    print(f"🌐 Starting on http://0.0.0.0:5001")
    print(f"🚫 Cache-Busting: ENABLED (all API responses)")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
