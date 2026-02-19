#!/usr/bin/env python3
"""
Direct crontab installer using subprocess with proper handling
"""
import subprocess
import sys

crontab_content = """# ============================================================================
# 🎰 LarlBot Autonomous Betting System - 4-Hour Push Schedule
# ============================================================================
# Local updates every 15 min, GitHub pushes every 4 hours

# 1. DAILY PICKS GENERATOR - 7:00 AM EST
# Generates fresh betting recommendations with ML and adaptive learning
0 7 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/daily_recommendations.py > /Users/macmini/.openclaw/workspace/daily_picks.log 2>&1

# 2. INITIALIZE DAILY BETS - 7:05 AM EST
# Sets up active_bets.json and ranked_bets.json for the day
5 7 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/initialize_daily_bets.py >> /Users/macmini/.openclaw/workspace/daily_picks.log 2>&1

# ============================================================================
# 15-MINUTE LOCAL UPDATE CYCLE (Keeps dashboard fresh, NO GitHub push)
# ============================================================================
# Runs: :00, :15, :30, :45 every hour
# Checks games, updates stats, refreshes local dashboard
0,15,30,45 * * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/auto_update_cycle.py >> /Users/macmini/.openclaw/workspace/auto_update.log 2>&1

# ============================================================================
# INTERNAL SYNC - 30 min BEFORE each GitHub push (Every 4 hours)
# ============================================================================
# Runs at: 6:30 AM, 10:30 AM, 2:30 PM, 6:30 PM, 10:30 PM EST
# Full comprehensive sync: scores, results, stats, consistency check
30 6,10,14,18,22 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/full_internal_sync.py >> /Users/macmini/.openclaw/workspace/internal_sync.log 2>&1

# ============================================================================
# GITHUB PUSH - Every 4 hours (5x per day)
# ============================================================================
# Runs at: 7:00 AM, 11:00 AM, 3:00 PM, 7:00 PM, 11:00 PM EST
# Commits and pushes to GitHub → Railway auto-deploys
0 7,11,15,19,23 * * * cd /Users/macmini/.openclaw/workspace && /bin/bash /Users/macmini/.openclaw/workspace/scheduled_git_push.sh >> /Users/macmini/.openclaw/workspace/git_sync.log 2>&1

# ============================================================================
# LEARNING ENGINE - Every 6 hours
# ============================================================================
# Analyzes completed bets and updates ML insights
0 */6 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/learning_engine.py >> /Users/macmini/.openclaw/workspace/learning_engine.log 2>&1

# ============================================================================
# MAINTENANCE JOBS
# ============================================================================

# NIGHTLY CLEANUP - 2:00 AM EST
# Archives old logs and cleans up cache
0 2 * * * cd /Users/macmini/.openclaw/workspace && find . -name "*.log" -mtime +7 -delete

# WEEKLY VERIFICATION - Sunday 10:00 PM EST
# Full database verification and consistency check
0 22 * * 0 cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/bet_processor.py verify >> /Users/macmini/.openclaw/workspace/bet_verification.log 2>&1
"""

try:
    print("Installing new crontab...")
    process = subprocess.run(
        ['crontab', '-'],
        input=crontab_content.encode('utf-8'),
        timeout=5,
        capture_output=True
    )
    
    if process.returncode == 0:
        print("✅ Crontab installed successfully!")
        sys.exit(0)
    else:
        print(f"❌ Error installing crontab:")
        print(process.stderr.decode('utf-8'))
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("⏱️  Crontab command timed out (macOS permission issue?)")
    print("")
    print("MANUAL INSTALLATION REQUIRED:")
    print("1. Run: crontab -e")
    print("2. Replace all content with the configuration shown in setup_4hour_cron.sh")
    print("3. Save and exit")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
