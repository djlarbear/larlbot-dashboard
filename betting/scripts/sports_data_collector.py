#!/usr/bin/env python3
"""
LarlBot Multi-Sport Data Collector 🎰
Collects live data for NCAA, NBA, MLB, NFL, UFC, and Soccer
"""

import requests
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

class SportsDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.db_path = 'sports_betting.db'
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with tables for all sports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Games table - universal for all sports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                sport TEXT NOT NULL,
                date TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                spread REAL,
                total REAL,
                status TEXT,
                venue TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Team stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_stats (
                team_name TEXT,
                sport TEXT,
                stat_name TEXT,
                stat_value REAL,
                date TEXT,
                PRIMARY KEY (team_name, sport, stat_name, date)
            )
        ''')
        
        # Betting opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS betting_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                bet_type TEXT,
                predicted_value REAL,
                book_odds REAL,
                edge REAL,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")

    def get_espn_data(self, sport_code, league=None):
        """Get games and scores from ESPN's public API"""
        sport_endpoints = {
            'ncb': 'basketball/mens-college-basketball',  # NCAA Basketball
            'nba': 'basketball/nba',
            'mlb': 'baseball/mlb', 
            'nfl': 'football/nfl',
            'soccer': 'soccer'  # We'll add specific leagues
        }
        
        if sport_code not in sport_endpoints:
            print(f"❌ Unknown sport: {sport_code}")
            return None
            
        endpoint = sport_endpoints[sport_code]
        url = f"https://site.api.espn.com/apis/site/v2/sports/{endpoint}/scoreboard"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', []):
                game_data = self.parse_espn_game(event, sport_code)
                if game_data:
                    games.append(game_data)
                    
            print(f"📊 Collected {len(games)} {sport_code.upper()} games")
            return games
            
        except Exception as e:
            print(f"❌ Error fetching {sport_code} data: {e}")
            return []

    def parse_espn_game(self, event, sport):
        """Parse individual game from ESPN API response"""
        try:
            game_id = f"{sport}_{event['id']}"
            date = event['date']
            
            competitions = event['competitions'][0]
            competitors = competitions['competitors']
            
            # Home vs Away (ESPN sometimes flips this)
            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
            
            return {
                'id': game_id,
                'sport': sport,
                'date': date,
                'home_team': home_team['team']['displayName'],
                'away_team': away_team['team']['displayName'],
                'home_score': home_team.get('score', 0),
                'away_score': away_team.get('score', 0),
                'status': competitions.get('status', {}).get('type', {}).get('description', 'scheduled'),
                'venue': competitions.get('venue', {}).get('fullName', ''),
                # We'll add odds scraping later
                'spread': None,
                'total': None
            }
        except Exception as e:
            print(f"❌ Error parsing game: {e}")
            return None

    def collect_all_sports_data(self):
        """Collect data for all target sports"""
        print("🎰 Starting multi-sport data collection...")
        
        sports_to_collect = [
            ('ncb', 'NCAA Basketball'),
            ('nba', 'NBA'),
            ('mlb', 'MLB'),
            ('nfl', 'NFL')
        ]
        
        all_games = []
        
        for sport_code, sport_name in sports_to_collect:
            print(f"\n📡 Collecting {sport_name} data...")
            games = self.get_espn_data(sport_code)
            if games:
                all_games.extend(games)
                time.sleep(1)  # Be nice to ESPN's servers
        
        # Store in database
        if all_games:
            self.store_games(all_games)
            
        return all_games

    def store_games(self, games):
        """Store games in SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for game in games:
            cursor.execute('''
                INSERT OR REPLACE INTO games 
                (id, sport, date, home_team, away_team, home_score, away_score, 
                 spread, total, status, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game['id'], game['sport'], game['date'], game['home_team'],
                game['away_team'], game['home_score'], game['away_score'],
                game['spread'], game['total'], game['status'], game['venue']
            ))
        
        conn.commit()
        conn.close()
        print(f"💾 Stored {len(games)} games in database")

    def get_todays_games(self, sport=None):
        """Get today's games from database"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM games 
            WHERE date >= date('now') 
            AND date < date('now', '+1 day')
        """
        if sport:
            query += f" AND sport = '{sport}'"
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def run_collection(self):
        """Main collection runner"""
        print("🚀 LarlBot Sports Data Collection Started!")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        games = self.collect_all_sports_data()
        
        print(f"\n📈 Collection Summary:")
        print(f"   Total games collected: {len(games)}")
        
        # Show breakdown by sport
        if games:
            sports_count = {}
            for game in games:
                sport = game['sport']
                sports_count[sport] = sports_count.get(sport, 0) + 1
            
            for sport, count in sports_count.items():
                print(f"   {sport.upper()}: {count} games")
        
        return games

if __name__ == "__main__":
    collector = SportsDataCollector()
    collector.run_collection()