# System Audit Checklist

**Date:** YYYY-MM-DD  
**Auditor:** [Name]

## Dashboard Status
- [ ] Local dashboard (localhost:5001) - UP/DOWN
- [ ] Railway dashboard - UP/DOWN
- [ ] Last data refresh timestamp - [TIME]

## Data Integrity
- [ ] `betting.db` exists and accessible
- [ ] `team_stats_cache.json` current (last updated: [DATE])
- [ ] `adaptive_weights.json` valid JSON
- [ ] Active bets count: X
- [ ] Completed bets count: X

## Pipeline Health
- [ ] OddsAPI responding (check last API call)
- [ ] Score fetcher working (check recent games)
- [ ] Learning engine ran successfully (check last run time)
- [ ] Picks generated for today

## Cron Jobs
- [ ] 5 AM - Score fetch (last run: [TIME])
- [ ] 7 AM - Daily picks (last run: [TIME])
- [ ] Every 6h - Learning engine (last run: [TIME])
- [ ] 10 PM Sunday - Weekly DB verify (last run: [DATE])

## Performance Metrics
- **Last 7 days win rate:** X%
- **Last 30 days win rate:** X%
- **TOTAL performance:** X%
- **SPREAD performance:** X%

## Git Status
- [ ] All changes committed
- [ ] Synced with remote
- [ ] No uncommitted data files

## Issues Found
1. [Issue description] - Priority: HIGH/MEDIUM/LOW
2. [Issue description] - Priority: HIGH/MEDIUM/LOW

## Actions Required
- [ ] [Action item with deadline]
- [ ] [Action item with deadline]

## Notes
[Additional observations]
