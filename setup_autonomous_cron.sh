#!/bin/bash
# Setup Autonomous Betting System - Cron Jobs
# Configures fully automated 15-minute refresh cycle

echo "======================================================================"
echo "🤖 Setting Up Autonomous Betting System"
echo "======================================================================"

WORKSPACE="/Users/macmini/.openclaw/workspace"

# Create new crontab
cat > /tmp/larlbot_cron.txt << 'EOF'
# ============================================================================
# 🎰 LarlBot Autonomous Betting System - Full Automation
# ============================================================================

# 1. DAILY PICKS GENERATOR - 7:00 AM EST
# Generates fresh betting recommendations with ML and adaptive learning
0 7 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/daily_recommendations.py > /Users/macmini/.openclaw/workspace/daily_picks.log 2>&1

# 2. INITIALIZE DAILY BETS - 7:05 AM EST
# Sets up active_bets.json and ranked_bets.json for the day
5 7 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/initialize_daily_bets.py >> /Users/macmini/.openclaw/workspace/daily_picks.log 2>&1

# 3. 15-MINUTE UPDATE CYCLE - Every 15 minutes (96x/day)
# Checks game statuses, moves finished games, updates stats, refreshes dashboard
0,15,30,45 * * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/auto_update_cycle.py >> /Users/macmini/.openclaw/workspace/auto_update.log 2>&1

# 4. PRODUCTION SYNC - Every 15 minutes (after update cycle)
# Auto-commits and pushes to GitHub, triggering Railway deployment
5,20,35,50 * * * * cd /Users/macmini/.openclaw/workspace && /bin/bash /Users/macmini/.openclaw/workspace/production_sync.sh >> /Users/macmini/.openclaw/workspace/git_sync.log 2>&1

# 5. LEARNING ENGINE - Every 6 hours
# Analyzes completed bets and updates ML insights
0 */6 * * * cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/learning_engine.py >> /Users/macmini/.openclaw/workspace/learning_engine.log 2>&1

# 6. NIGHTLY CLEANUP - 2:00 AM EST
# Archives old logs and cleans up cache
0 2 * * * cd /Users/macmini/.openclaw/workspace && find . -name "*.log" -mtime +7 -delete

# 7. WEEKLY VERIFICATION - Sunday 10:00 PM EST
# Full database verification and consistency check
0 22 * * 0 cd /Users/macmini/.openclaw/workspace && /usr/bin/python3 /Users/macmini/.openclaw/workspace/bet_processor.py verify >> /Users/macmini/.openclaw/workspace/bet_verification.log 2>&1

EOF

# Install crontab
crontab /tmp/larlbot_cron.txt

echo "✅ Cron jobs installed"
echo ""
echo "📋 Active cron jobs:"
crontab -l

echo ""
echo "======================================================================"
echo "✅ Autonomous System Setup Complete!"
echo "======================================================================"
echo ""
echo "🔄 System will now:"
echo "   • Generate picks daily at 7:00 AM"
echo "   • Check game statuses every 15 minutes"
echo "   • Auto-update dashboard every 15 minutes"
echo "   • Sync to production (Railway) every 15 minutes"
echo "   • Run learning engine every 6 hours"
echo "   • Cleanup logs nightly at 2:00 AM"
echo ""
echo "🌐 Local Dashboard:      http://localhost:5001"
echo "🚀 Production Dashboard: https://web-production-a39703.up.railway.app/"
echo ""
echo "📝 Logs:"
echo "   • Daily Picks:    daily_picks.log"
echo "   • Auto Updates:   auto_update.log"
echo "   • Git Sync:       git_sync.log"
echo "   • Learning:       learning_engine.log"
echo ""
echo "======================================================================"
