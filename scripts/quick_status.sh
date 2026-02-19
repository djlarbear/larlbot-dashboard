#!/bin/bash
# Quick Status Check for Betting System

echo "════════════════════════════════════════════"
echo "🎲 BETTING SYSTEM STATUS"
echo "════════════════════════════════════════════"
echo ""

# Dashboard Status
echo "📊 DASHBOARD STATUS:"
if curl -s http://localhost:5001 >/dev/null 2>&1; then
    echo "  ✅ Local (localhost:5001) - UP"
else
    echo "  ❌ Local (localhost:5001) - DOWN"
fi
echo ""

# Database Check
echo "💾 DATABASE:"
if [ -f ~/.openclaw/workspace/betting.db ]; then
    DB_SIZE=$(du -h ~/.openclaw/workspace/betting.db | cut -f1)
    BETS=$(sqlite3 ~/.openclaw/workspace/betting.db "SELECT COUNT(*) FROM bets;" 2>/dev/null || echo "Error")
    TEAMS=$(sqlite3 ~/.openclaw/workspace/betting.db "SELECT COUNT(*) FROM team_stats;" 2>/dev/null || echo "Error")
    echo "  ✅ betting.db ($DB_SIZE)"
    echo "  📈 Total bets: $BETS"
    echo "  🏀 Teams cached: $TEAMS"
else
    echo "  ❌ betting.db NOT FOUND"
fi
echo ""

# Recent Picks
echo "🎯 RECENT PICKS:"
if [ -f ~/.openclaw/workspace/betting/data/ranked_bets.json ]; then
    PICKS=$(jq 'length' ~/.openclaw/workspace/betting/data/ranked_bets.json 2>/dev/null || echo "Error")
    TOP_SCORE=$(jq '.[0].larl_score // "N/A"' ~/.openclaw/workspace/betting/data/ranked_bets.json 2>/dev/null)
    echo "  📋 Total picks available: $PICKS"
    echo "  ⭐ Top LARLScore: $TOP_SCORE"
else
    echo "  ⚠️  ranked_bets.json NOT FOUND"
fi
echo ""

# Win Rates
echo "📈 PERFORMANCE (from adaptive_weights.json):"
WEIGHTS_FILE=~/.openclaw/workspace/betting/data/adaptive_weights.json
if [ -f "$WEIGHTS_FILE" ]; then
    TOTAL_WR=$(jq -r '.weights.TOTAL.win_rate // "N/A"' "$WEIGHTS_FILE" 2>/dev/null)
    SPREAD_WR=$(jq -r '.weights.SPREAD.win_rate // "N/A"' "$WEIGHTS_FILE" 2>/dev/null)
    TOTAL_WT=$(jq -r '.weights.TOTAL.weight // "N/A"' "$WEIGHTS_FILE" 2>/dev/null)
    SPREAD_WT=$(jq -r '.weights.SPREAD.weight // "N/A"' "$WEIGHTS_FILE" 2>/dev/null)
    echo "  🎯 TOTAL: ${TOTAL_WR}% (weight: $TOTAL_WT)"
    echo "  📏 SPREAD: ${SPREAD_WR}% (weight: $SPREAD_WT)"
else
    echo "  ⚠️  adaptive_weights.json NOT FOUND"
fi
echo ""

# Cron Jobs
echo "⏰ CRON JOBS:"
echo "  Run: openclaw cron list"
echo ""

# Git Status
echo "🔧 GIT STATUS:"
cd ~/.openclaw/workspace
if [ -d .git ]; then
    UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
    if [ "$UNCOMMITTED" -eq 0 ]; then
        echo "  ✅ All changes committed"
    else
        echo "  ⚠️  $UNCOMMITTED uncommitted changes"
        echo "  Run: git status"
    fi
else
    echo "  ⚠️  Not a git repository"
fi
echo ""

echo "════════════════════════════════════════════"
echo "💡 Quick Commands:"
echo "  Dashboard: open http://localhost:5001"
echo "  Logs: tail -f ~/.openclaw/workspace/betting/logs/*.log"
echo "  Full audit: Use templates/audit_checklist.md"
echo "════════════════════════════════════════════"
