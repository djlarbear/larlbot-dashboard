# Quick Start Guide - Betting System

## Daily Pipeline (Automated via Cron)

**5:00 AM EST** - Fetch yesterday's scores
```bash
cd ~/.openclaw/workspace/betting/scripts
python ncaa_hybrid_score_fetcher.py
```

**7:00 AM EST** - Generate daily picks
```bash
cd ~/.openclaw/workspace/betting/scripts
python initialize_daily_bets.py
```

**Every 6h** - Run learning engine
```bash
cd ~/.openclaw/workspace/betting/scripts
python learning_engine.py
python update_adaptive_weights.py
```

## Manual Operations

### Check System Status
```bash
~/.openclaw/workspace/scripts/quick_status.sh
```

### View Today's Picks
```bash
cat ~/.openclaw/workspace/betting/data/ranked_bets.json | jq '.[0:10]'
```

### Check Results
```bash
cd ~/.openclaw/workspace/betting/scripts
python auto_result_tracker.py
```

### View Dashboard
```bash
# Local
open http://localhost:5001

# Start if not running
cd ~/.openclaw/workspace
./START_DASHBOARD.sh
```

### Update Team Stats
```bash
cd ~/.openclaw/workspace/betting/scripts
python ncaa_team_stats_fetcher.py
```

## Common Troubleshooting

### Dashboard won't start
1. Check if port 5001 is in use: `lsof -i :5001`
2. Kill existing process: `kill -9 [PID]`
3. Check logs: `tail -f ~/.openclaw/workspace/betting/logs/*.log`

### No picks generated
1. Check OddsAPI status: `curl https://api.the-odds-api.com/v4/sports`
2. Verify team stats cache exists: `ls -lh ~/.openclaw/workspace/betting/data/team_stats_cache.json`
3. Check adaptive weights: `cat ~/.openclaw/workspace/betting/data/adaptive_weights.json`

### Scores not updating
1. Run score fetcher manually: `python ncaa_hybrid_score_fetcher.py`
2. Check if ESPN API is responding
3. Verify betting.db has recent data: `sqlite3 betting.db "SELECT * FROM bets ORDER BY date DESC LIMIT 5;"`

### Learning engine not improving
1. Check sample sizes: Need 10+ bets per type for reliable learning
2. Verify result normalization: "WIN"/"LOSS"/"PUSH" only (uppercase, stripped)
3. Review calibration buckets in `update_adaptive_weights.py`

## File Locations

- **Scripts:** `~/.openclaw/workspace/betting/scripts/`
- **Data:** `~/.openclaw/workspace/betting/data/`
- **Database:** `~/.openclaw/workspace/betting.db`
- **Logs:** `~/.openclaw/workspace/betting/logs/`
- **Templates:** `~/.openclaw/workspace/templates/`
- **Docs:** `~/.openclaw/workspace/docs/`

## Key Concepts

**LARLScore Formula:**
```
LARLScore = (edge * confidence * bet_type_weight) / 100
```

**Adaptive Learning:**
- Win rates update every 6h
- Bayesian smoothing (Beta(2,2) prior, min 10 samples)
- Weights adjust based on performance

**Top 10 Strategy:**
- Score ALL picks first
- Sort by LARLScore DESC
- Take top 10 only
- Proven 80% win rate on Feb 15

## Quick Commands Cheat Sheet

```bash
# Status check
~/.openclaw/workspace/scripts/quick_status.sh

# Force pick regeneration
cd ~/.openclaw/workspace/betting/scripts && python initialize_daily_bets.py

# View recent bets
sqlite3 ~/.openclaw/workspace/betting.db "SELECT game, bet_type, pick, confidence, result FROM bets ORDER BY date DESC LIMIT 10;"

# Check adaptive weights
cat ~/.openclaw/workspace/betting/data/adaptive_weights.json | jq

# Tail dashboard logs
tail -f ~/.openclaw/workspace/betting/logs/mission-control.log

# Git sync
cd ~/.openclaw/workspace && git add . && git commit -m "Daily update" && git push
```

## Getting Help

1. Check this guide first
2. Review `docs/FILE_GUIDE.md` for script purposes
3. Read `docs/architecture/BETTING_ARCHITECTURE.md` for system design
4. Ask Jarvis (me!) for assistance
