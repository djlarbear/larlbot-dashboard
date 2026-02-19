# Multi-Sport Betting Model - Build Plan (Feb 18, 2026)

## Goal
All 4 sports (NCAA, NBA, NHL, NFL) generating picks by **end of day (5 PM EST)**

## Architecture

### Unified Data Flow
```
BallDontLie API
    ├─ NCAA Basketball
    ├─ NBA Basketball  
    ├─ NHL Hockey
    └─ NFL Football
        ↓
    Sport-Specific Fetchers
        ↓
    Sport-Specific Team Stats DB
        ↓
    Sport-Specific Pick Generator
        ↓
    Central Learning Engine (unified)
        ↓
    Dashboard (10 per sport + 10 combined)
```

### Phase Breakdown

**Phase 1: Architecture & Validation (30 min)**
- [ ] Verify BallDontLie API access
- [ ] Design sport metric mappings
- [ ] Plan unified learning schema

**Phase 2: Core Refactor (60 min)**
- [ ] Build universal score fetcher (BallDontLie)
- [ ] Extend learning engine for multi-sport
- [ ] Create sport config schema

**Phase 3: Sport Implementation (90 min)**
- [ ] NCAA Basketball (FAST - already working)
- [ ] NBA Basketball (FAST - similar to NCAA)
- [ ] NHL Hockey (MEDIUM - different metrics)
- [ ] NFL Football (MEDIUM - different metrics)

**Phase 4: Dashboard & Deployment (30 min)**
- [ ] Update dashboard for all sports
- [ ] Verify 10 per sport + 10 combined
- [ ] Deploy & test

## Metric Strategy

### Basketball (NCAA + NBA)
- Model: Pace × Efficiency
- Metrics: PPG, Pace, Offensive Efficiency, Defensive Efficiency
- Bet Types: SPREAD, TOTAL, MONEYLINE

### Hockey (NHL)
- Model: Shot-Based
- Metrics: Shots For, Shots Against, Save %, High-Danger Chances
- Bet Types: SPREAD, TOTAL (goals), MONEYLINE

### Football (NFL)
- Model: Yardage-Based
- Metrics: Yards/Game, Yards/Play, Passing Yards, Rushing Yards
- Bet Types: SPREAD, TOTAL, MONEYLINE

## Data Sources
- **Scores & Live Data:** BallDontLie API
- **Team Stats:** BallDontLie + ESPN scraping
- **Betting Lines:** BallDontLie (integrated)

## Timeline
- **14:00 EST:** Phase 1 complete
- **15:00 EST:** Phase 2 complete  
- **16:30 EST:** Phase 3 complete
- **17:00 EST:** Phase 4 complete + LIVE

## Success Criteria
✅ All 4 sports generating picks
✅ 10 bets per sport on dashboard
✅ 10 top bets across all sports
✅ Learning engine tracking all sports
✅ Games today (NBA, NHL) getting recommendations
