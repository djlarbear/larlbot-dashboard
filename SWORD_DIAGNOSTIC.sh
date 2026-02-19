#!/bin/bash
echo "=== SWORD COMPREHENSIVE DIAGNOSTIC ==="
echo ""
echo "1. PYTHON ENVIRONMENT"
python3 --version
python3 -c "import sys; print(f'✓ Path: {sys.prefix}')"
echo ""

echo "2. CRITICAL SCRIPTS - PERMISSIONS & SYNTAX"
for script in initialize_daily_bets.py game_status_checker.py learning_engine.py auto_result_tracker_v2.py; do
  if [ -f "$script" ]; then
    if [ -x "$script" ]; then
      echo "✓ $script (executable)"
      python3 -m py_compile "$script" 2>&1 | grep -q "Error" && echo "  ⚠️ SYNTAX ERROR" || echo "  ✓ Syntax OK"
    else
      echo "✗ $script (NOT executable) - FIXING..."
      chmod +x "$script"
      echo "  ✓ Fixed"
    fi
  else
    echo "✗ $script (MISSING)"
  fi
done
echo ""

echo "3. JSON DATA FILES - INTEGRITY & TIMESTAMPS"
for json in active_bets.json ranked_bets.json completed_bets_2026-02-16.json todays_smart_picks.json learning_insights.json; do
  if [ -f "$json" ]; then
    python3 -c "import json; json.load(open('$json'))" 2>&1 | grep -q "Error" && echo "✗ $json (CORRUPT)" || echo "✓ $json (valid)"
  fi
done
echo ""

echo "4. GIT STATUS"
git status --short || echo "✗ Git not initialized"
echo ""
echo "Last commit:"
git log -1 --format="%h %s" 2>/dev/null || echo "No commits"
echo ""

echo "5. API CREDENTIALS & CONFIGS"
if [ -f "railway.json" ]; then
  echo "✓ railway.json present"
else
  echo "✗ railway.json MISSING"
fi
echo ""

echo "6. MEMORY SYSTEM"
ls -lh SOUL.md IDENTITY.md HEARTBEAT.md 2>/dev/null | awk '{print "✓", $9}'
[ -d "memory" ] && echo "✓ Memory directory exists ($(ls memory/*.md 2>/dev/null | wc -l) files)" || echo "✗ Memory directory missing"
echo ""

echo "7. DISK SPACE & INODE STATUS"
df -h /Users/macmini/.openclaw/agents/sword | tail -1 | awk '{print "Disk: " $5 " used (" $4 " available)"}'
echo ""

echo "8. PERMISSION ISSUES"
find . -type f ! -perm -u+r 2>/dev/null | wc -l | xargs -I {} echo "{} files with read permission issues"
find . -type f -name "*.py" ! -perm -u+x ! -perm -g+x 2>/dev/null | wc -l | xargs -I {} echo "{} Python scripts not executable"
echo ""

echo "=== DIAGNOSTIC COMPLETE ==="
