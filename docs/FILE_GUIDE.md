# File Guide - Betting System

## 🔑 Core Scripts (Active Production)

### Pick Generation
| File | Purpose |
|------|---------|
| `initialize_daily_bets.py` | **Main entry point** - Generates top 10 daily picks via LARLScore |
| `real_betting_model.py` | Core prediction model (TOTAL/SPREAD/ML edges + confidence) |
| `ncaa_total_predictor.py` | TOTAL prediction (PPG, pace, splits, recent form) |
| `ncaa_spread_predictor.py` | SPREAD prediction (strength diff, HCA, form) |
| `bet_ranker.py` | LARLScore formula + deduplication |

### Data & Stats
| File | Purpose |
|------|---------|
| `betting_database.py` | SQLite wrapper (bets, teams, weights tables) |
| `ncaa_team_stats_fetcher.py` | Fetch team stats from ESPN API |
| `ncaa_hybrid_score_fetcher.py` | Fetch game scores (NCAA API + fallbacks) |
| `team_stats_cache.json` | Cached stats for 362 NCAA teams |
| `nba_team_stats_cache.json` | Cached stats for 30 NBA teams |

### Results & Tracking
| File | Purpose |
|------|---------|
| `auto_result_tracker.py` | Fetch settled results from OddsAPI |
| `learning_engine.py` | Analyze wins/losses, update insights |
| `update_adaptive_weights.py` | Bayesian weight updates based on performance |

### Dashboard
| File | Purpose |
|------|---------|
| `dashboard_server_cache_fixed.py` | Flask server (localhost:5001) |
| `START_DASHBOARD.sh` | Dashboard startup script |

## 📁 Key Data Files

| File | Purpose | Location |
|------|---------|----------|
| `betting.db` | SQLite database (68 bets, 362 teams) | `/workspace/` |
| `ranked_bets.json` | Today's top 10 picks with LARLScores | `betting/data/` |
| `adaptive_weights.json` | Current bet type weights (TOTAL/SPREAD/ML) | `betting/data/` |
| `team_stats_cache.json` | NCAA team stats + recent form | `betting/data/` |
| `nba_team_stats_cache.json` | NBA team stats + recent form | `betting/data/` |

## 📋 Configuration

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `.env` (if exists) | API keys, secrets |

## 🗂️ Folder Structure

```
betting/
  ├── scripts/      # All Python betting scripts
  ├── data/         # JSON data files (picks, stats, bets)
  ├── models/       # ML models (.pkl files)
  └── logs/         # Log files

docs/
  ├── architecture/ # System design docs
  ├── sessions/     # Session summaries
  └── analysis/     # Audits and analysis reports

memory/
  # Daily session logs (2026-02-XX.md)
  # Topic-specific memory files

templates/
  # daily_summary.md
  # audit_checklist.md

scripts/
  # quick_status.sh
  # (other utility scripts)

archive/
  ├── old_scripts/  # Deprecated Python files
  ├── old_data/     # Old JSON backups
  └── old_docs/     # Outdated documentation
```

## 🔧 Utility Scripts

### Analysis
| File | Purpose |
|------|---------|
| `analyze_todays_bets.py` | Analyze current day's picks |
| `calculate_win_rates.py` | Calculate historical win rates |
| `comprehensive_outcome_analysis.py` | Deep dive on bet outcomes |

### Testing & POC
| File | Purpose |
|------|---------|
| `poc_espn_api.py` | ESPN API proof of concept |
| `poc_naia_scrape.py` | NAIA scraping proof of concept |

### Maintenance
| File | Purpose |
|------|---------|
| `fix_game_results.py` | Manual result correction |
| `smart_conflict_resolver.py` | Resolve data conflicts |
| `cache_manager.py` | Manage cached data |

## 🗑️ Deprecated Scripts (Archived)

These files are in `archive/old_scripts/` and should NOT be used:

- `generate_daily_picks.py` - OLD hardcoded Feb 14 script
- `bet_ranker_v4_improved.py` - Superseded by `bet_ranker.py`
- `auto_result_tracker_v2.py` - Use `auto_result_tracker.py` instead
- `adaptive_learning_v2.py` - Use `learning_engine.py` instead

## 🚨 Important Notes

1. **ALWAYS use `initialize_daily_bets.py`** - Not `generate_daily_picks.py`
2. **Score ALL picks before taking top 10** - Fixed bug on Feb 18
3. **Check adaptive weights before each run** - Ensures proper bet type weighting
4. **Git commit data files regularly** - Prevent data loss

## 📞 Script Dependencies

```
initialize_daily_bets.py
  └── bet_ranker.py
        └── real_betting_model.py
              ├── ncaa_total_predictor.py
              └── ncaa_spread_predictor.py

learning_engine.py
  └── betting_database.py
        └── betting.db

update_adaptive_weights.py
  └── betting_database.py
        └── betting.db
```

## 🔍 Finding Scripts

Use these commands to locate files:

```bash
# Find all Python scripts
find betting/scripts -name "*.py" -type f

# Find scripts by keyword
grep -l "LARLScore" betting/scripts/*.py

# Check script last modified time
ls -lt betting/scripts/*.py | head

# Search for function definitions
grep "def " betting/scripts/bet_ranker.py
```

## 📚 Related Documentation

- `docs/QUICK_START.md` - How to run the system
- `docs/CRON_SCHEDULE.md` - Automated job schedule
- `docs/architecture/BETTING_ARCHITECTURE.md` - System design
- `MEMORY.md` - Long-term system memory
- `memory/2026-02-XX.md` - Daily session logs
