# 🕐 4-Hour Update Schedule - Configuration Guide

## Overview

**Goal:** Reduce GitHub commits from **96/day to 5/day** while maintaining local system responsiveness.

**Strategy:** 
- Keep 15-minute local updates for dashboard freshness
- Push to GitHub every 4 hours (5x/day)
- Internal sync 30 minutes before each push

---

## 📅 Schedule

### **GitHub Push Times (Every 4 Hours)**
- 🕖 **7:00 AM EST**
- 🕚 **11:00 AM EST**
- 🕒 **3:00 PM EST**
- 🕖 **7:00 PM EST**
- 🕚 **11:00 PM EST**

### **Internal Sync Times (30 min before each push)**
- 🕡 **6:30 AM EST** - Full internal sync
- 🕥 **10:30 AM EST** - Full internal sync
- 🕝 **2:30 PM EST** - Full internal sync
- 🕡 **6:30 PM EST** - Full internal sync
- 🕥 **10:30 PM EST** - Full internal sync

### **Local Updates (Every 15 Minutes)**
- Runs at **:00, :15, :30, :45** every hour
- Updates dashboard locally
- NO GitHub push

---

## 🔄 What Happens When

### **Every 15 Minutes (:00, :15, :30, :45)**
**Script:** `auto_update_cycle.py`

1. Check game statuses (ESPN API)
2. Move finished games to completed
3. Update win/loss records
4. Recalculate basic stats
5. Refresh local dashboard
6. **NO GitHub commit** (local only)

**Log:** `auto_update.log`

---

### **Every 4 Hours (:30) - Internal Sync**
**Script:** `full_internal_sync.py`

Comprehensive pre-push sync (30 min before GitHub push):

1. ✅ Check all active games for status
2. ✅ Pull latest scores from ESPN API
3. ✅ Calculate final scores against predictions
4. ✅ Mark bets as WIN/LOSS if game finished
5. ✅ Move finished games to Previous Results
6. ✅ Update win/loss records
7. ✅ Recalculate all stats (Win Rate, Record, by type)
8. ✅ Update `active_bets.json`
9. ✅ Update `ranked_bets.json`
10. ✅ Update `completed_bets_YYYY-MM-DD.json`
11. ✅ Verify data consistency
12. ✅ Prepare everything for GitHub push

**Log:** `internal_sync.log`

**Alert:** If sync takes >5 minutes, logs warning

---

### **Every 4 Hours (:00) - GitHub Push**
**Script:** `scheduled_git_push.sh` → `production_sync.sh`

1. ✅ Check if current time is a scheduled push time
2. ✅ Commit all changes to Git
3. ✅ Push to GitHub (origin/main)
4. ✅ Railway auto-deploys
5. ✅ Production dashboard gets latest data

**Log:** `git_sync.log`

**Commits:** Only at scheduled times (not every 15 min)

---

## 📁 Files Created/Modified

### **New Files:**
```
full_internal_sync.py          - Comprehensive sync before push
scheduled_git_push.sh          - Time-gated GitHub push wrapper
setup_4hour_cron.sh           - Install new cron schedule
verify_4hour_schedule.py      - Verify system configuration
test_4hour_cycle.sh           - Test complete update cycle
4_HOUR_SCHEDULE_GUIDE.md      - This documentation
```

### **Modified Files:**
```
auto_update_cycle.py          - Kept for 15-min local updates (unchanged)
production_sync.sh            - Original push script (called by scheduled_git_push.sh)
```

### **Cron Configuration:**
```
crontab -l                    - View current schedule
setup_4hour_cron.sh          - Install new schedule
```

---

## 🚀 Installation

### **1. Verify Current System**
```bash
cd /Users/macmini/.openclaw/workspace

# Check current cron jobs
crontab -l

# Verify files exist
ls -lh auto_update_cycle.py
ls -lh game_status_checker.py
ls -lh production_sync.sh
```

### **2. Make Scripts Executable**
```bash
chmod +x full_internal_sync.py
chmod +x scheduled_git_push.sh
chmod +x setup_4hour_cron.sh
chmod +x verify_4hour_schedule.py
chmod +x test_4hour_cycle.sh
```

### **3. Install New Cron Schedule**
```bash
./setup_4hour_cron.sh
```

This will:
- Show the new cron configuration
- Ask for confirmation
- Install the new schedule
- Display verification

### **4. Verify Configuration**
```bash
./verify_4hour_schedule.py
```

Expected output:
- ✅ All required files exist
- ✅ Scripts have executable permissions
- ✅ Cron jobs scheduled correctly
- ✅ Push times: 7, 11, 15, 19, 23
- ✅ Sync times: 6:30, 10:30, 14:30, 18:30, 22:30

### **5. Test Complete Cycle**
```bash
./test_4hour_cycle.sh
```

This simulates:
- Local update (15-min)
- Internal sync (pre-push)
- GitHub push check
- Data validation
- Log verification

---

## 📊 Monitoring

### **Real-Time Logs**
```bash
# Local updates (every 15 min)
tail -f auto_update.log

# Internal sync (every 4 hours at :30)
tail -f internal_sync.log

# GitHub push (every 4 hours at :00)
tail -f git_sync.log
```

### **Check Recent Activity**
```bash
# Last 10 local updates
tail -20 auto_update.log

# Last internal sync
tail -50 internal_sync.log | grep "INTERNAL SYNC"

# Last GitHub push
tail -30 git_sync.log | grep "Production Sync"
```

### **Verify Commits**
```bash
# Commits in last 24 hours
git log --oneline --since='1 day ago'

# Should see ~5 commits per day (not 96)
git log --oneline --since='1 day ago' | wc -l
```

### **Railway Deployments**
```bash
# Check Railway dashboard
https://railway.app/project/<your-project>

# Deployments should match push times:
# 7 AM, 11 AM, 3 PM, 7 PM, 11 PM EST
```

---

## 🔧 Troubleshooting

### **Issue: Cron jobs not running**
```bash
# Check if cron service is running
ps aux | grep cron

# Check cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h

# Verify cron jobs
crontab -l | grep -E "(auto_update|internal_sync|git_push)"
```

### **Issue: Scripts not executable**
```bash
chmod +x *.py *.sh

# Verify
ls -lh | grep -E "\.py|\.sh"
```

### **Issue: Internal sync takes too long**
```bash
# Check sync duration
grep "Duration:" internal_sync.log | tail -5

# If >5 minutes, check:
# - ESPN API response time
# - Number of active bets
# - Network connectivity
```

### **Issue: GitHub push failed**
```bash
# Check git status
git status

# Check remote
git remote -v

# Test manual push
git push origin main

# Check credentials
git config --list | grep user
```

### **Issue: Data files corrupted**
```bash
# Validate JSON
python3 -m json.tool active_bets.json
python3 -m json.tool ranked_bets.json

# Check for syntax errors
python3 -c "import json; json.load(open('active_bets.json'))"
```

---

## 📈 Expected Results

### **Before (Old System)**
- **Local updates:** Every 15 min (96x/day)
- **GitHub commits:** Every 15 min (96x/day)
- **Railway deploys:** Every 15 min (96x/day)
- **Issues:** Too many commits, unnecessary deployments

### **After (New System)**
- **Local updates:** Every 15 min (96x/day) ✅
- **GitHub commits:** Every 4 hours (5x/day) ✅
- **Railway deploys:** Every 4 hours (5x/day) ✅
- **Benefits:** 
  - 95% reduction in commits
  - 95% reduction in deployments
  - Same local responsiveness
  - Fresh data 5x/day in production

---

## 🎯 Success Criteria

### ✅ **System Configuration**
- [x] Cron jobs installed for 4-hour schedule
- [x] Internal sync at :30 (5x/day)
- [x] GitHub push at :00 (5x/day)
- [x] Local updates still every 15 min

### ✅ **Data Pipeline**
- [x] Game statuses checked continuously
- [x] Scores updated from ESPN API
- [x] Bets marked WIN/LOSS when finished
- [x] Stats recalculated accurately
- [x] Files updated consistently

### ✅ **Deployment**
- [x] GitHub commits reduced to 5/day
- [x] Railway deploys only at scheduled times
- [x] Production dashboard fresh 5x/day
- [x] Local dashboard updates every 15 min

### ✅ **Logging**
- [x] Internal sync logged at :30
- [x] GitHub push logged at :00
- [x] Alerts if sync >5 minutes
- [x] All data committed before push

---

## 📞 Support

### **Log Files**
- `auto_update.log` - 15-min local updates
- `internal_sync.log` - 4-hour comprehensive sync
- `git_sync.log` - GitHub push activity

### **Verification Scripts**
- `verify_4hour_schedule.py` - Check configuration
- `test_4hour_cycle.sh` - Test complete cycle

### **Manual Operations**
```bash
# Force internal sync
./full_internal_sync.py

# Force GitHub push (bypasses time check)
./production_sync.sh

# Check cron schedule
crontab -l
```

---

## 📝 Version History

- **2026-02-16:** Initial 4-hour schedule implementation
- **Previous:** 15-minute update/push cycle (96x/day)

---

**🎉 System configured for optimal balance:**
- **Local:** Fresh every 15 min
- **Production:** Fresh 5x/day
- **Commits:** Reduced by 95%
- **Deployments:** Reduced by 95%
