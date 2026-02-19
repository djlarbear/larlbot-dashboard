#!/usr/bin/env python3
"""
LarlBot Bet Results Tracker 🎰
Automatically tracks value bet results and performance
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests
from sports_data_collector import SportsDataCollector

class BetResultsTracker:
    def __init__(self):
        self.db_path = 'sports_betting.db'
        self.collector = SportsDataCollector()
        self.init_results_table()
    
    def init_results_table(self):
        """Initialize bet results tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bet_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                matchup TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                bet_recommendation TEXT NOT NULL,
                predicted_edge REAL NOT NULL,
                confidence REAL NOT NULL,
                predicted_spread REAL,
                market_spread REAL,
                predicted_total REAL,
                market_total REAL,
                final_home_score INTEGER,
                final_away_score INTEGER,
                bet_result TEXT,
                actual_margin REAL,
                actual_total REAL,
                value_was_correct BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settled_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Bet results tracking table initialized")
    
    def record_value_bet(self, bet_data):
        """Record a value bet for future tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Parse bet recommendation
        bet_recommendation = self.generate_bet_recommendation(bet_data)
        
        # Handle different bet types safely
        predicted_spread = bet_data['prediction'].get('predicted_spread')
        market_spread = bet_data['market'].get('market_spread')
        predicted_total = bet_data['prediction'].get('predicted_total')
        
        # Handle player props vs game bets differently
        if bet_data['bet_type'] == 'player_prop':
            market_total = bet_data['market'].get('market_line')  # Player props use market_line
        else:
            market_total = bet_data['market'].get('market_total')  # Game bets use market_total
        
        cursor.execute('''
            INSERT OR REPLACE INTO bet_results 
            (game_id, matchup, bet_type, bet_recommendation, predicted_edge, confidence,
             predicted_spread, market_spread, predicted_total, market_total, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bet_data['game_id'],
            bet_data['matchup'], 
            bet_data['bet_type'],
            bet_recommendation,
            bet_data['edge'],
            bet_data['confidence'],
            predicted_spread,
            market_spread,
            predicted_total,
            market_total,
            f"Recorded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📝 Recorded value bet: {bet_recommendation} (ID: {bet_id})")
        return bet_id
    
    def generate_bet_recommendation(self, bet_data):
        """Generate human-readable bet recommendation"""
        matchup = bet_data['matchup']
        
        if bet_data['bet_type'] == 'player_prop':
            # Handle player props
            prop_details = bet_data.get('prop_details', {})
            return prop_details.get('recommendation', 'PLAYER PROP BET')
        
        if ' @ ' in matchup:
            away_team, home_team = matchup.split(' @ ')
        else:
            away_team, home_team = matchup.split(' vs ')
        
        if bet_data['bet_type'] == 'spread':
            market_line = bet_data['market']['market_spread']
            our_line = bet_data['prediction']['predicted_spread']
            
            if our_line > market_line:
                return f"BET: {home_team} {market_line:+.1f}"
            else:
                return f"BET: {away_team} {-market_line:+.1f}"
        else:  # total bet
            market_total = bet_data['market']['market_total']
            our_total = bet_data['prediction']['predicted_total']
            
            if our_total > market_total:
                return f"BET: OVER {market_total:.1f}"
            else:
                return f"BET: UNDER {market_total:.1f}"
    
    def check_game_results(self):
        """Check for completed games and settle bets"""
        print("🔍 Checking for completed games...")
        
        # Get all unsettled bets
        conn = sqlite3.connect(self.db_path)
        unsettled_query = """
            SELECT * FROM bet_results 
            WHERE bet_result IS NULL 
            AND created_at >= date('now', '-7 days')
            ORDER BY created_at DESC
        """
        
        unsettled_bets = pd.read_sql_query(unsettled_query, conn)
        
        if unsettled_bets.empty:
            print("📋 No unsettled bets to check")
            return
        
        print(f"📊 Found {len(unsettled_bets)} unsettled bets")
        settled_count = 0
        
        for _, bet in unsettled_bets.iterrows():
            game_result = self.get_game_result(bet['game_id'])
            
            if game_result:
                self.settle_bet(bet['id'], game_result)
                settled_count += 1
        
        conn.close()
        print(f"✅ Settled {settled_count} bets")
        
        if settled_count > 0:
            self.print_performance_summary()
    
    def get_game_result(self, game_id):
        """Get final score for a completed game"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT home_team, away_team, home_score, away_score, status 
            FROM games WHERE id = ?
        """, (game_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[4] and 'final' in result[4].lower():
            return {
                'home_team': result[0],
                'away_team': result[1],
                'home_score': result[2],
                'away_score': result[3],
                'status': result[4]
            }
        
        return None
    
    def settle_bet(self, bet_id, game_result):
        """Settle a completed bet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get bet details
        cursor.execute("SELECT * FROM bet_results WHERE id = ?", (bet_id,))
        bet = cursor.fetchone()
        
        if not bet:
            return
        
        home_score = game_result['home_score']
        away_score = game_result['away_score']
        actual_margin = home_score - away_score  # Positive = home team won
        actual_total = home_score + away_score
        
        # Determine bet result
        bet_result = self.calculate_bet_result(bet, actual_margin, actual_total)
        
        # Check if our value assessment was correct
        value_correct = self.was_value_correct(bet, actual_margin, actual_total)
        
        # Update database
        cursor.execute('''
            UPDATE bet_results 
            SET final_home_score = ?, final_away_score = ?, bet_result = ?, 
                actual_margin = ?, actual_total = ?, value_was_correct = ?,
                settled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (home_score, away_score, bet_result, actual_margin, actual_total, 
              value_correct, bet_id))
        
        conn.commit()
        conn.close()
        
        result_emoji = "✅" if bet_result == "WIN" else "❌" if bet_result == "LOSS" else "⚖️"
        print(f"{result_emoji} Settled bet {bet_id}: {bet_result}")
    
    def calculate_bet_result(self, bet, actual_margin, actual_total):
        """Calculate if bet won, lost, or pushed"""
        bet_type = bet[3]  # bet_type column
        bet_recommendation = bet[4]  # bet_recommendation column
        
        if bet_type == 'spread':
            # Parse spread from recommendation
            if '+' in bet_recommendation:
                spread = float(bet_recommendation.split('+')[1])
                # Away team bet - they need to lose by less than spread
                return "WIN" if actual_margin < spread else "LOSS"
            else:
                spread = float(bet_recommendation.split('-')[1]) 
                # Home team bet - they need to win by more than spread
                return "WIN" if actual_margin > spread else "LOSS"
        
        else:  # total bet
            if 'OVER' in bet_recommendation:
                total = float(bet_recommendation.split('OVER ')[1])
                return "WIN" if actual_total > total else "LOSS"
            else:
                total = float(bet_recommendation.split('UNDER ')[1])
                return "WIN" if actual_total < total else "LOSS"
    
    def was_value_correct(self, bet, actual_margin, actual_total):
        """Check if our value assessment was correct"""
        predicted_spread = bet[7]  # predicted_spread
        predicted_total = bet[9]   # predicted_total
        
        if bet[3] == 'spread':  # bet_type
            # Was our spread prediction closer than market?
            market_error = abs(bet[8] - actual_margin)  # market_spread vs actual
            our_error = abs(predicted_spread - actual_margin)
            return our_error < market_error
        else:
            # Was our total prediction closer than market?  
            market_error = abs(bet[10] - actual_total)  # market_total vs actual
            our_error = abs(predicted_total - actual_total)
            return our_error < market_error
    
    def print_performance_summary(self):
        """Print betting performance summary"""
        conn = sqlite3.connect(self.db_path)
        
        # Get settled bets performance
        query = """
            SELECT 
                COUNT(*) as total_bets,
                SUM(CASE WHEN bet_result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN bet_result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN bet_result = 'PUSH' THEN 1 ELSE 0 END) as pushes,
                AVG(predicted_edge) as avg_edge,
                AVG(CASE WHEN value_was_correct = 1 THEN 1.0 ELSE 0.0 END) as value_accuracy
            FROM bet_results 
            WHERE bet_result IS NOT NULL
        """
        
        results = pd.read_sql_query(query, conn)
        conn.close()
        
        if not results.empty and results.iloc[0]['total_bets'] > 0:
            row = results.iloc[0]
            win_rate = (row['wins'] / row['total_bets']) * 100
            
            print(f"\n🎰 BETTING PERFORMANCE SUMMARY")
            print(f"=" * 50)
            print(f"📊 Total Bets: {row['total_bets']}")
            print(f"✅ Wins: {row['wins']}")
            print(f"❌ Losses: {row['losses']}")
            print(f"⚖️ Pushes: {row['pushes']}")
            print(f"🎯 Win Rate: {win_rate:.1f}%")
            print(f"📈 Avg Edge: {row['avg_edge']:.1f} points")
            print(f"🔮 Value Accuracy: {row['value_accuracy']*100:.1f}%")

if __name__ == "__main__":
    tracker = BetResultsTracker()
    tracker.check_game_results()