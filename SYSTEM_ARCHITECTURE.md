# 🏗️ SYSTEM ARCHITECTURE - Betting System v4.0

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     LARLBOT BETTING SYSTEM                       │
│                    (Fully Autonomous v4.0)                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   GENERATION LAYER   │         │   LEARNING LAYER     │
├──────────────────────┤         ├──────────────────────┤
│ • Daily picks (7 AM) │    +    │ • Learning engine    │
│ • Comprehensive exp. │         │ • Adaptive weights   │
│ • LarlScore v4.0     │         │ • Performance track  │
└──────┬───────────────┘         └──────┬───────────────┘
       │                                 │
       └────────────────┬────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   RANKING LAYER (LarlScore)   │
        ├───────────────────────────────┤
        │ • Formula: edge × conf × rate │
        │ • Adaptive weights applied    │
        │ • Top 10 selected             │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │    DASHBOARD LAYER            │
        ├───────────────────────────────┤
        │ • Flask backend (localhost:5001)
        │ • Real-time updates           │
        │ • REST APIs                   │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   MONITORING LAYER            │
        ├───────────────────────────────┤
        │ • Game status checker (15 min)│
        │ • Score auto-population       │
        │ • Result tracking             │
        └───────────────────────────────┘
```

---

## Component Architecture

### 1. **Pick Generation** (7:00 AM EST)
**File:** `generate_improved_picks.py`  
**Inputs:** Today's OddsAPI odds + Historical performance  
**Process:**
- Calls `daily_recommendations.py`
- Fetches real games + odds from FanDuel
- Generates predictions (confidence, edge)
- Creates 25 initial picks

**Output:** `active_bets.json`
```json
{
  "date": "2026-02-17",
  "total_picks": 25,
  "bets": [
    {
      "game": "Team A @ Team B",
      "bet_type": "SPREAD|TOTAL|MONEYLINE",
      "recommendation": "Team +5.5",
      "confidence": 75,
      "edge": 5.0
    }
  ]
}
```

---

### 2. **Comprehensive Expansion** (7:00 AM EST)
**File:** `comprehensive_bet_generator.py`  
**Inputs:** 25 initial picks from generation  
**Process:**
- For each SPREAD: generates both favorite + underdog
- For each TOTAL: generates both OVER + UNDER
- Preserves all metadata
- Creates 135 total options

**Output:** Updated `active_bets.json` (135 bets)

**Why:** Ensures LarlScore ranks ALL options fairly, not just pre-selected ones

---

### 3. **LarlScore Ranking** (7:00 AM EST)
**File:** `bet_ranker_v4_improved.py`  
**Formula:**
```
LarlScore = base × edge_mult × conf_mult × bet_type_mult

Where:
  base = (confidence/100) × edge × (win_rate/0.5)
  
  edge_mult:
    - 1.5x if edge ≥ 20pts
    - 1.3x if edge 10-19pts
    - 1.0x if edge 5-9pts
    - 0.5x if edge < 5pts
  
  conf_mult:
    - 1.2x if confidence ≥ 80%
    - 1.1x if confidence 75-79%
    - 1.0x otherwise
  
  bet_type_mult:
    - SPREAD: 1.22x (63.6% historical win rate)
    - TOTAL: 1.4x if edge ≥ 20pts, else 0.75x
    - MONEYLINE: 0.0x (disabled - 0% win rate)
```

**Inputs:** 135 comprehensive bets + adaptive weights  
**Process:**
- Calculates score for each bet
- Sorts by score descending
- Selects top 10
- Ranks #1-#10

**Outputs:**
- `ranked_bets.json` (main dashboard file)
- `ranked_bets_2026-02-17.json` (dated archive)

---

### 4. **Dashboard** (Continuous)
**File:** `dashboard_server_cache_fixed.py` (Flask backend)  
**Port:** localhost:5001

**APIs:**
```
GET /api/stats
  Returns: { win_rate, record, total_bets, timestamp }

GET /api/bets
  Returns: { bets (top 10 active), count, timestamp }

GET /api/ranked-bets
  Returns: { top_10, rest, summary }

GET /api/previous-results
  Returns: [ { game, result, win/loss }, ... ]
```

**Frontend:** `templates/index.html` + `static/script_v3.js`
- Displays top 10 picks
- Shows previous results
- Auto-refreshes every 30 seconds
- Glass-morphism design (modern UI)

---

### 5. **Game Status Checker** (Every 15 minutes)
**File:** `game_status_checker.py`  
**Cron:** `0,15,30,45 * * * *`  
**Process:**
- Fetches game scores from NCAA-API
- Updates `completed_bets_*.json` with results
- Moves games from "PENDING" → "WIN"/"LOSS"
- Auto-populations scores and final results

**Key:** Uses date-path NCAA-API (`/scoreboard/.../YYYY/MM/DD`)
- Critical: This endpoint requires date path
- Returns `away.score`, `home.score`, `gameState`

---

### 6. **Learning Engine** (Every 6 hours)
**File:** `learning_engine.py`  
**Cron:** `0 */6 * * *`  
**Process:**
1. Load all completed bets
2. Calculate win % by bet type
3. Identify patterns (edge, confidence, etc.)
4. Generate insights
5. Save to `learning_insights.json`

**Output:** Used to update adaptive weights

---

### 7. **Adaptive Weights** (Every 6 hours)
**File:** `update_adaptive_weights.py`  
**Cron:** Triggered by learning engine  
**Process:**
1. Read betting results
2. Calculate win rate by type
3. Adjust multipliers:
   - If type wins 60%+ → boost weight
   - If type wins 40%- → suppress weight
4. Save to `adaptive_weights.json`

**Example:**
```json
{
  "weights": {
    "SPREAD": {"weight": 1.22, "win_rate": 0.636, "reason": "Strong performer"},
    "TOTAL": {"weight": 0.75, "win_rate": 0.400, "reason": "Weak performer"},
    "MONEYLINE": {"weight": 0.0, "win_rate": 0.000, "reason": "Disabled"}
  }
}
```

**Impact:** Tomorrow's LarlScore uses today's learned weights

---

## Cron Job Schedule

```
TIME              COMMAND                            PURPOSE
─────────────────────────────────────────────────────────────────
7:00 AM EST       generate_improved_picks.py        Generate + rank picks
7:05 AM EST       (implicit via generate)           Saves ranked_bets.json

3:00 PM EST       learning_engine.py                Analyze performance
3:01 PM EST       update_adaptive_weights.py        Update weights

9:00 PM EST       learning_engine.py                Second analysis
9:01 PM EST       update_adaptive_weights.py        Update weights

3:00 AM EST       learning_engine.py                Final analysis
3:01 AM EST       update_adaptive_weights.py        Update weights

Every 15 min      game_status_checker.py            Track game results
(0,15,30,45 * * * *)

Sundays 10 PM EST data_integrity_audit_v2.py        Weekly verification
```

---

## Data Flow

```
OddsAPI (Live Odds)
    │
    ▼
daily_recommendations.py (Generate 25 picks)
    │
    ▼
active_bets.json (Initial picks)
    │
    ▼
comprehensive_bet_generator.py (Expand to 135)
    │
    ▼
active_bets.json (All options)
    │
    ▼
bet_ranker_v4_improved.py (Score + rank)
    │
    ▼
ranked_bets.json (Top 10)
    │
    ▼
Dashboard Backend (Flask)
    │
    ▼
Dashboard Frontend (Browser)
    │
    └─ User places bets
    │
    ▼
Games kick off (6-8 PM)
    │
    ▼
game_status_checker.py (Every 15 min)
    │
    ▼
NCAA-API (Fetch scores)
    │
    ▼
completed_bets_*.json (Populate results)
    │
    ▼
learning_engine.py (Every 6 hours)
    │
    ▼
learning_insights.json (Performance analysis)
    │
    ▼
update_adaptive_weights.py
    │
    ▼
adaptive_weights.json (New weights)
    │
    └─ Used next day for LarlScore
```

---

## File Structure

```
/Users/macmini/.openclaw/workspace/
├─ CORE SCRIPTS
│  ├─ generate_improved_picks.py        (Daily pick generation)
│  ├─ daily_recommendations.py          (Fetch odds + generate)
│  ├─ comprehensive_bet_generator.py    (Expand options)
│  ├─ bet_ranker_v4_improved.py        (LarlScore ranking)
│  ├─ game_status_checker.py            (Track results)
│  ├─ learning_engine.py                (Analyze performance)
│  ├─ update_adaptive_weights.py        (Update weights)
│  └─ dashboard_server_cache_fixed.py   (Flask backend)
│
├─ DATA FILES
│  ├─ active_bets.json                  (Today's picks - 135 options)
│  ├─ ranked_bets.json                  (Top 10 ranked - MAIN)
│  ├─ ranked_bets_2026-02-17.json       (Dated archive)
│  ├─ completed_bets_2026-02-17.json    (Today's results)
│  ├─ completed_bets_2026-02-16.json    (Yesterday's results)
│  ├─ completed_bets_2026-02-15.json    (Historical)
│  ├─ adaptive_weights.json             (Learned multipliers)
│  ├─ learning_insights.json            (Performance analysis)
│  └─ bet_tracker_input.json            (Tracking metadata)
│
├─ FRONTEND
│  ├─ templates/
│  │  └─ index.html                     (Dashboard page)
│  └─ static/
│     ├─ script_v3.js                   (JavaScript frontend)
│     └─ style.css                      (Styling)
│
├─ DOCS
│  ├─ MEMORY.md                         (Long-term memory)
│  ├─ LARLESCORE_DAILY_IMPROVEMENT.md   (Sword's docs)
│  ├─ SESSION_SUMMARY_2026-02-17.md     (Today's summary)
│  └─ SYSTEM_ARCHITECTURE.md            (This file)
│
└─ UTILITIES
   ├─ cache_manager.py                  (Caching layer)
   ├─ data_integrity_audit_v2.py        (Verification)
   └─ smart_edge_calculator.py          (Edge calculation)
```

---

## Database Schema

### active_bets.json
```json
{
  "date": "2026-02-17",
  "timestamp": "ISO-8601",
  "total_picks": 135,
  "bets": [
    {
      "game": "Team A @ Team B",
      "sport": "🏀 NCAA Basketball",
      "bet_type": "SPREAD|TOTAL|MONEYLINE",
      "recommendation": "Team +5.5|OVER 155|Team (ML)",
      "confidence": 75,
      "edge": 5.0,
      "game_time": "06:00 PM EST",
      "reason": "Explanation...",
      "fanduel_line": "...",
      "bookmaker_source": "FanDuel"
    }
  ]
}
```

### ranked_bets.json
```json
{
  "timestamp": "ISO-8601",
  "larlescore_version": "4.0",
  "larlescore_formula": "...",
  "adaptive_weights": {...},
  "top_10": [
    {
      "rank": 1,
      "score": 24.5,
      "game": "Team A @ Team B",
      "bet_type": "TOTAL",
      "recommendation": "UNDER 159.5",
      "confidence": 61,
      "edge": 23.9,
      "full_bet": { ... }
    }
  ],
  "summary": {
    "top_10_avg_confidence": 67.5,
    "top_10_avg_edge": 16.0,
    "by_type": { "SPREAD": 5, "TOTAL": 5, "MONEYLINE": 0 }
  }
}
```

### completed_bets_2026-02-17.json
```json
{
  "date": "2026-02-17",
  "timestamp": "ISO-8601",
  "bets": [
    {
      "game": "Team A @ Team B",
      "bet_type": "SPREAD",
      "recommendation": "Team +5.5",
      "confidence": 75,
      "edge": 5.0,
      "result": "WIN|LOSS|PENDING",
      "away_score": 85,
      "home_score": 80,
      "final_score": "85-80",
      "result_updated_at": "ISO-8601"
    }
  ]
}
```

---

## Performance Metrics

### Expected Win Rates
- **Current (Feb 15-17):** 55.3% (21W-17L)
- **With v4.0 filtering:** 70-80% (estimated)
- **After 30 days learning:** 75-85% (convergence expected)
- **Target:** 80%+ (sustainable)

### Historical Data Points
- SPREAD wins: 63.6% (7W-4L)
- TOTAL wins: 40% (6W-9L)
- MONEYLINE wins: 0% (0W-3L)
- High conf + high edge wins: 80% (4W-1L)

---

## Security & Reliability

### File Integrity
- All JSON files backed up daily
- Git tracks changes (GitHub)
- Checksums verified on load

### Error Handling
- Try/catch on all API calls
- Fallback to cached data
- Graceful degradation

### Monitoring
- Dashboard health check every 15 min
- API response time tracked
- Game status logged

### Disaster Recovery
- All data in Git (version control)
- Railway auto-deployment from GitHub
- Local backups + cloud sync

---

## Improvement Path

### Short-term (Days)
- [ ] Monitor win rate (should be 70%+)
- [ ] Verify game tracking accuracy
- [ ] Check learning engine output

### Medium-term (Weeks)
- [ ] Refine confidence thresholds
- [ ] Test alternative edge formulas
- [ ] Add injury/weather factors

### Long-term (Months)
- [ ] Machine learning model integration
- [ ] Multi-sport expansion
- [ ] Real-time odds arbitrage

---

## Deployment Checklist

- [x] Code written and tested
- [x] Database schema finalized
- [x] Frontend built (HTML/CSS/JS)
- [x] Backend APIs working
- [x] Cron jobs configured
- [x] GitHub repo synced
- [x] Railway connected
- [ ] Documentation complete (subagent in progress)
- [ ] Dashboard live on Railway
- [x] System health verified

---

**Last Updated:** Feb 17, 2026 @ 12:00 PM EST  
**Version:** 4.0 (Production)  
**Status:** FULLY OPERATIONAL ✅
