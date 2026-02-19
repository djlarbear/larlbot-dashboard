#!/usr/bin/env python3
"""
✅ Verify 4-Hour Schedule Configuration
Checks that all components are properly configured
"""

import os
import subprocess
import json
from datetime import datetime, timedelta
import pytz

WORKSPACE = os.environ.get('WORKSPACE', os.getcwd())
EST = pytz.timezone('America/Detroit')

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_executable(filepath: str, description: str) -> bool:
    """Check if a file is executable"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: {filepath} (not found)")
        return False
    
    is_exec = os.access(filepath, os.X_OK)
    status = "✅" if is_exec else "❌"
    print(f"{status} {description}: {filepath}")
    return is_exec

def check_cron_schedule() -> bool:
    """Verify cron schedule is correct"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        cron_content = result.stdout
        
        required_jobs = [
            ('daily_recommendations.py', 'Daily picks generator'),
            ('auto_update_cycle.py', '15-min local update'),
            ('full_internal_sync.py', 'Internal sync (every 4h)'),
            ('scheduled_git_push.sh', 'GitHub push (every 4h)'),
            ('learning_engine.py', 'Learning engine'),
        ]
        
        print("\n📋 Cron Job Verification:")
        all_found = True
        
        for script, description in required_jobs:
            if script in cron_content:
                print(f"✅ {description}: {script}")
            else:
                print(f"❌ {description}: {script} (NOT FOUND)")
                all_found = False
        
        # Check specific times
        print("\n🕐 GitHub Push Schedule Verification:")
        push_times = ['7', '11', '15', '19', '23']
        
        for hour in push_times:
            # Look for scheduled_git_push.sh at this hour
            if f'0 {hour},' in cron_content or f' {hour} ' in cron_content:
                hour_12 = int(hour) if int(hour) <= 12 else int(hour) - 12
                am_pm = 'AM' if int(hour) < 12 else 'PM'
                print(f"✅ {hour_12}:00 {am_pm} push scheduled")
            else:
                print(f"❌ {hour}:00 push NOT scheduled")
                all_found = False
        
        # Check internal sync times (30 min before)
        print("\n🔄 Internal Sync Schedule Verification:")
        sync_hours = ['6', '10', '14', '18', '22']
        
        for hour in sync_hours:
            if f'30 {hour}' in cron_content or f'30 {hour.zfill(2)}' in cron_content:
                hour_12 = int(hour) if int(hour) <= 12 else int(hour) - 12
                am_pm = 'AM' if int(hour) < 12 else 'PM'
                print(f"✅ {hour_12}:30 {am_pm} internal sync scheduled")
            else:
                print(f"❌ {hour}:30 internal sync NOT scheduled")
                all_found = False
        
        return all_found
    
    except Exception as e:
        print(f"❌ Error checking cron: {e}")
        return False

def check_log_files() -> bool:
    """Check that log files exist or can be created"""
    log_files = [
        (f"{WORKSPACE}/auto_update.log", "Auto update log"),
        (f"{WORKSPACE}/internal_sync.log", "Internal sync log"),
        (f"{WORKSPACE}/git_sync.log", "Git sync log"),
    ]
    
    print("\n📁 Log Files:")
    all_ok = True
    
    for filepath, description in log_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {description}: {filepath} ({size} bytes)")
        else:
            # Check if we can create it
            try:
                with open(filepath, 'a') as f:
                    pass
                print(f"✅ {description}: {filepath} (created)")
            except:
                print(f"❌ {description}: {filepath} (cannot create)")
                all_ok = False
    
    return all_ok

def check_data_files() -> bool:
    """Check that required data files exist"""
    data_files = [
        (f"{WORKSPACE}/active_bets.json", "Active bets"),
        (f"{WORKSPACE}/ranked_bets.json", "Ranked bets"),
    ]
    
    print("\n📊 Data Files:")
    all_ok = True
    
    for filepath, description in data_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                print(f"✅ {description}: {filepath} (valid JSON)")
            except:
                print(f"⚠️ {description}: {filepath} (INVALID JSON)")
                all_ok = False
        else:
            print(f"⚠️ {description}: {filepath} (not found - will be created)")
    
    return all_ok

def predict_next_events():
    """Predict next scheduled events"""
    now = datetime.now(EST)
    
    # Find next local update (every 15 min)
    next_update_min = ((now.minute // 15) + 1) * 15
    if next_update_min >= 60:
        next_update = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0)
    else:
        next_update = now.replace(minute=next_update_min, second=0)
    
    # Find next internal sync (at :30 on hours 6, 10, 14, 18, 22)
    sync_hours = [6, 10, 14, 18, 22]
    next_sync = None
    for hour in sync_hours:
        candidate = now.replace(hour=hour, minute=30, second=0)
        if candidate > now:
            next_sync = candidate
            break
    
    if not next_sync:
        # Next day's first sync
        next_sync = (now + timedelta(days=1)).replace(hour=6, minute=30, second=0)
    
    # Find next GitHub push (at :00 on hours 7, 11, 15, 19, 23)
    push_hours = [7, 11, 15, 19, 23]
    next_push = None
    for hour in push_hours:
        candidate = now.replace(hour=hour, minute=0, second=0)
        if candidate > now:
            next_push = candidate
            break
    
    if not next_push:
        # Next day's first push
        next_push = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0)
    
    print("\n📅 Next Scheduled Events:")
    print(f"   🔄 Local update: {next_update.strftime('%I:%M %p')} ({(next_update - now).seconds // 60} min)")
    print(f"   🔧 Internal sync: {next_sync.strftime('%I:%M %p')} ({(next_sync - now).seconds // 60} min)")
    print(f"   🚀 GitHub push: {next_push.strftime('%I:%M %p')} ({(next_push - now).seconds // 60} min)")

def main():
    """Main verification"""
    print("=" * 80)
    print("✅ 4-Hour Schedule Verification")
    print("=" * 80)
    print(f"⏰ Current Time: {datetime.now(EST).strftime('%Y-%m-%d %I:%M:%S %p EST')}")
    print(f"📁 Workspace: {WORKSPACE}")
    print("")
    
    # Check files
    print("📂 Required Files:")
    files_ok = True
    files_ok &= check_file_exists(f"{WORKSPACE}/auto_update_cycle.py", "Auto update script")
    files_ok &= check_file_exists(f"{WORKSPACE}/game_status_checker.py", "Game status checker")
    files_ok &= check_file_exists(f"{WORKSPACE}/full_internal_sync.py", "Full internal sync")
    files_ok &= check_file_exists(f"{WORKSPACE}/production_sync.sh", "Production sync")
    files_ok &= check_file_exists(f"{WORKSPACE}/scheduled_git_push.sh", "Scheduled git push")
    
    print("")
    
    # Check executables
    print("🔧 Executable Permissions:")
    exec_ok = True
    exec_ok &= check_executable(f"{WORKSPACE}/full_internal_sync.py", "Full internal sync")
    exec_ok &= check_executable(f"{WORKSPACE}/scheduled_git_push.sh", "Scheduled git push")
    exec_ok &= check_executable(f"{WORKSPACE}/production_sync.sh", "Production sync")
    
    # Check cron
    cron_ok = check_cron_schedule()
    
    # Check logs
    logs_ok = check_log_files()
    
    # Check data
    data_ok = check_data_files()
    
    # Predict next events
    predict_next_events()
    
    # Summary
    print("")
    print("=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_checks = [
        (files_ok, "Required files"),
        (exec_ok, "Executable permissions"),
        (cron_ok, "Cron schedule"),
        (logs_ok, "Log files"),
        (data_ok, "Data files"),
    ]
    
    for status, check_name in all_checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")
    
    print("")
    
    if all(status for status, _ in all_checks):
        print("🎉 ALL CHECKS PASSED - System ready for 4-hour schedule!")
        print("")
        print("📋 Schedule Summary:")
        print("   • Local updates: Every 15 minutes (96x/day)")
        print("   • Internal sync: 5x/day at 6:30, 10:30, 14:30, 18:30, 22:30")
        print("   • GitHub push: 5x/day at 7:00, 11:00, 15:00, 19:00, 23:00")
        print("   • Railway deploys: 5x/day (down from 96x/day)")
        print("")
        return 0
    else:
        print("⚠️ SOME CHECKS FAILED - Review issues above")
        print("")
        print("To fix:")
        print("   1. Run: ./setup_4hour_cron.sh")
        print("   2. Ensure all scripts are executable: chmod +x *.py *.sh")
        print("   3. Re-run this verification")
        print("")
        return 1

if __name__ == "__main__":
    exit(main())
