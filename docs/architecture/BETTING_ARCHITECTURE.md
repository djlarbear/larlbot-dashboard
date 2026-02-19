# 🎯 BETTING SYSTEM ARCHITECTURE - TOP 10 ONLY

**CRITICAL RULE: We track and display ONLY the TOP 10 bets per day, ranked by LarlScore.**

## Daily Workflow

### 1. Generation Phase (7:00 AM EST)
- `initialize_daily_bets.py` generates 20-25 picks from market data
- Each pick gets:
  - Edge (points of advantage over spread)
  - Confidence (80-95% typical)
  - Bet type (SPREAD, TOTAL, MONEYLINE)
  - Reasoning and model analysis

### 2. Ranking Phase (7:00 AM EST - same job)
- All 20-25 picks fed into `BetRanker` 
- **LarlScore calculated for each pick:**
  ```
  LarlScore = (Confidence × Weight) + (Edge × EdgeWeight) + (HistoricalWinRate × TypeWeight)
  ```
- **TOP 10 selected** by LarlScore descending
- Stored in `ranked_bets.json` with `top_10` array

### 3. Tracking Phase (Real-time + 3x Daily ESPN Fetches)
- ONLY the 10 bets in `ranked_bets.json[top_10]` are tracked
- `game_status_checker.py` monitors these 10 games every 15 min
- `espn_score_fetcher.py` pulls final scores (3 PM, 8 PM, 11 PM EST)
- Results marked WIN/LOSS when games finish

### 4. Display Phase
- **Dashboard Today's Bets:** Active games from top 10 only
- **Dashboard Previous Results:** Completed games from top 10, grouped by date
- **Stats at top:** Win rate calculated from top 10 only (exclude PENDING)
- **Color coding:** GREEN (WIN), RED (LOSS), YELLOW (PENDING awaiting scores)

## File Structure

```
active_bets.json
├── date: "2026-02-17"
└── bets: [all 24 picks, full details]

ranked_bets.json
├── timestamp: "2026-02-17T07:00:00-05:00"
├── performance_stats: {...}
└── top_10: [
    {rank: 1, score: 150.33, game: "...", full_bet: {...}},
    {rank: 2, score: 148.97, game: "...", full_bet: {...}},
    ...
  ]

completed_bets_2026-02-16.json
├── date: "2026-02-16"
├── bets: [
    {game: "...", result: "WIN", final_score: "...", ...},
    {game: "...", result: "LOSS", final_score: "...", ...},
    {game: "...", result: "PENDING", ...}
  ]
└── last_updated: "2026-02-17T08:30:00-05:00"
```

## Dashboard Display Logic

### "Today's Bets" Tab
- **Data source:** `ranked_bets.json[top_10]` where `result` is not WIN/LOSS (active games)
- **Sort:** By rank (1-10)
- **Display:**
  - Game name
  - Recommendation (our pick)
  - Edge (confidence)
  - LarlScore
  - Status (NOT STARTED / IN PROGRESS / PENDING RESULT)

### "Previous Results" Tab
- **Data source:** All `completed_bets_*.json` files, filtered for games in top 10
- **Group by:** Date (newest first)
- **Display per bet:**
  - Game name
  - Recommendation
  - Result (WIN/LOSS with color)
  - Final score
  - Status indicator

### "Stats" At Top
- **Source:** `ranked_bets.json[top_10]` + `completed_bets_*.json` files
- **Calculation:** Only count bets with result in ['WIN', 'LOSS']
- **Exclude:** PENDING bets (awaiting ESPN scores)
- **Display:** "{wins}-{losses} ({win_rate}%)"

## Data Flow

```
Market Data → initialize_daily_bets (7 AM)
    ↓
20-25 Picks → BetRanker → LarlScore ranking
    ↓
TOP 10 → ranked_bets.json ← Dashboard reads this
    ↓
Game Status Checker (every 15 min)
    ↓
ESPN Fetcher (3 PM, 8 PM, 11 PM)
    ↓
completed_bets_YYYY-MM-DD.json (WIN/LOSS marked)
    ↓
Dashboard Previous Results (grouped by date)
```

## Critical Invariants

1. **Only top 10 get tracked** - No betting on outside 10
2. **Only top 10 on dashboard** - Never display all 24
3. **Date preservation** - Previous results show actual game date, not current date
4. **Status accuracy** - WIN/LOSS must be determined from ESPN scores, not displayed incorrectly
5. **Color logic** - GREEN/RED for results, not confidence-based colors
6. **Stats accuracy** - Only finalized bets count toward win rate

## When These Rules Broke (Feb 17 Morning)

1. Dashboard showed all 24 picks instead of top 10 ❌
2. Previous Results showed 2026-02-17 instead of 2026-02-16 ❌
3. No WIN/LOSS determination (all PENDING) ❌
4. Color-coded by confidence, not result status ❌

**Root cause:** Backend/Frontend weren't filtering to top 10, and previous results weren't preserving original game dates.

**Fixed by:** 
- Sword: Ensures `ranked_bets.json[top_10]` created correctly
- Backend: Filters all endpoints to return only top_10
- Frontend: Displays only top 10, uses result for colors, preserves dates
