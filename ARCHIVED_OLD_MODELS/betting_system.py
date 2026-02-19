#!/usr/bin/env python3
"""
LarlBot Master Sports Betting System 🎰
Complete automated betting system for multiple sports
"""

import sys
import subprocess
import time
from datetime import datetime
from sports_data_collector import SportsDataCollector
from betting_analyzer import BettingAnalyzer  
from odds_collector import OddsCollector
import argparse

class BettingSystem:
    def __init__(self):
        self.data_collector = SportsDataCollector()
        self.odds_collector = OddsCollector()  
        self.analyzer = BettingAnalyzer()
        
    def collect_data(self):
        """Collect all sports data and odds"""
        print("🎰 LarlBot Betting System - Data Collection")
        print("=" * 50)
        
        # Collect game data from ESPN
        print("📡 Collecting sports data...")
        games = self.data_collector.collect_all_sports_data()
        
        # Collect odds data
        print("\n💰 Collecting odds data...")  
        odds = self.odds_collector.collect_all_odds()
        
        return games, odds
    
    def find_opportunities(self, confidence_threshold=0.4, edge_threshold=1.5):
        """Find betting opportunities"""
        print("\n🎯 Analyzing betting opportunities...")
        print("-" * 50)
        
        value_bets = self.analyzer.find_value_bets(
            confidence_threshold=confidence_threshold,
            edge_threshold=edge_threshold
        )
        
        return value_bets
    
    def run_full_analysis(self):
        """Complete analysis pipeline"""
        print(f"🚀 Starting Full Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Collect data
        games, odds = self.collect_data()
        
        # Step 2: Find opportunities
        value_bets = self.find_opportunities()
        
        # Step 3: Display results
        self.display_summary(games, odds, value_bets)
        
        return value_bets
    
    def display_summary(self, games, odds, value_bets):
        """Display analysis summary"""
        print("\n" + "="*60)
        print("🎰 LARLBOT BETTING SYSTEM SUMMARY")
        print("="*60)
        
        print(f"📊 Data Collection:")
        print(f"   • Games found: {len(games) if games else 0}")
        print(f"   • Sports covered: NBA, NCAA, MLB, NFL")
        print(f"   • Odds sources: Mock data (add real API key for live odds)")
        
        print(f"\n💎 Value Opportunities:")
        if value_bets:
            print(f"   • {len(value_bets)} value bets identified")
            print(f"   • Average edge: {sum(bet['edge'] for bet in value_bets) / len(value_bets):.1f} points")
            print(f"   • Best opportunity: {max(value_bets, key=lambda x: x['edge'])['matchup']}")
            
            print(f"\n🎯 Recommended Actions:")
            for i, bet in enumerate(value_bets[:3], 1):  # Top 3
                confidence_text = "🔥 HIGH" if bet['confidence'] > 0.6 else "⚡ MED" if bet['confidence'] > 0.4 else "💡 LOW"
                print(f"   {i}. {bet['matchup']}")
                print(f"      • Type: {bet['bet_type'].upper()}, Edge: {bet['edge']:.1f}pts, {confidence_text}")
        else:
            print("   • No value bets found with current criteria")
            print("   • Consider lowering thresholds or waiting for more games")
        
        print(f"\n⚙️  Next Steps:")
        print(f"   • Add real odds API key for live market data")  
        print(f"   • Launch dashboard: python betting_system.py --dashboard")
        print(f"   • Set up automated monitoring with cron jobs")
        print(f"   • Track bet performance for model improvement")
    
    def launch_dashboard(self):
        """Launch Streamlit dashboard"""
        print("🖥️  Launching betting dashboard...")
        print("   Dashboard will open in your browser automatically")
        print("   Use Ctrl+C to stop the dashboard")
        
        try:
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", 
                "betting_dashboard.py", 
                "--server.port", "8502",
                "--server.address", "localhost"
            ])
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")
    
    def monitor_mode(self, interval_minutes=30):
        """Continuous monitoring mode"""
        print(f"📡 Starting continuous monitoring (every {interval_minutes} minutes)")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Running analysis...")
                
                value_bets = self.run_full_analysis()
                
                if value_bets:
                    print(f"🚨 ALERT: {len(value_bets)} value bets found!")
                    # In production, send notifications here
                
                print(f"💤 Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description="LarlBot Sports Betting System 🎰")
    parser.add_argument("--dashboard", action="store_true", help="Launch web dashboard")
    parser.add_argument("--monitor", type=int, metavar="MINUTES", help="Continuous monitoring mode")
    parser.add_argument("--collect-only", action="store_true", help="Only collect data")
    parser.add_argument("--confidence", type=float, default=0.4, help="Minimum confidence threshold")
    parser.add_argument("--edge", type=float, default=1.5, help="Minimum edge threshold")
    
    args = parser.parse_args()
    
    system = BettingSystem()
    
    if args.dashboard:
        system.launch_dashboard()
    elif args.monitor:
        system.monitor_mode(args.monitor)
    elif args.collect_only:
        games, odds = system.collect_data()
        print(f"✅ Data collection complete: {len(games)} games")
    else:
        # Default: run full analysis
        system.run_full_analysis()

if __name__ == "__main__":
    main()