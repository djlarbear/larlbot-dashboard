#!/usr/bin/env python3
"""
LarlBot Bet Tracker 🎰
Track bet performance and results
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

class BetTracker:
    def __init__(self):
        self.db_path = 'sports_betting.db'
        self.init_tracking_tables()
    
    def init_tracking_tables(self):
        """Initialize bet tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Placed bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS placed_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                bet_side TEXT NOT NULL,
                amount REAL NOT NULL,
                odds INTEGER NOT NULL,
                predicted_edge REAL,
                confidence REAL,
                bookmaker TEXT,
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                result TEXT,
                payout REAL,
                settled_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Performance tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_stats (
                date TEXT PRIMARY KEY,
                total_bets INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                pushes INTEGER DEFAULT 0,
                total_wagered REAL DEFAULT 0,
                total_returned REAL DEFAULT 0,
                roi REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table for monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                game_id TEXT,
                message TEXT NOT NULL,
                edge REAL,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Bet tracking tables initialized")
    
    def place_bet(self, game_id, bet_type, bet_side, amount, odds, edge, confidence, bookmaker="unknown", notes=""):
        """Record a placed bet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO placed_bets 
            (game_id, bet_type, bet_side, amount, odds, predicted_edge, confidence, bookmaker, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (game_id, bet_type, bet_side, amount, odds, edge, confidence, bookmaker, notes))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📝 Bet recorded: ID {bet_id}, {bet_type} {bet_side}, ${amount} @ {odds}")
        return bet_id
    
    def settle_bet(self, bet_id, result, payout):
        """Settle a completed bet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE placed_bets 
            SET result = ?, payout = ?, status = 'settled', settled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (result, payout, bet_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Bet {bet_id} settled: {result}, payout: ${payout}")
        self.update_performance_stats()
    
    def update_performance_stats(self):
        """Update daily performance statistics"""
        conn = sqlite3.connect(self.db_path)
        
        # Calculate today's stats
        today = datetime.now().strftime('%Y-%m-%d')
        
        query = '''
            SELECT 
                COUNT(*) as total_bets,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = 'push' THEN 1 ELSE 0 END) as pushes,
                SUM(amount) as total_wagered,
                SUM(COALESCE(payout, 0)) as total_returned
            FROM placed_bets 
            WHERE DATE(placed_at) = ?
        '''
        
        stats = pd.read_sql_query(query, conn, params=[today])
        
        if not stats.empty and stats.iloc[0]['total_bets'] > 0:
            row = stats.iloc[0]
            roi = ((row['total_returned'] - row['total_wagered']) / row['total_wagered'] * 100) if row['total_wagered'] > 0 else 0
            
            # Insert or update today's stats
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO performance_stats 
                (date, total_bets, wins, losses, pushes, total_wagered, total_returned, roi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (today, row['total_bets'], row['wins'], row['losses'], row['pushes'], 
                  row['total_wagered'], row['total_returned'], roi))
            
            conn.commit()
        
        conn.close()
    
    def log_alert(self, alert_type, message, game_id=None, edge=None, confidence=None):
        """Log an alert for monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (alert_type, game_id, message, edge, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (alert_type, game_id, message, edge, confidence))
        
        conn.commit()
        conn.close()
        print(f"🚨 Alert logged: {alert_type} - {message}")
    
    def get_performance_summary(self, days=30):
        """Get performance summary for last N days"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM performance_stats 
            WHERE date >= date('now', '-{} days')
            ORDER BY date DESC
        '''.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {
                'total_bets': 0,
                'win_rate': 0,
                'total_wagered': 0,
                'total_profit': 0,
                'roi': 0
            }
        
        total_bets = df['total_bets'].sum()
        total_wins = df['wins'].sum()
        total_wagered = df['total_wagered'].sum()
        total_returned = df['total_returned'].sum()
        
        return {
            'total_bets': total_bets,
            'win_rate': (total_wins / total_bets * 100) if total_bets > 0 else 0,
            'total_wagered': total_wagered,
            'total_profit': total_returned - total_wagered,
            'roi': ((total_returned - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0,
            'daily_stats': df.to_dict('records')
        }
    
    def get_pending_bets(self):
        """Get all pending bets that need settlement"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM placed_bets 
            WHERE status = 'pending'
            ORDER BY placed_at DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_recent_alerts(self, limit=10):
        """Get recent alerts"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM alerts 
            ORDER BY created_at DESC 
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        return df

if __name__ == "__main__":
    # Test the tracker
    tracker = BetTracker()
    
    # Example bet
    bet_id = tracker.place_bet(
        game_id="ncb_test_123",
        bet_type="spread", 
        bet_side="Michigan State +2.5",
        amount=50,
        odds=-110,
        edge=3.2,
        confidence=0.75,
        bookmaker="fanduel",
        notes="Strong value bet"
    )
    
    # Example settlement
    tracker.settle_bet(bet_id, "win", 95.45)
    
    # Show performance
    perf = tracker.get_performance_summary()
    print(f"\n📊 Performance Summary:")
    print(f"   Win Rate: {perf['win_rate']:.1f}%")
    print(f"   ROI: {perf['roi']:.1f}%")
    print(f"   Profit: ${perf['total_profit']:.2f}")