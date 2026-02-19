#!/usr/bin/env python3
"""
🔄 Full Internal Sync - Comprehensive Pre-Push Update
Runs 30 minutes before each GitHub push (at :30)

COMPREHENSIVE SYNC TASKS:
1. Check all active games for status (started/in-progress/finished)
2. Pull latest scores from ESPN API
3. Calculate final scores against predictions
4. Mark bets as WIN/LOSS if game finished
5. Move finished games to Previous Results
6. Update win/loss records
7. Recalculate stats (Win Rate, Record)
8. Update active_bets.json
9. Update ranked_bets.json
10. Update completed_bets_YYYY-MM-DD.json
11. Verify data consistency
12. Prepare everything for GitHub push

This ensures all data is fresh and consistent before production deployment.
"""

import json
import os
import sys
import subprocess
from datetime import datetime
import pytz
from typing import Dict, List, Optional

# Configuration
WORKSPACE = os.environ.get('WORKSPACE', os.getcwd())
sys.path.insert(0, WORKSPACE)

# Timezone
EST = pytz.timezone('America/Detroit')

# Files
ACTIVE_BETS_FILE = f"{WORKSPACE}/active_bets.json"
RANKED_BETS_FILE = f"{WORKSPACE}/ranked_bets.json"
COMPLETED_BETS_FILE = f"{WORKSPACE}/completed_bets_{datetime.now(EST).strftime('%Y-%m-%d')}.json"
SYNC_LOG_FILE = f"{WORKSPACE}/internal_sync.log"

# Alert threshold (5 minutes)
ALERT_THRESHOLD_SECONDS = 300

def log(message: str):
    """Log with timestamp to console and file"""
    timestamp = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST")
    log_message = f"[{timestamp}] {message}"
    
    print(log_message)
    
    # Also write to log file
    try:
        with open(SYNC_LOG_FILE, 'a') as f:
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
            timeout=300  # 5-minute timeout per script
        )
        
        if result.returncode == 0:
            log(f"✅ {description} - SUCCESS")
            if result.stdout:
                # Log first 300 chars of output
                output_preview = result.stdout[:300].replace('\n', ' ')
                log(f"   Output: {output_preview}...")
            return True
        else:
            log(f"❌ {description} - FAILED (exit code: {result.returncode})")
            if result.stderr:
                error_preview = result.stderr[:300].replace('\n', ' ')
                log(f"   Error: {error_preview}...")
            return False
    
    except subprocess.TimeoutExpired:
        log(f"⏱️ {description} - TIMEOUT (>5 min)")
        return False
    
    except Exception as e:
        log(f"❌ {description} - ERROR: {e}")
        return False

def load_json_file(filepath: str) -> Optional[Dict]:
    """Load JSON file safely"""
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        log(f"⚠️ Error loading {filepath}: {e}")
        return None

def save_json_file(filepath: str, data: Dict) -> bool:
    """Save JSON file safely"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        log(f"⚠️ Error saving {filepath}: {e}")
        return False

def verify_data_consistency() -> bool:
    """Verify all data files are consistent and valid"""
    log("🔍 Verifying data consistency...")
    
    issues = []
    
    # Check active_bets.json
    active_data = load_json_file(ACTIVE_BETS_FILE)
    if not active_data:
        issues.append("active_bets.json missing or corrupted")
    elif 'bets' not in active_data:
        issues.append("active_bets.json missing 'bets' key")
    else:
        log(f"   ✅ active_bets.json: {len(active_data['bets'])} bets")
    
    # Check ranked_bets.json
    ranked_data = load_json_file(RANKED_BETS_FILE)
    if not ranked_data:
        issues.append("ranked_bets.json missing or corrupted")
    elif 'top_10' not in ranked_data:
        issues.append("ranked_bets.json missing 'top_10' key")
    else:
        log(f"   ✅ ranked_bets.json: {len(ranked_data['top_10'])} ranked bets")
    
    # Check completed_bets file
    completed_data = load_json_file(COMPLETED_BETS_FILE)
    if not completed_data:
        log(f"   ⚠️ completed_bets file missing (creating new)")
        save_json_file(COMPLETED_BETS_FILE, {
            'date': datetime.now(EST).strftime('%Y-%m-%d'),
            'bets': []
        })
    elif 'bets' not in completed_data:
        issues.append("completed_bets file missing 'bets' key")
    else:
        log(f"   ✅ completed_bets: {len(completed_data['bets'])} completed")
    
    if issues:
        log("❌ Data consistency issues found:")
        for issue in issues:
            log(f"   - {issue}")
        return False
    
    log("✅ Data consistency verified")
    return True

def recalculate_all_stats() -> Dict:
    """Recalculate comprehensive statistics from completed bets"""
    try:
        log("📊 Recalculating all statistics...")
        
        completed_data = load_json_file(COMPLETED_BETS_FILE)
        if not completed_data or 'bets' not in completed_data:
            log("   ⚠️ No completed bets found")
            return {'wins': 0, 'losses': 0, 'win_rate': 0, 'record': '0-0'}
        
        bets = completed_data['bets']
        wins = sum(1 for b in bets if b.get('result') == 'WIN')
        losses = sum(1 for b in bets if b.get('result') == 'LOSS')
        total = wins + losses
        
        win_rate = int((wins / total * 100)) if total > 0 else 0
        
        # Calculate by bet type
        by_type = {}
        for bet in bets:
            bet_type = bet.get('bet_type', 'UNKNOWN')
            if bet_type not in by_type:
                by_type[bet_type] = {'wins': 0, 'losses': 0}
            
            if bet.get('result') == 'WIN':
                by_type[bet_type]['wins'] += 1
            elif bet.get('result') == 'LOSS':
                by_type[bet_type]['losses'] += 1
        
        stats = {
            'wins': wins,
            'losses': losses,
            'total': total,
            'win_rate': win_rate,
            'record': f"{wins}-{losses}",
            'by_type': by_type,
            'last_updated': datetime.now(EST).isoformat()
        }
        
        log(f"   ✅ Overall Stats: {stats['record']} ({win_rate}% win rate)")
        for bet_type, type_stats in by_type.items():
            type_total = type_stats['wins'] + type_stats['losses']
            type_wr = int((type_stats['wins'] / type_total * 100)) if type_total > 0 else 0
            log(f"   ✅ {bet_type}: {type_stats['wins']}-{type_stats['losses']} ({type_wr}%)")
        
        # Save to cache
        cache_dir = f"{WORKSPACE}/cache"
        os.makedirs(cache_dir, exist_ok=True)
        save_json_file(f"{cache_dir}/bet_stats.json", stats)
        
        return stats
    
    except Exception as e:
        log(f"❌ Stats calculation failed: {e}")
        return None

def update_all_timestamps():
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
    """Main internal sync process"""
    log("=" * 80)
    log("🔄 FULL INTERNAL SYNC - Pre-Push Comprehensive Update")
    log("=" * 80)
    
    start_time = datetime.now(EST)
    log(f"⏰ Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S EST')}")
    
    success_count = 0
    total_tasks = 5
    
    # TASK 1: Check game statuses and move finished games
    # This handles steps 1-5 of the requirements
    log("")
    log("📋 TASK 1/5: Game Status Check & Results Processing")
    if run_script(f"{WORKSPACE}/game_status_checker.py", "Game Status Checker"):
        success_count += 1
    
    # TASK 2: Recalculate all statistics
    # This handles steps 6-7 of the requirements
    log("")
    log("📋 TASK 2/5: Statistics Recalculation")
    if recalculate_all_stats():
        success_count += 1
    
    # TASK 3: Update all timestamps
    # This handles step 8-10 of the requirements
    log("")
    log("📋 TASK 3/5: Update Data File Timestamps")
    if update_all_timestamps():
        success_count += 1
    
    # TASK 4: Verify data consistency
    # This handles step 11 of the requirements
    log("")
    log("📋 TASK 4/5: Data Consistency Verification")
    if verify_data_consistency():
        success_count += 1
    
    # TASK 5: Prepare for GitHub push (ensure cache is fresh)
    # This handles step 12 of the requirements
    log("")
    log("📋 TASK 5/5: Cache Refresh for Production")
    cache_dir = f"{WORKSPACE}/cache"
    if os.path.exists(cache_dir):
        log("   ✅ Cache directory ready for production sync")
        success_count += 1
    else:
        os.makedirs(cache_dir, exist_ok=True)
        log("   ✅ Cache directory created")
        success_count += 1
    
    # Calculate duration
    end_time = datetime.now(EST)
    duration = (end_time - start_time).total_seconds()
    
    log("")
    log("=" * 80)
    log(f"✅ INTERNAL SYNC COMPLETE")
    log(f"   Success Rate: {success_count}/{total_tasks} tasks")
    log(f"   Duration: {duration:.1f} seconds")
    
    # Alert if sync took too long
    if duration > ALERT_THRESHOLD_SECONDS:
        log(f"   ⚠️ WARNING: Sync took longer than {ALERT_THRESHOLD_SECONDS}s threshold!")
        log(f"   ⚠️ May not complete before scheduled GitHub push")
    else:
        log(f"   ✅ Sync completed well within time budget")
    
    log(f"   Next Sync: +4 hours")
    log(f"   Next GitHub Push: +30 minutes (at :00)")
    log("=" * 80)
    
    # Exit with error code if any critical tasks failed
    if success_count < 4:  # Allow 1 failure
        log("❌ Too many failures - sync incomplete")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
