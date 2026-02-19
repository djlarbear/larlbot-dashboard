#!/bin/bash
# Setup automated bet tracking and result updates

WORKSPACE="/Users/macmini/.openclaw/workspace"
SCRIPT="$WORKSPACE/auto_update_results.py"

echo "🎰 Setting up automated bet tracking..."

# Create cron job to check for completed games every 30 minutes
# This runs auto_update_results.py check to move completed bets to tracker

CRON_SCHEDULE="*/30 * * * * cd $WORKSPACE && /usr/bin/python3 $SCRIPT check >> /tmp/larlbot_tracking.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "auto_update_results.py"; then
    echo "✅ Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE") | crontab -
    echo "✅ Cron job added: Check for completed bets every 30 minutes"
fi

echo ""
echo "📊 Automated Bet Tracking Setup Complete!"
echo ""
echo "How it works:"
echo "1. All today's picks are auto-saved to active_bets.json"
echo "2. Every 30 minutes, the system checks for completed games"
echo "3. When a game is finished, use: curl -X POST http://localhost:8000/api/update-result ..."
echo "4. The bet automatically moves to Previous Results with all data"
echo ""
echo "Manual update command:"
echo "curl -X POST http://localhost:8000/api/update-result \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"game\": \"Ohio @ Miami\", \"result\": \"WIN\", \"final_score\": \"74-90\"}'"
echo ""
echo "Tracking log: /tmp/larlbot_tracking.log"
