# Implementation Roadmap - NCAA-API Score Integration

## Overview
Deploy NCAA-API for D1/D2/D3 score tracking within 48 hours.  
Add NAIA scraper within 2 weeks.

---

## PHASE 1: NCAA-API Integration (48 Hours)

### Step 1: Select Deployment Model (Recommendation: Public API)
- **Public API:** Zero setup, instant start
- **Self-hosted:** 2 hours setup, guaranteed uptime

**Recommendation:** Start with public API, migrate to self-hosted in Phase 3 if needed.

### Step 2: Build Score Fetcher Service
**File:** `score_fetcher.py`

```python
import requests
import json
from datetime import datetime
from typing import List, Dict

class NCAAScoreFetcher:
    def __init__(self, use_self_hosted=False, self_hosted_url=None):
        self.base_url = self_hosted_url or "https://ncaa-api.henrygd.me"
        
    def fetch_scores(self, date: str = None) -> Dict:
        """
        Fetch all games for a date across D1, D2, D3
        date format: YYYY-MM-DD
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        all_games = {}
        
        for division in ['d1', 'd2', 'd3']:
            try:
                response = requests.get(
                    f"{self.base_url}/scoreboard/basketball-men/{division}/{date}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    games = data.get('games', [])
                    
                    for game in games:
                        g = game['game']
                        game_id = g['gameID']
                        
                        all_games[game_id] = {
                            'division': division.upper(),
                            'away_team': g['away']['names']['short'],
                            'away_team_full': g['away']['names']['full'],
                            'home_team': g['home']['names']['short'],
                            'home_team_full': g['home']['names']['full'],
                            'away_score': int(g['away']['score']) if g['away']['score'] else None,
                            'home_score': int(g['home']['score']) if g['home']['score'] else None,
                            'game_state': g['gameState'],
                            'conference': g['home']['conferences'][0]['conferenceSeo'] if g['home']['conferences'] else None,
                            'start_time': g['startTime'],
                            'start_epoch': int(g['startTimeEpoch']),
                            'ncaa_url': f"https://www.ncaa.com{g['url']}",
                            'fetched_at': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                print(f"Error fetching {division}: {e}")
        
        return all_games
    
    def store_in_db(self, games: Dict, db_connection):
        """Store scores in PostgreSQL"""
        for game_id, game_data in games.items():
            db_connection.execute("""
                INSERT INTO ncaa_scores (
                    game_id, division, away_team, home_team,
                    away_score, home_score, game_state, conference
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id) DO UPDATE SET
                    away_score = EXCLUDED.away_score,
                    home_score = EXCLUDED.home_score,
                    game_state = EXCLUDED.game_state,
                    updated_at = NOW()
            """, (
                game_id, game_data['division'], game_data['away_team'],
                game_data['home_team'], game_data['away_score'],
                game_data['home_score'], game_data['game_state'],
                game_data['conference']
            ))
```

### Step 3: Database Schema
**File:** `schema.sql`

```sql
CREATE TABLE ncaa_scores (
    game_id VARCHAR(20) PRIMARY KEY,
    division VARCHAR(3),  -- D1, D2, D3
    away_team VARCHAR(100),
    away_team_full VARCHAR(200),
    home_team VARCHAR(100),
    home_team_full VARCHAR(200),
    away_score INT,
    home_score INT,
    game_state VARCHAR(20),  -- pre, live, final
    conference VARCHAR(50),
    start_time TIMESTAMP,
    ncaa_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Team name mapping (for matching to betting DB)
CREATE TABLE team_mappings (
    betting_db_name VARCHAR(100),
    ncaa_name VARCHAR(100),
    ncaa_full_name VARCHAR(200),
    division VARCHAR(3),
    confidence FLOAT,  -- 0.0-1.0
    PRIMARY KEY (betting_db_name, ncaa_name)
);

-- Score lookup history
CREATE TABLE score_lookups (
    lookup_id SERIAL PRIMARY KEY,
    bet_id VARCHAR(20),
    game_id VARCHAR(20),
    matched_at TIMESTAMP DEFAULT NOW(),
    match_confidence FLOAT,
    result VARCHAR(20)  -- away_win, home_win, tie, pending
);
```

### Step 4: Cron Job / Scheduled Task
**File:** `cron_score_updater.py`

```python
#!/usr/bin/env python3
"""
Runs every 2 hours during basketball season
Fetches latest scores and updates database
"""

import schedule
import time
from score_fetcher import NCAAScoreFetcher
from database import get_connection

def update_scores():
    """Main cron job"""
    fetcher = NCAAScoreFetcher()
    games = fetcher.fetch_scores()
    
    db = get_connection()
    fetcher.store_in_db(games, db)
    db.commit()
    
    print(f"[{datetime.now()}] Updated {len(games)} games")

# Schedule: Run every 2 hours from 10 AM to 11 PM
schedule.every().day.at("10:00").do(update_scores)
schedule.every().day.at("12:00").do(update_scores)
schedule.every().day.at("14:00").do(update_scores)
schedule.every().day.at("16:00").do(update_scores)
schedule.every().day.at("18:00").do(update_scores)
schedule.every().day.at("20:00").do(update_scores)
schedule.every().day.at("22:00").do(update_scores)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
```

### Step 5: Integration with Betting System
**File:** `score_resolver.py`

```python
class BetScoreResolver:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def resolve_pending_bets(self, bet_ids: List[str] = None):
        """
        Match pending bets to NCAA scores
        Returns: {bet_id: {'status': 'resolved'/'unresolved', 'result': 'win'/'loss'/'push'}}
        """
        
        # Get pending bets
        query = "SELECT * FROM bets WHERE status = 'PENDING'"
        if bet_ids:
            query += f" AND bet_id IN ({','.join(['%s']*len(bet_ids))})"
        
        bets = self.db.execute(query, bet_ids or []).fetchall()
        results = {}
        
        for bet in bets:
            # Try to match away team
            away_match = self._match_team_name(bet['away_team'])
            home_match = self._match_team_name(bet['home_team'])
            
            if away_match and home_match:
                # Find game in scores table
                score = self.db.execute("""
                    SELECT * FROM ncaa_scores
                    WHERE away_team = %s AND home_team = %s
                    AND game_state = 'final'
                    ORDER BY created_at DESC LIMIT 1
                """, (away_match, home_match)).fetchone()
                
                if score and score['game_state'] == 'final':
                    # Determine winner
                    if score['away_score'] > score['home_score']:
                        result = 'away_win'
                    elif score['home_score'] > score['away_score']:
                        result = 'home_win'
                    else:
                        result = 'push'
                    
                    results[bet['bet_id']] = {
                        'status': 'resolved',
                        'result': result,
                        'game_id': score['game_id'],
                        'score': f"{score['away_score']}-{score['home_score']}"
                    }
                else:
                    results[bet['bet_id']] = {
                        'status': 'unresolved',
                        'reason': 'game_not_final'
                    }
            else:
                results[bet['bet_id']] = {
                    'status': 'unresolved',
                    'reason': 'team_match_failed'
                }
        
        return results
    
    def _match_team_name(self, betting_name: str, threshold=0.85):
        """
        Match team name from betting DB to NCAA DB
        Uses: exact match > confidence score > no match
        """
        
        # Exact match first
        exact = self.db.execute(
            "SELECT ncaa_name FROM team_mappings WHERE betting_db_name = %s",
            (betting_name,)
        ).fetchone()
        
        if exact:
            return exact['ncaa_name']
        
        # Fuzzy match second
        from difflib import SequenceMatcher
        
        candidates = self.db.execute(
            "SELECT ncaa_name, ncaa_full_name FROM ncaa_scores GROUP BY ncaa_name"
        ).fetchall()
        
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            score1 = SequenceMatcher(None, betting_name, candidate['ncaa_name']).ratio()
            score2 = SequenceMatcher(None, betting_name, candidate['ncaa_full_name']).ratio()
            match_score = max(score1, score2)
            
            if match_score > best_score and match_score >= threshold:
                best_score = match_score
                best_match = candidate['ncaa_name']
        
        return best_match
```

### Step 6: Testing
**File:** `test_score_integration.py`

```python
import unittest
from score_fetcher import NCAAScoreFetcher

class TestScoreFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = NCAAScoreFetcher()
    
    def test_fetch_scores(self):
        """Test fetching today's scores"""
        scores = self.fetcher.fetch_scores()
        self.assertIsInstance(scores, dict)
        self.assertGreater(len(scores), 0)  # Should have games
    
    def test_division_coverage(self):
        """Test D1, D2, D3 all have data"""
        for div in ['d1', 'd2', 'd3']:
            # Verify endpoint works
            response = requests.get(
                f"{self.fetcher.base_url}/scoreboard/basketball-men/{div}/2026-02-17"
            )
            self.assertEqual(response.status_code, 200)
    
    def test_game_data_structure(self):
        """Test game data has required fields"""
        scores = self.fetcher.fetch_scores()
        game = list(scores.values())[0]
        
        required = ['away_team', 'home_team', 'game_state', 'division']
        for field in required:
            self.assertIn(field, game)
```

### Step 7: Deployment Checklist
- [ ] Database schema created
- [ ] `score_fetcher.py` tested
- [ ] `score_resolver.py` tested
- [ ] Cron job configured
- [ ] Team name mappings populated (initial set)
- [ ] Feb 16 scores backfilled
- [ ] Pending bets resolved
- [ ] Monitoring alerts configured

---

## PHASE 2: NAIA Scraper (Week 2)

### Implementation
1. Build Selenium scraper for PrestoSports
2. Test selectors (verify they don't change daily)
3. Add to cron rotation (evening updates)
4. Merge with NCAA-API data
5. Extend team_mappings for NAIA teams

### Expected Effort
- Development: 3 days
- Testing: 2 days
- Maintenance: 2-4 hours/month

---

## PHASE 3: Redundancy (Month 2)

### If NCAA-API becomes unavailable:
- Fallback to espn.com scraping for D1
- Manual NCAA.com lookup for D2/D3
- Alert ops team

---

## Cost Summary

| Component | Cost | Timeline |
|-----------|------|----------|
| NCAA-API (public) | $0 | Immediate |
| Development (Phase 1) | 40 hours engineer time | 2 days |
| Database (cloud) | $10-20/month | Immediate |
| NAIA scraper (Phase 2) | 40 hours engineer time | 2 weeks |
| Maintenance (ongoing) | 2-4 hours/month | Continuous |
| **Total Year 1** | ~$150 + 1 engineer-month | 2 weeks |

vs.

| Component | Cost |
|-----------|------|
| SportsDataIO API | $500-2000/month |
| Manual data entry | 10 hours/week (~$300/week) |

---

## Go-Live Timeline

**Today:** Approve plan  
**Tomorrow:** Start Phase 1 development  
**Day 3:** Deploy and test  
**Day 4:** Backfill Feb 16 scores, resolve PENDING bets  
**Day 5+:** Monitor and adjust  
**Week 2:** NAIA scraper development  
**Week 3:** NAIA deployment  

---

## Success Metrics

- [ ] 100% of D1/D2/D3 games covered within 2 hours of final
- [ ] Team name matching >95% automated
- [ ] NAIA coverage added within 2 weeks
- [ ] 0 API downtime in first month
- [ ] Feb 16 bets resolved retroactively

---

**Questions? Ask before we commit.**  
**Ready to start? We can go today.**
