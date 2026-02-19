#!/usr/bin/env python3
"""
🔄 Auto-Update Cycle - 15-Minute Refresh System
Runs every 15 minutes to keep dashboard fresh

TASKS:
1. Check all active games for status (started/in-progress/finished)
2. Move finished games to Previous Results
3. Update win/loss records
4. Recalculate stats (Win Rate, Record)
5. Update active_bets.json
6. Update ranked_bets.json
7. Update completed_bets file
8. Trigger dashboard refresh
"""

import json
import os
import sys
import subprocess
from datetime import datetime
import pytz

# Configuration
WORKSPACE = os.environ.get('WORKSPACE', os.getcwd())
sys.path.insert(0, WORKSPACE)

# Timezone
EST = pytz.timezone('America/Detroit')

# Files
ACTIVE_BETS_FILE = f"{WORKSPACE}/active_bets.json"
RANKED_BETS_FILE = f"{WORKSPACE}/ranked_bets.json"
COMPLETED_BETS_FILE = f"{WORKSPACE}/completed_bets_2026-02-16.json"
UPDATE_LOG_FILE = f"{WORKSPACE}/auto_update.log"

def log(message: str):
    """Log with timestamp to console and file"""
    timestamp = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST")
    log_message = f"[{timestamp}] {message}"
    
    print(log_message)
    
    # Also write to log file
    try:
        with open(UPDATE_LOG_FILE, 'a') as f:
            f.write(log_message + '\n')
    except:
        pass

def run_script(script_path: str, description: str) -> bool:
    """Run a Python script and return success status"""
    try:
        log(f"▶️  Running: {description}")
        
        result = subprocess.run(
            ['python3', script_path],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=300  # 5-minute timeout
        )
        
        if result.returncode == 0:
            log(f"✅ {description} - SUCCESS")
            if result.stdout:
                log(f"   Output: {result.stdout[:500]}")  # First 500 chars
            return True
        else:
            log(f"❌ {description} - FAILED")
            if result.stderr:
                log(f"   Error: {result.stderr[:500]}")
            return False
    
    except subprocess.TimeoutExpired:
        log(f"⏱️ {description} - TIMEOUT (>5 min)")
        return False
    
    except Exception as e:
        log(f"❌ {description} - ERROR: {e}")
        return False

def load_json_file(filepath: str):
    """Load JSON file safely"""
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        log(f"⚠️ Error loading {filepath}: {e}")
        return None

def save_json_file(filepath: str, data: dict):
    """Save JSON file safely"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        log(f"⚠️ Error saving {filepath}: {e}")
        return False

def recalculate_stats():
    """Recalculate win/loss stats from completed bets"""
    try:
        log("📊 Recalculating stats...")
        
        completed_data = load_json_file(COMPLETED_BETS_FILE)
        if not completed_data:
            log("   ⚠️ No completed bets file found")
            return {'wins': 0, 'losses': 0, 'win_rate': 0, 'record': '0-0'}
        
        bets = completed_data.get('bets', [])
        wins = sum(1 for b in bets if b.get('result') == 'WIN')
        losses = sum(1 for b in bets if b.get('result') == 'LOSS')
        total = wins + losses
        
        win_rate = int((wins / total * 100)) if total > 0 else 0
        
        stats = {
            'wins': wins,
            'losses': losses,
            'total': total,
            'win_rate': win_rate,
            'record': f"{wins}-{losses}",
            'last_updated': datetime.now(EST).isoformat()
        }
        
        log(f"   ✅ Stats: {stats['record']} ({win_rate}% win rate)")
        
        # Save to cache
        cache_dir = f"{WORKSPACE}/cache"
        os.makedirs(cache_dir, exist_ok=True)
        save_json_file(f"{cache_dir}/bet_stats.json", stats)
        
        return stats
    
    except Exception as e:
        log(f"❌ Stats calculation failed: {e}")
        return None

def update_timestamps():
    """Update last_updated timestamps in all data files"""
    try:
        timestamp = datetime.now(EST).isoformat()
        
        for filepath in [ACTIVE_BETS_FILE, RANKED_BETS_FILE, COMPLETED_BETS_FILE]:
            if os.path.exists(filepath):
                data = load_json_file(filepath)
                if data:
                    data['last_updated'] = timestamp
                    save_json_file(filepath, data)
        
        log(f"✅ Updated timestamps to {timestamp}")
        return True
    
    except Exception as e:
        log(f"⚠️ Timestamp update failed: {e}")
        return False

def main():
    """Main update cycle"""
    log("=" * 70)
    log("🔄 AUTO-UPDATE CYCLE - 15-MINUTE REFRESH")
    log("=" * 70)
    
    start_time = datetime.now(EST)
    
    success_count = 0
    total_tasks = 3
    
    # Task 1: Check game statuses and move finished games
    if run_script(f"{WORKSPACE}/game_status_checker.py", "Game Status Checker"):
        success_count += 1
    
    # Task 2: Recalculate stats
    if recalculate_stats():
        success_count += 1
    
    # Task 3: Update timestamps for dashboard refresh
    if update_timestamps():
        success_count += 1
    
    # Calculate duration
    end_time = datetime.now(EST)
    duration = (end_time - start_time).total_seconds()
    
    log("=" * 70)
    log(f"✅ UPDATE CYCLE COMPLETE")
    log(f"   Success Rate: {success_count}/{total_tasks} tasks")
    log(f"   Duration: {duration:.1f} seconds")
    log(f"   Next Update: +15 minutes")
    log("=" * 70)
    
    # Exit with error code if any tasks failed
    if success_count < total_tasks:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
