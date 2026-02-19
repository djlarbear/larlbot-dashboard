#!/usr/bin/env python3
"""
OddsAPI Rate Limiter
Manages API usage to stay within monthly quota
"""

import json
import os
from datetime import datetime, date
from pathlib import Path

class OddsAPIRateLimiter:
    def __init__(self, api_key='82865426fd192e243376eb4e51185f3b'):
        self.api_key = api_key
        self.usage_file = Path('oddsapi_usage.json')
        self.monthly_quota = 20000  # Paid tier quota
        self.daily_budget = 666  # 20000 / 30 days (conservative)
        
    def load_usage(self):
        """Load usage tracking data"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        
        return {
            'month': date.today().strftime('%Y-%m'),
            'requests_used': 0,
            'daily_usage': {},
            'last_reset': date.today().strftime('%Y-%m-01')
        }
    
    def save_usage(self, data):
        """Save usage tracking data"""
        with open(self.usage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_and_reset(self):
        """Check if we need to reset for new month"""
        usage = self.load_usage()
        current_month = date.today().strftime('%Y-%m')
        
        if usage['month'] != current_month:
            # New month - reset
            usage = {
                'month': current_month,
                'requests_used': 0,
                'daily_usage': {},
                'last_reset': date.today().replace(day=1).strftime('%Y-%m-%d')
            }
            self.save_usage(usage)
            print(f"📅 New month detected - usage reset!")
        
        return usage
    
    def get_status(self):
        """Get current usage status"""
        usage = self.check_and_reset()
        
        today_str = date.today().strftime('%Y-%m-%d')
        today_usage = usage['daily_usage'].get(today_str, 0)
        
        remaining = self.monthly_quota - usage['requests_used']
        days_in_month = 30
        today_day = date.today().day
        days_remaining = days_in_month - today_day + 1
        
        return {
            'monthly_quota': self.monthly_quota,
            'used_this_month': usage['requests_used'],
            'remaining_this_month': remaining,
            'usage_percentage': (usage['requests_used'] / self.monthly_quota * 100),
            'daily_budget': self.daily_budget,
            'used_today': today_usage,
            'remaining_today': max(0, self.daily_budget - today_usage),
            'days_into_month': today_day,
            'days_remaining': days_remaining,
            'recommended_daily_budget': remaining // days_remaining if days_remaining > 0 else 0
        }
    
    def can_make_request(self, num_requests=1):
        """Check if we can make N requests without exceeding limits"""
        status = self.get_status()
        
        # Check monthly limit
        if status['remaining_this_month'] < num_requests:
            return False, "Monthly quota exceeded"
        
        # Check daily budget (warning, not hard limit)
        if status['remaining_today'] < num_requests:
            return True, f"Warning: Daily budget low ({status['remaining_today']} left)"
        
        return True, "OK"
    
    def record_request(self, num_requests=1):
        """Record API request(s)"""
        usage = self.check_and_reset()
        today_str = date.today().strftime('%Y-%m-%d')
        
        # Update totals
        usage['requests_used'] += num_requests
        
        # Update daily usage
        if today_str not in usage['daily_usage']:
            usage['daily_usage'][today_str] = 0
        usage['daily_usage'][today_str] += num_requests
        
        self.save_usage(usage)
    
    def print_status(self):
        """Print formatted status"""
        status = self.get_status()
        
        print("╔════════════════════════════════════════════════════════════╗")
        print("║         📊 OddsAPI Usage Status - Rate Limiter            ║")
        print("╠════════════════════════════════════════════════════════════╣")
        print(f"║ Monthly Quota:      {status['monthly_quota']:>6} requests                    ║")
        print(f"║ Used This Month:    {status['used_this_month']:>6} requests ({status['usage_percentage']:>5.1f}%)           ║")
        print(f"║ Remaining:          {status['remaining_this_month']:>6} requests                    ║")
        print("╠════════════════════════════════════════════════════════════╣")
        print(f"║ Daily Budget:       {status['daily_budget']:>6} requests/day                ║")
        print(f"║ Used Today:         {status['used_today']:>6} requests                    ║")
        print(f"║ Remaining Today:    {status['remaining_today']:>6} requests                    ║")
        print("╠════════════════════════════════════════════════════════════╣")
        print(f"║ Days into month:    {status['days_into_month']:>6} days                         ║")
        print(f"║ Days remaining:     {status['days_remaining']:>6} days                         ║")
        print(f"║ Recommended daily:  {status['recommended_daily_budget']:>6} requests/day                ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        # Warning messages
        if status['usage_percentage'] > 80:
            print("\n⚠️  WARNING: Over 80% of monthly quota used!")
        elif status['usage_percentage'] > 50:
            print("\n⚠️  NOTICE: Over 50% of monthly quota used")
        
        if status['remaining_today'] < 50:
            print(f"⚠️  WARNING: Daily budget low ({status['remaining_today']} requests left)")

if __name__ == "__main__":
    limiter = OddsAPIRateLimiter()
    limiter.print_status()
