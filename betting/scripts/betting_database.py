#!/usr/bin/env python3
"""
Simple SQLite wrapper for betting data. Provides migration from existing JSON files
into a local SQLite database at ./betting.db. This is additive — JSON files remain
as the source of truth for now.
"""

import sqlite3
import json
import glob
import os
from datetime import datetime

DB_PATH = 'betting.db'
WORKSPACE = '.'

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS bets (
        id TEXT PRIMARY KEY,
        date TEXT,
        game TEXT,
        sport TEXT,
        bet_type TEXT,
        recommendation TEXT,
        edge REAL,
        confidence REAL,
        larlscore REAL,
        result TEXT,
        actual_score TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS team_stats (
        team_name TEXT,
        league TEXT,
        ppg REAL,
        opp_ppg REAL,
        mov REAL,
        home_ppg REAL,
        away_ppg REAL,
        recent_ppg_json TEXT,
        recent_margin_json TEXT,
        wins INTEGER,
        losses INTEGER,
        last_updated TEXT,
        PRIMARY KEY(team_name, league)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS weights (
        date TEXT,
        bet_type TEXT,
        weight REAL,
        tier TEXT,
        rationale TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_picks (
        date TEXT PRIMARY KEY,
        picks_json TEXT,
        top10_json TEXT
    );
    """
]

class BettingDB:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        for sql in CREATE_TABLES_SQL:
            cur.executescript(sql)
        self.conn.commit()

    # --- Bets ---
    def save_bet(self, bet):
        """Save or replace a bet record. Bet is a dict with matching keys."""
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO bets (id, date, game, sport, bet_type, recommendation, edge, confidence, larlscore, result, actual_score)
            VALUES (:id, :date, :game, :sport, :bet_type, :recommendation, :edge, :confidence, :larlscore, :result, :actual_score)
            """,
            {
                'id': bet.get('id') or f"{bet.get('date')}_{bet.get('game')}_{bet.get('bet_type')}",
                'date': bet.get('date'),
                'game': bet.get('game'),
                'sport': bet.get('sport'),
                'bet_type': bet.get('bet_type'),
                'recommendation': bet.get('recommendation'),
                'edge': bet.get('edge'),
                'confidence': bet.get('confidence'),
                'larlscore': bet.get('larlscore'),
                'result': bet.get('result'),
                'actual_score': bet.get('actual_score')
            }
        )
        self.conn.commit()

    def get_bets_by_date(self, date):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM bets WHERE date = ?", (date,))
        return [dict(r) for r in cur.fetchall()]

    # --- Team stats ---
    def save_team_stats(self, team_stats):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO team_stats (team_name, league, ppg, opp_ppg, mov, home_ppg, away_ppg, recent_ppg_json, recent_margin_json, wins, losses, last_updated)
            VALUES (:team_name, :league, :ppg, :opp_ppg, :mov, :home_ppg, :away_ppg, :recent_ppg_json, :recent_margin_json, :wins, :losses, :last_updated)
            """,
            {
                'team_name': team_stats.get('team_name'),
                'league': team_stats.get('league'),
                'ppg': team_stats.get('ppg'),
                'opp_ppg': team_stats.get('opp_ppg'),
                'mov': team_stats.get('mov'),
                'home_ppg': team_stats.get('home_ppg'),
                'away_ppg': team_stats.get('away_ppg'),
                'recent_ppg_json': json.dumps(team_stats.get('recent_ppg', [])),
                'recent_margin_json': json.dumps(team_stats.get('recent_margin', [])),
                'wins': team_stats.get('wins'),
                'losses': team_stats.get('losses'),
                'last_updated': team_stats.get('last_updated')
            }
        )
        self.conn.commit()

    def get_team_stats(self, team_name, league):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM team_stats WHERE team_name = ? AND league = ?", (team_name, league))
        row = cur.fetchone()
        return dict(row) if row else None

    # --- Weights ---
    def save_weight_entry(self, date, bet_type, weight, tier=None, rationale=None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO weights (date, bet_type, weight, tier, rationale) VALUES (?, ?, ?, ?, ?)",
            (date, bet_type, weight, tier, rationale)
        )
        self.conn.commit()

    def get_weights(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM weights ORDER BY date DESC")
        return [dict(r) for r in cur.fetchall()]

    # --- Daily picks ---
    def save_daily_picks(self, date, picks, top10=None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO daily_picks (date, picks_json, top10_json) VALUES (?, ?, ?)",
            (date, json.dumps(picks), json.dumps(top10) if top10 is not None else None)
        )
        self.conn.commit()

    def get_daily_picks(self, date):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM daily_picks WHERE date = ?", (date,))
        row = cur.fetchone()
        return dict(row) if row else None

    # --- Migration helpers ---
    def migrate_completed_bets(self, pattern='completed_bets_*.json'):
        files = glob.glob(os.path.join(WORKSPACE, pattern))
        count = 0
        for path in files:
            try:
                with open(path) as f:
                    data = json.load(f)
            except Exception:
                continue
            # Handle both list and dict-with-bets-key formats
            if isinstance(data, dict) and 'bets' in data:
                bets_list = data['bets']
            elif isinstance(data, list):
                bets_list = data
            else:
                bets_list = [data]
            for bet in bets_list:
                # Normalize keys
                bet_record = {
                    'id': bet.get('id') or bet.get('bet_id') or None,
                    'date': bet.get('date') or bet.get('day'),
                    'game': bet.get('game'),
                    'sport': bet.get('sport'),
                    'bet_type': bet.get('bet_type') or bet.get('type'),
                    'recommendation': bet.get('recommendation') or bet.get('pick'),
                    'edge': bet.get('edge'),
                    'confidence': bet.get('confidence'),
                    'larlscore': bet.get('larlscore'),
                    'result': bet.get('result'),
                    'actual_score': bet.get('actual_score')
                }
                self.save_bet(bet_record)
                count += 1
        return count

    def migrate_team_stats(self, filename='team_stats_cache.json'):
        path = os.path.join(WORKSPACE, filename)
        if not os.path.exists(path):
            return 0
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            return 0
        count = 0
        # Handle nested 'teams' key or flat dict
        teams = data.get('teams', data) if isinstance(data, dict) else data
        for team_name, stats in teams.items():
            # Some cache formats map team -> simple string or value; skip non-dict entries
            if not isinstance(stats, dict):
                continue
            record = {
                'team_name': team_name,
                'league': stats.get('league') or ('nba' if 'nba' in filename else 'ncaa'),
                'ppg': stats.get('ppg'),
                'opp_ppg': stats.get('opp_ppg'),
                'mov': stats.get('mov'),
                'home_ppg': stats.get('home_ppg'),
                'away_ppg': stats.get('away_ppg'),
                'recent_ppg': stats.get('recent_ppg', []),
                'recent_margin': stats.get('recent_margin', []),
                'wins': stats.get('wins'),
                'losses': stats.get('losses'),
                'last_updated': stats.get('last_updated')
            }
            self.save_team_stats(record)
            count += 1
        return count

    def migrate_adaptive_weights(self, filename='adaptive_weights.json'):
        path = os.path.join(WORKSPACE, filename)
        if not os.path.exists(path):
            return 0
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            return 0
        weights = data.get('weights', {})
        count = 0
        date = data.get('generated_at') or datetime.now().isoformat()
        for bet_type, meta in weights.items():
            weight = meta.get('weight')
            tier = meta.get('confidence_level') or meta.get('tier')
            rationale = meta.get('rationale')
            self.save_weight_entry(date, bet_type, weight, tier, rationale)
            count += 1
        return count


if __name__ == '__main__':
    db = BettingDB()
    print('Initialized DB at', db.path)

    migrated_bets = db.migrate_completed_bets()
    migrated_teams = db.migrate_team_stats('team_stats_cache.json')
    migrated_weights = db.migrate_adaptive_weights('adaptive_weights.json')

    print('Migration summary:')
    print('  bets imported:', migrated_bets)
    print('  team stats imported:', migrated_teams)
    print('  adaptive weights imported:', migrated_weights)
