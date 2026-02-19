#!/usr/bin/env python3
"""
Performance Monitor - Track system health & betting results
Monitors: Win rate, confidence calibration, model accuracy, anomalies
"""

import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

class PerformanceMonitor:
    def __init__(self):
        self.tracker_file = 'bet_tracker_input.json'
        self.active_bets_file = 'active_bets.json'
        self.monitor_log = 'performance_monitor.log'
    
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.monitor_log, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_performance_metrics(self):
        """Calculate all performance metrics"""
        try:
            with open(self.tracker_file, 'r') as f:
                tracker = json.load(f)
            
            bets = tracker.get('bets', [])
            completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
            
            if not completed:
                return None
            
            wins = len([b for b in completed if b['result'] == 'WIN'])
            losses = len([b for b in completed if b['result'] == 'LOSS'])
            win_rate = (wins / len(completed) * 100) if completed else 0
            
            # Calculate by risk tier
            low_risk = [b for b in completed if '🟢' in b.get('risk_tier', '')]
            mod_risk = [b for b in completed if '🟡' in b.get('risk_tier', '')]
            high_risk = [b for b in completed if '🔴' in b.get('risk_tier', '')]
            
            metrics = {
                'total_bets': len(completed),
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'timestamp': datetime.now().isoformat(),
                'by_risk_tier': {
                    'low': {
                        'total': len(low_risk),
                        'wins': len([b for b in low_risk if b['result'] == 'WIN']),
                        'win_rate': (len([b for b in low_risk if b['result'] == 'WIN']) / len(low_risk) * 100) if low_risk else 0
                    },
                    'moderate': {
                        'total': len(mod_risk),
                        'wins': len([b for b in mod_risk if b['result'] == 'WIN']),
                        'win_rate': (len([b for b in mod_risk if b['result'] == 'WIN']) / len(mod_risk) * 100) if mod_risk else 0
                    },
                    'high': {
                        'total': len(high_risk),
                        'wins': len([b for b in high_risk if b['result'] == 'WIN']),
                        'win_rate': (len([b for b in high_risk if b['result'] == 'WIN']) / len(high_risk) * 100) if high_risk else 0
                    }
                }
            }
            
            return metrics
        except Exception as e:
            self.log(f"❌ Error calculating metrics: {e}")
            return None
    
    def get_active_bets_summary(self):
        """Get summary of active bets"""
        try:
            with open(self.active_bets_file, 'r') as f:
                active_data = json.load(f)
            
            bets = active_data.get('bets', [])
            
            low_risk = len([b for b in bets if '🟢' in b.get('risk_tier', '')])
            mod_risk = len([b for b in bets if '🟡' in b.get('risk_tier', '')])
            high_risk = len([b for b in bets if '🔴' in b.get('risk_tier', '')])
            
            return {
                'total_active': len(bets),
                'by_risk_tier': {
                    'low': low_risk,
                    'moderate': mod_risk,
                    'high': high_risk
                }
            }
        except Exception as e:
            self.log(f"⚠️  Could not load active bets: {e}")
            return None
    
    def check_confidence_calibration(self):
        """Check if confidence scores match actual results"""
        try:
            with open(self.tracker_file, 'r') as f:
                tracker = json.load(f)
            
            bets = tracker.get('bets', [])
            completed = [b for b in bets if b.get('result') in ['WIN', 'LOSS']]
            
            if not completed:
                return None
            
            # Bucket by confidence ranges
            buckets = defaultdict(lambda: {'total': 0, 'wins': 0})
            
            for bet in completed:
                conf = bet.get('confidence', 50)
                result = bet.get('result', 'UNKNOWN')
                
                # Bucket: 50-60, 60-70, 70-80, 80-90, 90-100
                if conf < 60:
                    bucket = '50-60%'
                elif conf < 70:
                    bucket = '60-70%'
                elif conf < 80:
                    bucket = '70-80%'
                elif conf < 90:
                    bucket = '80-90%'
                else:
                    bucket = '90-100%'
                
                buckets[bucket]['total'] += 1
                if result == 'WIN':
                    buckets[bucket]['wins'] += 1
            
            calibration = {}
            for bucket, data in sorted(buckets.items()):
                win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
                calibration[bucket] = {
                    'total': data['total'],
                    'win_rate': win_rate,
                    'matches_confidence': abs(win_rate - int(bucket.split('-')[0])) < 10
                }
            
            return calibration
        except Exception as e:
            self.log(f"⚠️  Calibration check failed: {e}")
            return None
    
    def detect_anomalies(self):
        """Detect unusual patterns in betting"""
        try:
            metrics = self.get_performance_metrics()
            if not metrics:
                return []
            
            anomalies = []
            
            # Check for win rate drops
            if metrics['win_rate'] < 50:
                anomalies.append(f"⚠️  Win rate below 50%: {metrics['win_rate']:.1f}%")
            
            # Check for empty risk tier
            for tier, data in metrics['by_risk_tier'].items():
                if data['total'] > 0 and data['win_rate'] < 40:
                    anomalies.append(f"⚠️  {tier} risk tier underperforming: {data['win_rate']:.1f}%")
            
            return anomalies
        except Exception as e:
            self.log(f"Error detecting anomalies: {e}")
            return []
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        self.log("\n" + "="*70)
        self.log("📊 LARLBOT PERFORMANCE MONITOR REPORT")
        self.log("="*70)
        
        # Historical metrics
        metrics = self.get_performance_metrics()
        if metrics:
            self.log(f"\n📈 HISTORICAL PERFORMANCE:")
            self.log(f"  Total bets completed: {metrics['total_bets']}")
            self.log(f"  Wins: {metrics['wins']} | Losses: {metrics['losses']}")
            self.log(f"  Win Rate: {metrics['win_rate']:.1f}%")
            
            self.log(f"\n  By Risk Tier:")
            for tier, data in metrics['by_risk_tier'].items():
                if data['total'] > 0:
                    self.log(f"    {tier.upper()}: {data['wins']}/{data['total']} = {data['win_rate']:.1f}%")
        
        # Active bets
        active = self.get_active_bets_summary()
        if active:
            self.log(f"\n🎯 ACTIVE BETS:")
            self.log(f"  Total active: {active['total_active']}")
            self.log(f"  🟢 LOW RISK: {active['by_risk_tier']['low']}")
            self.log(f"  🟡 MODERATE: {active['by_risk_tier']['moderate']}")
            self.log(f"  🔴 HIGH RISK: {active['by_risk_tier']['high']}")
        
        # Confidence calibration
        calibration = self.check_confidence_calibration()
        if calibration:
            self.log(f"\n🎲 CONFIDENCE CALIBRATION:")
            for conf_range, data in calibration.items():
                match = "✅" if data['matches_confidence'] else "⚠️"
                self.log(f"  {match} {conf_range}: {data['win_rate']:.1f}% (n={data['total']})")
        
        # Anomalies
        anomalies = self.detect_anomalies()
        if anomalies:
            self.log(f"\n🚨 ANOMALIES DETECTED:")
            for anomaly in anomalies:
                self.log(f"  {anomaly}")
        else:
            self.log(f"\n✅ No anomalies detected")
        
        self.log("="*70 + "\n")
    
    def run(self):
        """Generate full report"""
        self.generate_report()

if __name__ == '__main__':
    monitor = PerformanceMonitor()
    monitor.run()
