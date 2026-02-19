#!/usr/bin/env python3
"""
🔍 System Monitor - Check autonomous system health
Shows status of all components and recent activity
"""

import json
import os
from datetime import datetime, timedelta
import pytz
import subprocess

WORKSPACE = os.environ.get('WORKSPACE', os.getcwd())
EST = pytz.timezone('America/Detroit')

def log(message: str):
    """Print with emoji formatting"""
    print(message)

def check_file_age(filepath: str) -> dict:
    """Check if file exists and when it was last modified"""
    try:
        if not os.path.exists(filepath):
            return {'exists': False, 'age': None, 'status': '❌ Missing'}
        
        mtime = os.path.getmtime(filepath)
        mod_time = datetime.fromtimestamp(mtime, EST)
        age = datetime.now(EST) - mod_time
        
        # Status based on age
        if age < timedelta(minutes=20):
            status = '✅ Fresh'
        elif age < timedelta(hours=2):
            status = '⚠️ Stale'
        else:
            status = '❌ Old'
        
        return {
            'exists': True,
            'age': age,
            'mod_time': mod_time.strftime('%Y-%m-%d %H:%M:%S EST'),
            'status': status
        }
    except Exception as e:
        return {'exists': False, 'age': None, 'status': f'❌ Error: {e}'}

def check_cron_jobs():
    """Check if cron jobs are installed"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            cron_content = result.stdout
            
            jobs = {
                'Daily Picks (7 AM)': '0 7 * * *' in cron_content and 'daily_recommendations.py' in cron_content,
                '15-Min Updates': '0,15,30,45 * * * *' in cron_content and 'auto_update_cycle.py' in cron_content,
                'Git Sync': '5,20,35,50 * * * *' in cron_content and 'production_sync.sh' in cron_content,
                'Learning Engine (6h)': '0 */6 * * *' in cron_content and 'learning_engine.py' in cron_content,
            }
            
            return jobs
        else:
            return None
    except Exception as e:
        return None

def check_git_status():
    """Check git repository status"""
    try:
        os.chdir(WORKSPACE)
        
        # Check for uncommitted changes
        result = subprocess.run(['git', 'status', '-s'], capture_output=True, text=True)
        has_changes = bool(result.stdout.strip())
        
        # Check last commit
        result = subprocess.run(['git', 'log', '-1', '--format=%cr'], capture_output=True, text=True)
        last_commit = result.stdout.strip() if result.returncode == 0 else 'Unknown'
        
        # Check remote status
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        has_remote = 'github.com' in result.stdout
        
        return {
            'has_changes': has_changes,
            'last_commit': last_commit,
            'has_remote': has_remote,
            'status': '✅ Clean' if not has_changes else '⚠️ Uncommitted changes'
        }
    except Exception as e:
        return {'status': f'❌ Error: {e}'}

def read_recent_log(filepath: str, lines: int = 5) -> list:
    """Read last N lines from log file"""
    try:
        if not os.path.exists(filepath):
            return ['Log file not found']
        
        with open(filepath, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) >= lines else all_lines
    except Exception as e:
        return [f'Error reading log: {e}']

def main():
    """Main monitoring function"""
    log("=" * 80)
    log("🔍 LarlBot Autonomous System - Health Monitor")
    log("=" * 80)
    log(f"⏰ Current Time: {datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S EST')}")
    log("")
    
    # Check data files
    log("📊 DATA FILES:")
    files_to_check = {
        'active_bets.json': 'Active Bets',
        'ranked_bets.json': 'Ranked Bets (Top 10)',
        'completed_bets_2026-02-16.json': 'Completed Bets',
        'cache/bet_stats.json': 'Statistics Cache',
    }
    
    for filename, description in files_to_check.items():
        filepath = f"{WORKSPACE}/{filename}"
        info = check_file_age(filepath)
        log(f"   {info['status']} {description:30} {info.get('mod_time', 'N/A')}")
    
    log("")
    
    # Check cron jobs
    log("⏰ CRON JOBS:")
    cron_jobs = check_cron_jobs()
    if cron_jobs:
        for job_name, is_active in cron_jobs.items():
            status = '✅ Active' if is_active else '❌ Missing'
            log(f"   {status} {job_name}")
    else:
        log("   ❌ Could not read crontab")
    
    log("")
    
    # Check git status
    log("🔗 GIT REPOSITORY:")
    git_status = check_git_status()
    log(f"   {git_status['status']}")
    log(f"   📝 Last commit: {git_status.get('last_commit', 'Unknown')}")
    log(f"   🌐 Remote: {'✅ Connected to GitHub' if git_status.get('has_remote') else '❌ No remote'}")
    
    log("")
    
    # Check logs
    log("📝 RECENT ACTIVITY (last 5 lines):")
    logs_to_check = {
        'auto_update.log': 'Auto-Update Cycle',
        'git_sync.log': 'Git Sync',
        'daily_picks.log': 'Daily Picks',
        'learning_engine.log': 'Learning Engine',
    }
    
    for filename, description in logs_to_check.items():
        filepath = f"{WORKSPACE}/{filename}"
        log(f"\n   📄 {description} ({filename}):")
        recent_lines = read_recent_log(filepath, lines=3)
        for line in recent_lines:
            log(f"      {line.rstrip()}")
    
    log("")
    log("=" * 80)
    log("✅ Health Check Complete")
    log("=" * 80)
    log("")
    log("🌐 Dashboards:")
    log("   Local:      http://localhost:5001")
    log("   Production: https://web-production-a39703.up.railway.app/")
    log("")

if __name__ == "__main__":
    main()
