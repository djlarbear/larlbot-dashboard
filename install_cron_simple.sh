#!/bin/bash
# Simple Cron Installation Script
# Installs 4-hour schedule crontab directly

echo "Installing 4-hour schedule crontab..."

# Install the crontab
cat > /tmp/larlbot_4hour_cron.txt << 'CRONEOF'
# ============================================================================
# 🎰 LarlBot Autonomous Betting System - 4-Hour Push Schedule
# ============================================================================
# Local updates every 15 min, GitHub pushes every 4 hours

# 1. DAILY PICKS GENERATOR - 7:00 AM EST
0 7 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/daily_recommendations.py > /Users/macmini/.openclaw/workspace/daily_picks.log 2>&1

# 2. INITIALIZE DAILY BETS - 7:05 AM EST
5 7 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/initialize_daily_bets.py >> /Users/macmini/.openclaw/workspace/daily_picks.log 2>&1

# ============================================================================
# 15-MINUTE LOCAL UPDATE CYCLE (Keeps dashboard fresh, NO GitHub push)
# ============================================================================
0,15,30,45 * * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/auto_update_cycle.py >> /Users/macmini/.openclaw/workspace/auto_update.log 2>&1

# ============================================================================
# INTERNAL SYNC - 30 min BEFORE each GitHub push (Every 4 hours)
# ============================================================================
30 6,10,14,18,22 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/full_internal_sync.py >> /Users/macmini/.openclaw/workspace/internal_sync.log 2>&1

# ============================================================================
# GITHUB PUSH - Every 4 hours (5x per day)
# ============================================================================
0 7,11,15,19,23 * * * cd /Users/macmini/.openclaw/workspace && /bin/bash /Users/macmini/.openclaw/workspace/scheduled_git_push.sh >> /Users/macmini/.openclaw/workspace/git_sync.log 2>&1

# ============================================================================
# LEARNING ENGINE - Every 6 hours
# ============================================================================
0 */6 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/learning_engine.py >> /Users/macmini/.openclaw/workspace/learning_engine.log 2>&1

# ============================================================================
# MAINTENANCE JOBS
# ============================================================================

# NIGHTLY CLEANUP - 2:00 AM EST
0 2 * * * cd /Users/macmini/.openclaw/workspace && find . -name "*.log" -mtime +7 -delete

# WEEKLY VERIFICATION - Sunday 10:00 PM EST
0 22 * * 0 cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/bet_processor.py verify >> /Users/macmini/.openclaw/workspace/bet_verification.log 2>&1
CRONEOF

# Install it (will prompt for confirmation on macOS)
crontab < /tmp/larlbot_4hour_cron.txt

# Verify
echo ""
echo "✅ Crontab installed! Verifying..."
echo ""

if crontab -l | grep -q "full_internal_sync"; then
    echo "✅ Internal sync job found"
else
    echo "❌ Internal sync job NOT found"
fi

if crontab -l | grep -q "scheduled_git_push"; then
    echo "✅ GitHub push job found"
else
    echo "❌ GitHub push job NOT found"
fi

echo ""
echo "Run 'crontab -l' to view full schedule"
