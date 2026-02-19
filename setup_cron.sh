#!/bin/bash
# Setup automated bet tracking via cron

WORKSPACE="/Users/macmini/.openclaw/workspace"
SCRIPT="$WORKSPACE/run_auto_tracker.sh"

echo "🎰 Setting up automated bet tracking..."
echo ""

# Make scripts executable
chmod +x "$SCRIPT"
chmod +x "$WORKSPACE/auto_track_recommendations.py"
chmod +x "$WORKSPACE/auto_bet_tracker.py"

echo "✅ Made scripts executable"
echo ""

# Create cron job
CRON_CMD="0 8,14,20 * * * $SCRIPT >> $WORKSPACE/auto_tracker.log 2>&1"

echo "📅 Suggested cron schedule:"
echo "   • 8:00 AM  - Track today's recommendations"
echo "   • 2:00 PM  - Check for completed games"
echo "   • 8:00 PM  - Final check for late games"
echo ""

# Check if cron job already exists
crontab -l 2>/dev/null | grep -q "run_auto_tracker.sh"

if [ $? -eq 0 ]; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "run_auto_tracker.sh"
else
    echo "Would you like to add this cron job? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Add to crontab
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✅ Cron job added!"
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
echo "📖 Usage:"
echo "   Manual run:  ./run_auto_tracker.sh"
echo "   View logs:   tail -f auto_tracker.log"
echo "   Edit cron:   crontab -e"
echo "   View cron:   crontab -l"
