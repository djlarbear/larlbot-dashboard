# 🤝 Subagent Coordination & Knowledge Sharing

**All agents must work together, share context, and remember what they learn.**

## Agents & Responsibilities

### Sword 🗡️ (Betting Specialist)
**Responsibilities:**
- Daily pick generation (7 AM): 20-25 picks
- LarlScore ranking → select top 10
- Game status monitoring (every 15 min)
- ESPN score fetching (3 PM, 8 PM, 11 PM)
- Mark bets WIN/LOSS when games finish
- Learning loop (every 6h): Analyze wins/losses, adjust confidence

**Key Files:**
- `initialize_daily_bets.py` (generates picks, creates ranked_bets.json)
- `espn_score_fetcher.py` (fetches scores, marks WIN/LOSS)
- `learning_engine.py` (analyzes performance, updates thresholds)
- `game_status_checker.py` (monitors active games)

**Outputs:**
- `ranked_bets.json` - Has `top_10` array used by all
- `completed_bets_YYYY-MM-DD.json` - Win/loss records
- `learning_insights.json` - Calibration data

### Backend-Dev 🧠 (API/Data)
**Responsibilities:**
- Serve ONLY top 10 bets to frontend
- Aggregate stats from top 10 only
- Group previous results by date
- Preserve original game dates (not current date)
- Mark results WIN/LOSS from Sword's data

**Key Files:**
- `dashboard_server_cache_fixed.py` - Main API server
- Must read: `ranked_bets.json[top_10]` to filter what to serve

**Endpoints:**
- `/api/bets` - Return only active top 10
- `/api/stats` - Calculate from top 10 only
- `/api/previous-results` - Group by date, show top 10 only
- `/api/ranked-bets` - Return top_10 array

### Frontend-Dev 🎨 (UI/Display)
**Responsibilities:**
- Display only top 10 picks
- Color code by WIN/LOSS result (not confidence)
- Show correct dates in Previous Results
- Update when Backend updates
- 24-hour auto-refresh

**Key Files:**
- `templates/index.html` - Main UI
- `static/script_v3.js` - Dashboard logic, API calls

**Behavior:**
- GREEN = WIN
- RED = LOSS
- YELLOW = PENDING (awaiting ESPN scores)
- GRAY = Old date (show date, not current)

## Communication Flow

```
Sword Generates Picks
    ↓
    └→ Creates: ranked_bets.json[top_10]
    ↓
Backend Reads ranked_bets.json
    ↓
    └→ Serves: /api/bets (only top 10)
    ↓
Frontend Displays from /api/bets
    ↓
    └→ Shows: Only top 10 on dashboard
    ↓
Sword Fetches ESPN Scores
    ↓
    └→ Updates: completed_bets_*.json
    ↓
Backend Reads updated files
    ↓
    └→ Serves: /api/previous-results (top 10, correct dates)
    ↓
Frontend Refreshes display
    ↓
    └→ Shows: TOP 10 previous results, WIN/LOSS colors
```

## Information Sharing

### What Sword Must Tell Backend & Frontend
- "I just created `ranked_bets.json` with top 10"
- "I marked these games WIN/LOSS from ESPN scores"
- "My 6h learning cycle found SPREAD is 83% accurate"

### What Backend Must Tell Frontend
- "Here's the data from `/api/bets` - it's only top 10"
- "Previous results grouped by date with WIN/LOSS"
- "Stats now include data from all completed_bets files"

### What Frontend Must Tell Backend & Sword
- "I'm showing only top 10 on dashboard"
- "I'm using result field for colors, not confidence"
- "I need dates preserved from completed_bets files"

## Coordination Schedule

**Daily (7 AM EST):**
- Sword generates picks, creates ranked_bets.json[top_10]
- Backend picks up new ranked_bets.json, validates top_10 exists
- Frontend refreshes "Today's Bets" tab with new top 10

**Every 15 Minutes:**
- Sword monitors game status
- Backend/Frontend auto-refresh dashboard if games change

**Every 6 Hours:**
- Sword runs learning engine
- Updates confidence thresholds
- Logs insights to learning_insights.json

**3 PM, 8 PM, 11 PM EST:**
- Sword fetches ESPN scores
- Marks games WIN/LOSS in completed_bets files
- Backend picks up updates, recalculates stats
- Frontend refreshes Previous Results tab

## Failure Points & Prevention

### Problem: Dashboard Shows All 24 Bets
**Root:** Frontend not filtering to top 10
**Fix:** Backend ensures /api/bets returns only ranked_bets.json[top_10]
**Prevention:** Frontend code review - must verify top_10 array used

### Problem: Previous Results Show Wrong Date
**Root:** Using current date instead of game date from completed_bets
**Fix:** Backend preserves original date from file
**Prevention:** Sword ensures completed_bets files have correct date field

### Problem: All Bets Showing PENDING
**Root:** ESPN fetcher not running or not marking WIN/LOSS
**Fix:** Sword ensures espn_score_fetcher.py runs on schedule
**Prevention:** Cron jobs monitored, alerts on fetch failure

### Problem: Color-Coded by Confidence Not Result
**Root:** Frontend using wrong field for color logic
**Fix:** Frontend changed to use `result` field (WIN/LOSS) not confidence
**Prevention:** Frontend code review, test colors update when result changes

## Knowledge Base

All agents should read & understand:
1. `BETTING_ARCHITECTURE.md` - System design
2. `LARLESCORE_SYSTEM.md` - Ranking algorithm
3. `SUBAGENT_COORDINATION.md` (this file) - How to work together
4. `espn_score_fetcher.py` - How scores get marked
5. `dashboard_server_cache_fixed.py` - API structure

## Memory Persistence

If any agent or session discovers:
- A bug in the system
- A limitation in the workflow
- An improvement to the algorithm
- A failure mode we should prevent

**It MUST be:**
1. Documented in the memory files above
2. Communicated to other agents
3. Tested before deployment
4. Remembered in future sessions

## Future Improvements to Consider

- [ ] Auto-failover if ESPN API unavailable
- [ ] Manual override for result entry (if ESPN unavailable)
- [ ] A/B testing different LarlScore weights
- [ ] Confidence calibration by bet type
- [ ] Sharpe ratio optimization
- [ ] Real-time odds movement tracking
- [ ] DFS leverage scoring

All improvements must be coordinated through this process.
