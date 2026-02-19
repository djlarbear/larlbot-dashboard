# HEARTBEAT.md

# HEARTBEAT.md - Sword's Background Checks

Keep this file empty—Sword operates via cron jobs, not heartbeat polling.

## Cron-Driven Automation (No Heartbeat Needed)
✅ 5:00 AM EST - Browser scraper (get yesterday's results)
✅ 7:00 AM EST - Generate daily picks + update dashboard
✅ Every 6h - Learning engine (analyze wins/losses, update confidence)
✅ 10:00 PM Sunday - Weekly database verification
✅ Every 15 min - Dashboard refresh (game status check)

Sword runs these jobs autonomously. No manual heartbeat checks needed.

## If Jarvis Spawns Sword On-Demand
Sword will accept messages from Jarvis like:
- "Run daily picks now" → execute initialize_daily_bets.py
- "Check results" → run auto_result_tracker.py
- "Get status" → return current bet stats
- "Analyze performance" → run learning_engine.py

## Report Format
Always report back to Jarvis with:
- Status: SUCCESS | FAILURE
- Key metrics: (picks generated, results checked, win rate, etc.)
- Errors: (if any)
- Next scheduled run: (when is the next automated task?)
