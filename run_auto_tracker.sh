#!/bin/bash
# Master script to fully automate bet tracking & result verification
# Run every 30 minutes to track recommendations and update results

cd /Users/macmini/.openclaw/workspace

echo "🎰 LarlBot Automated Betting System"
echo "📅 $(date)"
echo ""

# Main: Check for completed games and move to previous results
echo "🔍 Checking for completed game results..."
python3 auto_result_tracker.py
RESULT_CHECK=$?

# Optional: Sync to dashboard if changes were made
echo ""
echo "💾 Syncing changes to GitHub..."

git add -A

if git diff --staged --quiet; then
    echo "✅ No changes to sync"
else
    git commit -m "Auto-update: Result tracking $(date '+%Y-%m-%d %H:%M')"
    git push
    echo "✅ Pushed updates to dashboard!"
fi

echo ""
echo "🎰 Automation complete!"
