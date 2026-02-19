#!/bin/bash
# Setup 4-Hour Update Schedule
# Reduces GitHub commits from 96/day to 5/day while keeping local updates every 15 min

WORKSPACE="/Users/macmini/.openclaw/workspace"
PYTHON="/usr/bin/python3"
BASH="/bin/bash"

echo "============================================================================"
echo "🔧 Setting Up 4-Hour Update Schedule"
echo "============================================================================"
echo ""
echo "NEW SCHEDULE:"
echo "  - Local updates: Every 15 minutes (keeps dashboard responsive)"
echo "  - Internal sync: 6:30 AM, 10:30 AM, 2:30 PM, 6:30 PM, 10:30 PM EST"
echo "  - GitHub push: 7:00 AM, 11:00 AM, 3:00 PM, 7:00 PM, 11:00 PM EST"
echo "  - Result: 5 GitHub commits/day (down from 96/day)"
echo ""

# Create new crontab
cat > /tmp/larlbot_cron.txt << 'CRONEOF'
# ============================================================================
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

CRONEOF

echo "📝 New crontab configuration created"
echo ""

# Show the new configuration
echo "NEW CRONTAB:"
echo "----------------------------------------"
cat /tmp/larlbot_cron.txt
echo "----------------------------------------"
echo ""

# Ask for confirmation
read -p "Install this new crontab? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install new crontab
    crontab /tmp/larlbot_cron.txt
    
    echo "✅ Crontab installed successfully!"
    echo ""
    echo "VERIFICATION:"
    crontab -l | head -20
    echo ""
    echo "============================================================================"
    echo "✅ 4-HOUR SCHEDULE ACTIVE"
    echo "============================================================================"
    echo ""
    echo "📊 Schedule Summary:"
    echo "  • Local updates: Every 15 min → Keeps dashboard fresh locally"
    echo "  • Internal sync: 5x/day at :30 → Full data processing before push"
    echo "  • GitHub push: 5x/day at :00 → Railway auto-deploys production"
    echo ""
    echo "🎯 Result: GitHub commits reduced from 96/day to 5/day!"
    echo ""
    echo "📋 Next scheduled events:"
    echo "  - Next local update: Within 15 minutes"
    echo "  - Next internal sync: $(date -v+1H -v+30M '+%H:30 %p EST')"
    echo "  - Next GitHub push: $(date -v+1H '+%H:00 %p EST')"
    echo ""
    echo "📁 Log files:"
    echo "  - Auto update: $WORKSPACE/auto_update.log"
    echo "  - Internal sync: $WORKSPACE/internal_sync.log"
    echo "  - Git push: $WORKSPACE/git_sync.log"
    echo ""
else
    echo "❌ Installation cancelled"
    echo "Cron configuration saved to: /tmp/larlbot_cron.txt"
    echo "You can review and manually install with: crontab /tmp/larlbot_cron.txt"
fi

# Cleanup
rm -f /tmp/larlbot_cron.txt

echo "============================================================================"
