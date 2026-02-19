#!/bin/bash
# Production Sync - Auto-commit and push to GitHub
# Triggers Railway auto-deployment

WORKSPACE="${WORKSPACE:-$(pwd)}"
cd "$WORKSPACE"

# Timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S EST")

echo "======================================================================"
echo "🚀 Production Sync - Git Auto-Commit & Push"
echo "======================================================================"
echo "⏰ Time: $TIMESTAMP"

# Check if there are changes
if [[ -z $(git status -s) ]]; then
    echo "✅ No changes to commit - workspace is clean"
    exit 0
fi

# Show what changed
echo ""
echo "📝 Changes detected:"
git status -s

# Add all changes
echo ""
echo "➕ Adding changes..."
git add active_bets.json ranked_bets.json completed_bets_*.json cache/*.json auto_update.log

# Commit with timestamp
COMMIT_MSG="Auto-update: $TIMESTAMP"
echo ""
echo "💾 Committing: $COMMIT_MSG"
git commit -m "$COMMIT_MSG" 2>&1

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
if git push origin main 2>&1; then
    echo "✅ Push successful - Railway will auto-deploy"
    echo "🌐 Dashboard: https://web-production-a39703.up.railway.app/"
else
    echo "❌ Push failed - check network/credentials"
    exit 1
fi

echo ""
echo "======================================================================"
echo "✅ Production Sync Complete"
echo "======================================================================"
