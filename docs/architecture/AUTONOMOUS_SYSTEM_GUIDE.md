# 🤖 LarlBot Autonomous Betting System - Complete Guide

## ✅ SYSTEM STATUS: FULLY OPERATIONAL

The LarlBot betting system is now **100% autonomous** with 15-minute refresh cycles and automatic deployment to production.

---

## 🎯 What This System Does

### Fully Automated Operation
- **NO manual intervention required**
- Generates daily picks automatically at 7:00 AM
- Updates game statuses every 15 minutes (96 times per day)
- Moves finished games to "Previous Results" automatically
- Calculates win/loss records in real-time
- Syncs to GitHub and deploys to Railway automatically
- Dashboard always shows fresh data (local AND production)

---

## 🏗️ System Architecture

### Core Components

#### 1. **Daily Picks Generator** (`daily_recommendations.py`)
- **Runs:** 7:00 AM EST daily
- **Function:** Generates betting recommendations using ML + adaptive learning
- **Output:** `active_bets.json` with all picks for the day

#### 2. **Bet Initializer** (`initialize_daily_bets.py`)
- **Runs:** 7:05 AM EST daily
- **Function:** Creates `active_bets.json` and runs `bet_ranker.py` to generate Top 10
- **Output:** `ranked_bets.json` with top recommendations

#### 3. **Game Status Checker** (`game_status_checker.py`)
- **Runs:** Every 15 minutes (via `auto_update_cycle.py`)
- **Function:** 
  - Checks ESPN API for game scores
  - Detects finished games
  - Calculates WIN/LOSS results
  - Moves completed bets to `completed_bets_2026-02-16.json`
- **Output:** Updated `active_bets.json`, `ranked_bets.json`, `completed_bets_*.json`

#### 4. **Auto-Update Cycle** (`auto_update_cycle.py`)
- **Runs:** Every 15 minutes (:00, :15, :30, :45)
- **Function:** Orchestrates the entire refresh cycle
  - Runs game status checker
  - Recalculates stats
  - Updates timestamps
- **Output:** Fresh data in all JSON files

#### 5. **Production Sync** (`production_sync.sh`)
- **Runs:** Every 15 minutes (:05, :20, :35, :50) - 5 min after update cycle
- **Function:**
  - Auto-commits changes to Git
  - Pushes to GitHub (`djlarbear/larlbot-dashboard`)
  - Triggers Railway auto-deployment
- **Output:** Production dashboard at https://web-production-a39703.up.railway.app/

#### 6. **Learning Engine** (`learning_engine.py`)
- **Runs:** Every 6 hours
- **Function:** Analyzes completed bets and updates ML insights
- **Output:** `learning_insights.json`

#### 7. **Dashboard Server** (`dashboard_server_cache_fixed.py`)
- **Runs:** Continuously on port 5001
- **Function:** Serves fresh data with strict no-cache headers
- **Features:**
  - All API endpoints return timestamps
  - Cache-Control headers force browser refresh
  - Railway-compatible timezone handling (EST)

---

## ⏰ Cron Schedule

```bash
# Daily Picks - 7:00 AM EST
0 7 * * * daily_recommendations.py

# Initialize Bets - 7:05 AM EST
5 7 * * * initialize_daily_bets.py

# 15-Minute Updates - Every 15 minutes (96x/day)
0,15,30,45 * * * * auto_update_cycle.py

# Git Sync - Every 15 minutes (5 min after updates)
5,20,35,50 * * * * production_sync.sh

# Learning Engine - Every 6 hours
0 */6 * * * learning_engine.py

# Nightly Cleanup - 2:00 AM EST
0 2 * * * find . -name "*.log" -mtime +7 -delete

# Weekly Verification - Sunday 10:00 PM EST
0 22 * * 0 bet_processor.py verify
```

---

## 📊 Data Flow

```
7:00 AM → Generate Picks → active_bets.json
         ↓
7:05 AM → Rank Bets → ranked_bets.json (Top 10)
         ↓
Every 15 min → Check Games → ESPN API
         ↓
         → Update Status → active_bets.json (remove finished)
         ↓
         → Move Completed → completed_bets_2026-02-16.json
         ↓
         → Recalculate Stats → cache/bet_stats.json
         ↓
+5 min → Git Commit & Push → GitHub
         ↓
         → Railway Auto-Deploy → Production Dashboard
```

---

## 🌐 Dashboard URLs

- **Local:** http://localhost:5001
- **Production:** https://web-production-a39703.up.railway.app/

Both dashboards update automatically every 15 minutes with:
- Active games (Today's Bets tab)
- Completed games (Previous Results tab)
- Live win/loss statistics
- Real-time timestamps

---

## 📝 Log Files

All automation logs stored in workspace:

- `daily_picks.log` - Daily picks generation
- `auto_update.log` - 15-minute update cycles
- `git_sync.log` - Git push operations
- `learning_engine.log` - ML learning updates
- `dashboard.log` - Dashboard server output
- `bet_verification.log` - Weekly verification

---

## 🔍 Monitoring & Verification

### System Health Check
```bash
python3 system_monitor.py
```

Shows:
- Data file freshness (updated timestamps)
- Cron job status (active/missing)
- Git repository health
- Recent log activity

### Full System Verification
```bash
python3 verify_autonomous_system.py
```

Tests:
- Essential files existence
- Automation scripts executable
- Cron jobs installed
- Git repository connected
- Local dashboard API
- Production dashboard API (Railway)

**Expected Result:** 100% pass rate (21/21 tests)

---

## 🚀 Railway Deployment

### Auto-Deployment Pipeline

1. Local cron job runs every 15 minutes
2. `production_sync.sh` commits changes to Git
3. Pushes to GitHub repository
4. Railway detects commit on `main` branch
5. Railway rebuilds and deploys automatically
6. Production dashboard updates within 2-3 minutes

### Railway Configuration

**Project:** larlbot-dashboard  
**Repository:** djlarbear/larlbot-dashboard  
**Branch:** main  
**Build Command:** Automatic (Dockerfile)  
**Start Command:** Defined in Dockerfile  
**Environment:** Python 3.9  
**Port:** 5001 (auto-detected)

---

## 🛠️ Manual Operations (If Needed)

### Force Immediate Update
```bash
python3 auto_update_cycle.py
```

### Force Git Sync
```bash
bash production_sync.sh
```

### Restart Dashboard
```bash
pkill -f dashboard_server_cache_fixed.py
nohup python3 dashboard_server_cache_fixed.py > dashboard.log 2>&1 &
```

### Check Cron Jobs
```bash
crontab -l
```

### Reinstall Cron Jobs
```bash
bash setup_autonomous_cron.sh
```

---

## ✅ Verification Checklist

After system setup, verify:

- [ ] Cron jobs installed (`crontab -l`)
- [ ] Dashboard running locally (http://localhost:5001)
- [ ] Production dashboard accessible (Railway URL)
- [ ] API endpoints return timestamps
- [ ] Cache headers prevent stale data
- [ ] Git pushes automatically every 15 min
- [ ] Railway deploys automatically
- [ ] Game status checker works (ESPN API)
- [ ] Stats recalculate correctly
- [ ] Logs are being written

**Run:** `python3 verify_autonomous_system.py` for automated checks

---

## 📈 Success Metrics

### What "Working" Looks Like:

1. **Morning (7:00 AM):**
   - New picks generated automatically
   - Top 10 ranked and displayed on dashboard

2. **Throughout Day (Every 15 min):**
   - Games checked for completion
   - Finished games move to Previous Results
   - Win/loss records updated
   - Dashboard refreshes

3. **Production Sync (Every 15 min):**
   - Changes committed to Git
   - Pushed to GitHub
   - Railway deploys latest code
   - Production dashboard stays current

4. **End of Day:**
   - All finished games show results
   - Stats accurately reflect performance
   - Learning engine has updated insights

---

## 🎯 Key Features

### ✅ Autonomous Operation
- Zero manual intervention required
- Self-maintaining 24/7

### ✅ Real-Time Updates
- 15-minute refresh cycle
- Always shows current game status

### ✅ Automatic Result Detection
- ESPN API integration
- Auto-calculates WIN/LOSS
- Moves finished games automatically

### ✅ Production Deployment
- Auto-sync to GitHub
- Railway auto-deployment
- Both dashboards always fresh

### ✅ Cache-Free Dashboard
- Strict no-cache headers
- Timestamps on all API responses
- Browser never shows stale data

### ✅ Monitoring & Logging
- Comprehensive logs for all operations
- Health check scripts
- Verification tools

---

## 🐛 Troubleshooting

### Dashboard Shows Old Data
1. Check `auto_update.log` for errors
2. Verify cron jobs are running (`crontab -l`)
3. Restart dashboard: `pkill -f dashboard_server_cache_fixed.py && nohup python3 dashboard_server_cache_fixed.py &`
4. Force browser refresh: Ctrl+Shift+R (hard refresh)

### Git Sync Not Working
1. Check `git_sync.log` for errors
2. Verify GitHub credentials: `git remote -v`
3. Test manual push: `bash production_sync.sh`
4. Check network connectivity

### Railway Not Deploying
1. Check GitHub for new commits
2. Verify Railway is connected to correct repo/branch
3. Check Railway dashboard for build logs
4. Verify Dockerfile is valid

### Cron Jobs Not Running
1. Check cron service: `ps aux | grep cron`
2. Reinstall cron jobs: `bash setup_autonomous_cron.sh`
3. Check cron logs: `/var/log/cron` or system logs

---

## 📚 File Reference

### Data Files
- `active_bets.json` - Current active bets (not yet finished)
- `ranked_bets.json` - Top 10 recommended bets
- `completed_bets_2026-02-16.json` - Finished games with results
- `cache/bet_stats.json` - Win/loss statistics

### Scripts
- `daily_recommendations.py` - Generate daily picks
- `initialize_daily_bets.py` - Initialize daily bet tracking
- `auto_update_cycle.py` - 15-min refresh orchestrator
- `game_status_checker.py` - Check game scores (ESPN)
- `production_sync.sh` - Git auto-sync
- `system_monitor.py` - Health check tool
- `verify_autonomous_system.py` - End-to-end testing
- `dashboard_server_cache_fixed.py` - Web server

### Configuration
- `setup_autonomous_cron.sh` - Install cron jobs
- `.gitignore` - Git ignore rules
- `Dockerfile` - Railway deployment config

---

## 🎉 Success Confirmation

**System is FULLY OPERATIONAL when:**

1. ✅ All cron jobs installed
2. ✅ Dashboard runs locally (http://localhost:5001)
3. ✅ Production dashboard accessible (Railway)
4. ✅ `verify_autonomous_system.py` shows 100% pass rate
5. ✅ `system_monitor.py` shows all files fresh (<20 min old)
6. ✅ `git_sync.log` shows recent pushes
7. ✅ Railway dashboard shows recent deployments
8. ✅ Both dashboards update automatically every 15 minutes

---

## 🙌 You Can Walk Away!

**Larry, the system is now autonomous:**

- ✅ Picks generated daily at 7 AM
- ✅ Games checked every 15 minutes
- ✅ Results detected automatically
- ✅ Stats updated in real-time
- ✅ Dashboard always fresh (local + production)
- ✅ Git syncs automatically
- ✅ Railway deploys automatically
- ✅ No manual work required

**Just check the dashboards when you want to see results!**

🌐 **Local:** http://localhost:5001  
🚀 **Production:** https://web-production-a39703.up.railway.app/

---

*Last Updated: 2026-02-16 08:10 EST*  
*System Version: Autonomous v1.0 - Full 15-Minute Refresh*
