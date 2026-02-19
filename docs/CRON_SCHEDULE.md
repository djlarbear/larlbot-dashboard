# Cron Schedule - Automated Jobs

All times in **America/Detroit (EST)** timezone.

## Active Jobs

### 🌅 Daily Betting Workflow - 5:00 AM
**Cron:** `0 5 * * *`  
**Script:** `python3 /Users/macmini/.openclaw/workspace/daily_betting_workflow.py`  
**Session:** Main  
**Purpose:** Batched morning workflow
- Fetch yesterday's game scores
- Run learning engine on completed bets
- Update adaptive weights based on performance
- Generate today's top 10 picks

**Status:** ✅ Enabled  
**Last run:** Check via `openclaw cron runs <job-id>`

---

### 🧠 Daily Memory Review - 2:00 AM
**Cron:** `0 2 * * *`  
**Model:** Haiku  
**Session:** Isolated (subagent)  
**Purpose:** Automated memory maintenance
- Read today's memory file
- Extract important decisions, facts, learnings
- Identify automation opportunities
- Update MEMORY.md with significant insights
- Store automation suggestions

**Status:** ✅ Enabled  
**Delivery:** Auto-announce to chat

---

## Planned Jobs (Not Yet Created)

### 📊 Dashboard Health Check - Every 30 min
**Cron:** `*/30 * * * *`  
**Purpose:** Verify dashboard is running
- Check localhost:5001 responds
- Check Railway deployment
- Alert if down

### 🔄 Git Auto-Sync - Daily at 11:59 PM
**Cron:** `59 23 * * *`  
**Purpose:** Backup all data
- Commit any uncommitted changes
- Push to remote
- Verify sync successful

### 📈 Weekly Performance Report - Sunday 10:00 PM
**Cron:** `0 22 * * 0`  
**Purpose:** Weekly summary
- Calculate 7-day win rates by bet type
- Compare to previous week
- Identify trends
- Generate report

### 🗄️ Database Maintenance - Sunday 3:00 AM
**Cron:** `0 3 * * 0`  
**Purpose:** Weekly cleanup
- Vacuum SQLite database
- Archive old log files (>30 days)
- Compress old JSON backups
- Verify data integrity

---

## Managing Cron Jobs

### List all jobs
```bash
openclaw cron list
```

### View job details
```bash
openclaw cron status
```

### Check run history
```bash
openclaw cron runs <job-id>
```

### Disable a job
```bash
# Edit job with patch
openclaw cron update --job-id <id> --patch '{"enabled": false}'
```

### Manually trigger a job
```bash
openclaw cron run <job-id>
```

---

## Cron Expression Format

OpenClaw uses standard cron syntax:
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

### Examples:
- `0 5 * * *` - Every day at 5:00 AM
- `0 2 * * *` - Every day at 2:00 AM
- `*/30 * * * *` - Every 30 minutes
- `0 22 * * 0` - Every Sunday at 10:00 PM
- `0 3 * * 0` - Every Sunday at 3:00 AM

---

## Adding New Jobs

### SystemEvent (Main Session)
For tasks that inject text into main session:
```bash
openclaw cron add --job '{
  "name": "Task Name",
  "schedule": {"kind": "cron", "expr": "0 5 * * *", "tz": "America/Detroit"},
  "payload": {"kind": "systemEvent", "text": "Your command here"},
  "sessionTarget": "main",
  "enabled": true
}'
```

### AgentTurn (Isolated Session)
For autonomous subagent tasks:
```bash
openclaw cron add --job '{
  "name": "Task Name",
  "schedule": {"kind": "cron", "expr": "0 2 * * *", "tz": "America/Detroit"},
  "payload": {
    "kind": "agentTurn",
    "message": "Your task description",
    "model": "anthropic/claude-haiku-4-5",
    "timeoutSeconds": 300
  },
  "sessionTarget": "isolated",
  "delivery": {"mode": "announce"},
  "enabled": true
}'
```

---

## Monitoring

### Check next scheduled run
```bash
openclaw cron list | jq '.jobs[] | {name, nextRun: .state.nextRunAtMs}'
```

### View recent failures
```bash
openclaw cron list | jq '.jobs[] | select(.state.consecutiveErrors > 0)'
```

### Check last run duration
```bash
openclaw cron runs <job-id> | jq '.[0].durationMs'
```

---

## Troubleshooting

### Job not running
1. Check if enabled: `openclaw cron list | jq '.jobs[] | {name, enabled}'`
2. Verify cron expression: Use https://crontab.guru
3. Check timezone: Should be `America/Detroit`
4. Review logs: `openclaw cron runs <job-id>`

### Job timing out
1. Increase `timeoutSeconds` in payload
2. Break into smaller tasks
3. Use Haiku instead of Sonnet for faster execution

### Delivery not working
1. Verify delivery mode: `announce` or `webhook`
2. Check channel config if using announce
3. Test webhook URL if using webhook delivery

---

## Best Practices

1. **Use Haiku for cron jobs** - Faster, cheaper, good enough for automation
2. **Set reasonable timeouts** - 300s (5 min) for most tasks, 600s (10 min) for complex
3. **Prefer isolated sessions** - Keeps main session history clean
4. **Auto-announce results** - So you get notified of completion/failures
5. **Batch similar tasks** - One 5 AM job instead of multiple small jobs
6. **Monitor consecutive errors** - Set up alerts if a job fails 3+ times
7. **Test manually first** - Run with `openclaw cron run` before scheduling

---

## Related Documentation

- `docs/QUICK_START.md` - Manual operation commands
- `docs/FILE_GUIDE.md` - Script purposes and locations
- `MEMORY.md` - System state and decisions
