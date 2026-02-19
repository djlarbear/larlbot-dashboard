#!/bin/bash
# Setup live game tracking with Telegram updates

WORKSPACE="/Users/macmini/.openclaw/workspace"
SCRIPT="$WORKSPACE/live_game_tracker.py"

echo "🎰 Setting up live game tracking with Telegram updates..."
echo ""

# Make script executable
chmod +x "$SCRIPT"

echo "✅ Made live_game_tracker.py executable"
echo ""

# Create cron job for game time updates
# Runs every 20 minutes during typical game hours (6 PM - 11 PM EST)
CRON_CMD="*/20 18-23 * * * $SCRIPT >> $WORKSPACE/live_tracker.log 2>&1"

echo "📅 Proposed schedule: Every 20 minutes from 6 PM - 11 PM EST"
echo "   (Covers quarter/half marks for NCAA Basketball & NBA)"
echo ""

# Check if cron job already exists
crontab -l 2>/dev/null | grep -q "live_game_tracker.py"

if [ $? -eq 0 ]; then
    echo "⚠️  Live tracker cron job already exists!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "live_game_tracker.py"
else
    echo "Would you like to add this cron job? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Add to crontab
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✅ Live tracker cron job added!"
    else
        echo "⏭️  Skipped cron setup"
        echo ""
        echo "To add manually later, run:"
        echo "  crontab -e"
        echo ""
        echo "Then add this line:"
        echo "  $CRON_CMD"
    fi
fi

echo ""
echo "🎰 Setup complete!"
echo ""
echo "📖 What happens:"
echo "   • Checks every 20 minutes during game hours"
echo "   • Sends Telegram update when games are in progress"
echo "   • Shows your bet and how it's tracking"
echo "   • Updates at quarter/half marks automatically"
echo ""
echo "🧪 Test now:"
echo "   python3 $SCRIPT"
echo ""
echo "📊 View logs:"
echo "   tail -f live_tracker.log"
echo ""
echo "⚙️ Telegram configured:"
echo "   Updates will be sent to your paired Telegram"
