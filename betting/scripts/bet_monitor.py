#!/usr/bin/env python3
"""
LarlBot Automated Betting Monitor 🎰
Continuous monitoring for value bets and alerts
"""

import time
import schedule
from datetime import datetime, timedelta
from betting_system import BettingSystem
from bet_tracker import BetTracker
import json

class BettingMonitor:
    def __init__(self):
        self.betting_system = BettingSystem()
        self.tracker = BetTracker()
        self.last_check = None
        self.alert_thresholds = {
            'high_confidence': 0.7,
            'high_edge': 3.0,
            'max_daily_alerts': 20
        }
        self.daily_alert_count = 0
        
    def check_for_opportunities(self):
        """Check for new betting opportunities"""
        print(f"\n🔍 Automated Check - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        try:
            # Run analysis
            value_bets = self.betting_system.find_opportunities(
                confidence_threshold=0.4,
                edge_threshold=1.0
            )
            
            # Process new opportunities
            new_alerts = 0
            for bet in value_bets:
                alert_sent = self.process_value_bet(bet)
                if alert_sent:
                    new_alerts += 1
            
            # Log check result
            self.tracker.log_alert(
                alert_type="system_check",
                message=f"Found {len(value_bets)} opportunities, {new_alerts} new alerts",
                edge=sum(b['edge'] for b in value_bets) / len(value_bets) if value_bets else 0
            )
            
            print(f"✅ Check complete: {len(value_bets)} opportunities, {new_alerts} alerts")
            self.last_check = datetime.now()
            
        except Exception as e:
            error_msg = f"Monitor check failed: {e}"
            print(f"❌ {error_msg}")
            self.tracker.log_alert("system_error", error_msg)
    
    def process_value_bet(self, bet):
        """Process a value bet and determine if alert is needed"""
        confidence = bet['confidence']
        edge = bet['edge']
        
        # Check if this is alert-worthy
        is_high_confidence = confidence >= self.alert_thresholds['high_confidence']
        is_high_edge = edge >= self.alert_thresholds['high_edge']
        
        if (is_high_confidence or is_high_edge) and self.daily_alert_count < self.alert_thresholds['max_daily_alerts']:
            
            # Create alert message
            alert_type = "high_value_bet"
            message = f"🎰 VALUE BET: {bet['matchup']} - {bet['bet_type'].upper()} (Edge: {edge:.1f}pts, Conf: {confidence:.1%})"
            
            # Log the alert
            self.tracker.log_alert(
                alert_type=alert_type,
                game_id=bet['game_id'],
                message=message,
                edge=edge,
                confidence=confidence
            )
            
            # Send notification (could extend this to email, SMS, etc.)
            self.send_notification(message, bet)
            
            self.daily_alert_count += 1
            return True
        
        return False
    
    def send_notification(self, message, bet_details):
        """Send notification (extend this for email/SMS)"""
        print(f"🚨 ALERT: {message}")
        
        # Could add integrations here:
        # - Email via SMTP
        # - SMS via Twilio  
        # - Slack/Discord webhook
        # - Push notifications
        
        # For now, just log to console and database
        print(f"   Game: {bet_details['date']}")
        print(f"   Recommended: Consider {bet_details['bet_type']} bet")
    
    def check_pending_bets(self):
        """Check if any pending bets can be settled"""
        pending = self.tracker.get_pending_bets()
        
        if pending.empty:
            print("📋 No pending bets to check")
            return
        
        print(f"📋 Checking {len(pending)} pending bets for settlement...")
        
        for _, bet in pending.iterrows():
            # In a full system, you'd check game results and settle automatically
            # For now, just log that we should check
            print(f"   Bet {bet['id']}: {bet['bet_side']} - needs manual settlement")
    
    def daily_reset(self):
        """Reset daily counters and stats"""
        print("🌅 Daily reset - clearing counters")
        self.daily_alert_count = 0
        
        # Update performance stats
        self.tracker.update_performance_stats()
        
        # Show yesterday's performance
        perf = self.tracker.get_performance_summary(days=1)
        if perf['total_bets'] > 0:
            print(f"📊 Yesterday: {perf['total_bets']} bets, {perf['win_rate']:.1f}% win rate, {perf['roi']:.1f}% ROI")
    
    def setup_schedule(self):
        """Set up automated checking schedule"""
        # Check for opportunities every 15 minutes during active hours
        schedule.every(15).minutes.do(self.check_for_opportunities)
        
        # Check pending bets every hour
        schedule.every().hour.do(self.check_pending_bets)
        
        # Daily reset at midnight
        schedule.every().day.at("00:01").do(self.daily_reset)
        
        # More frequent checks during peak betting hours
        peak_times = ["10:00", "14:00", "18:00", "21:00"]
        for time_str in peak_times:
            schedule.every().day.at(time_str).do(self.check_for_opportunities)
        
        print("⏰ Schedule configured:")
        print("   • Every 15 minutes: Check for value bets")
        print("   • Every hour: Check pending bets") 
        print("   • Peak times: Extra checks at 10am, 2pm, 6pm, 9pm")
        print("   • Daily: Performance reset at midnight")
    
    def run_monitor(self):
        """Start the continuous monitoring loop"""
        print("🎰 LarlBot Betting Monitor Started!")
        print(f"📅 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.setup_schedule()
        
        # Initial check
        self.check_for_opportunities()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
                
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped by user")
        except Exception as e:
            error_msg = f"Monitor crashed: {e}"
            print(f"💥 {error_msg}")
            self.tracker.log_alert("system_crash", error_msg)
    
    def run_once(self):
        """Run a single check (for testing)"""
        print("🎯 Running single monitoring check...")
        self.check_for_opportunities()
        self.check_pending_bets()
    
    def status_report(self):
        """Generate current status report"""
        print("\n📊 BETTING MONITOR STATUS REPORT")
        print("=" * 60)
        
        # System info
        print(f"Last check: {self.last_check or 'Never'}")
        print(f"Daily alerts sent: {self.daily_alert_count}")
        
        # Performance summary
        perf = self.tracker.get_performance_summary(days=7)
        print(f"\n📈 7-Day Performance:")
        print(f"   Total bets: {perf['total_bets']}")
        print(f"   Win rate: {perf['win_rate']:.1f}%")
        print(f"   ROI: {perf['roi']:.1f}%")
        print(f"   Profit/Loss: ${perf['total_profit']:.2f}")
        
        # Recent alerts
        alerts = self.tracker.get_recent_alerts(5)
        if not alerts.empty:
            print(f"\n🚨 Recent Alerts:")
            for _, alert in alerts.iterrows():
                timestamp = alert['created_at']
                print(f"   {timestamp}: {alert['message']}")
        
        # Pending bets
        pending = self.tracker.get_pending_bets()
        if not pending.empty:
            print(f"\n📋 Pending Bets: {len(pending)}")
            for _, bet in pending.iterrows():
                print(f"   ${bet['amount']} on {bet['bet_side']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LarlBot Betting Monitor")
    parser.add_argument("--run", action="store_true", help="Start continuous monitoring")
    parser.add_argument("--once", action="store_true", help="Run single check")
    parser.add_argument("--status", action="store_true", help="Show status report")
    
    args = parser.parse_args()
    
    monitor = BettingMonitor()
    
    if args.run:
        monitor.run_monitor()
    elif args.once:
        monitor.run_once()
    elif args.status:
        monitor.status_report()
    else:
        print("Usage: python bet_monitor.py [--run|--once|--status]")
        print("  --run: Start continuous monitoring")
        print("  --once: Run single check")  
        print("  --status: Show current status")