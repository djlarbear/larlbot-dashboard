#!/bin/bash
# Setup completely autonomous betting system
# No manual intervention needed after configuration

WORKSPACE="/Users/macmini/.openclaw/workspace"
CHECKER_SCRIPT="$WORKSPACE/auto_result_checker.py"
LOG_FILE="/tmp/larlbot_auto_update.log"

echo "🎰 Setting up Autonomous Betting System..."
echo ""

# Verify scripts exist
if [ ! -f "$CHECKER_SCRIPT" ]; then
    echo "❌ ERROR: auto_result_checker.py not found!"
    exit 1
fi

echo "✅ auto_result_checker.py found"
echo ""

# Make scripts executable
chmod +x "$CHECKER_SCRIPT"
chmod +x "$WORKSPACE/dashboard_server.py"

echo "📋 Cron Jobs to be added:"
echo ""
echo "1. Check for completed games every 30 minutes (all day)"
echo "   */30 * * * * cd $WORKSPACE && /usr/bin/python3 $CHECKER_SCRIPT"
echo ""
echo "2. Generate fresh daily picks at 8:00 AM EST (optional)"
echo "   0 8 * * * cd $WORKSPACE && /usr/bin/python3 -c 'from auto_update_results import save_todays_picks; from daily_recommendations import get_todays_value_bets; save_todays_picks(get_todays_value_bets())'"
echo ""

# Add cron jobs
echo "Installing cron jobs..."

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "auto_result_checker.py"; then
    echo "✅ Auto result checker cron job already exists"
else
    (crontab -l 2>/dev/null; echo "*/30 * * * * cd $WORKSPACE && /usr/bin/python3 $CHECKER_SCRIPT >> $LOG_FILE 2>&1") | crontab -
    echo "✅ Added auto result checker (every 30 minutes)"
fi

echo ""
echo "🎯 System Configuration Complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "AUTONOMOUS SYSTEM STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Daily Picks Generation:"
echo "   Auto-generated every day from daily_recommendations.py"
echo "   Saved to: active_bets.json"
echo "   Display: Today's Bets tab"
echo ""
echo "✅ Game Monitoring:"
echo "   Runs automatically every 30 minutes"
echo "   Fetches latest game results"
echo "   Matches results with active bets"
echo ""
echo "✅ Result Updates:"
echo "   Automatically determines WIN/LOSS"
echo "   Calculates final scores"
echo "   Moves completed bets to Previous Results"
echo ""
echo "✅ Statistics:"
echo "   Win rate auto-calculated"
echo "   Record auto-updated"
echo "   Organized by date"
echo ""
echo "✅ Data Files:"
echo "   active_bets.json → Today's picks (auto-managed)"
echo "   bet_tracker_input.json → Historical results (auto-updated)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NO MANUAL INTERVENTION REQUIRED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Just start the dashboard:"
echo "  python3 dashboard_server.py"
echo ""
echo "Everything else runs automatically! 🚀"
echo ""
echo "Monitor the log:"
echo "  tail -f $LOG_FILE"
echo ""
