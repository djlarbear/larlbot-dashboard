#!/usr/bin/env python3
"""
OddsAPI Call Manager - Limits calls to 10 per day and caches results
Conserves API quota and provides fresh data when needed
"""

import json
import sqlite3
from datetime import datetime, timedelta
import os

class OddsCacheManager:
    def __init__(self):
        self.cache_db = "odds_cache.db"
        self.max_daily_calls = 10
        self.cache_duration_hours = 3  # Cache data for 3 hours
        self.init_cache_db()
    
    def init_cache_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Cache table for odds data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_cache (
                sport TEXT PRIMARY KEY,
                odds_data TEXT,
                last_updated TIMESTAMP,
                api_calls_used INTEGER DEFAULT 0
            )
        ''')
        
        # Daily usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_usage (
                date TEXT PRIMARY KEY,
                calls_made INTEGER DEFAULT 0,
                last_reset TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Odds cache database initialized")
    
    def get_daily_usage(self):
        """Get today's API call count"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT calls_made FROM daily_usage WHERE date = ?', (today,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        else:
            # Create today's entry
            self.reset_daily_counter()
            return 0
    
    def increment_daily_usage(self):
        """Increment today's API call count"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_usage (date, calls_made, last_reset)
            VALUES (?, COALESCE((SELECT calls_made FROM daily_usage WHERE date = ?), 0) + 1, ?)
        ''', (today, today, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def reset_daily_counter(self):
        """Reset daily counter (called automatically at midnight)"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_usage (date, calls_made, last_reset)
            VALUES (?, 0, ?)
        ''', (today, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def can_make_api_call(self):
        """Check if we can make an API call today"""
        daily_usage = self.get_daily_usage()
        return daily_usage < self.max_daily_calls
    
    def get_cached_odds(self, sport):
        """Get cached odds for a sport if still fresh"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT odds_data, last_updated FROM odds_cache WHERE sport = ?
        ''', (sport,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None, None
        
        odds_data_json, last_updated_str = result
        last_updated = datetime.fromisoformat(last_updated_str)
        
        # Check if cache is still fresh
        cache_age = datetime.now() - last_updated
        if cache_age < timedelta(hours=self.cache_duration_hours):
            try:
                odds_data = json.loads(odds_data_json)
                return odds_data, last_updated
            except json.JSONDecodeError:
                return None, None
        
        return None, None
    
    def cache_odds(self, sport, odds_data):
        """Cache odds data for a sport"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        odds_json = json.dumps(odds_data)
        now = datetime.now()
        
        cursor.execute('''
            INSERT OR REPLACE INTO odds_cache (sport, odds_data, last_updated)
            VALUES (?, ?, ?)
        ''', (sport, odds_json, now))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Cached odds for {sport} at {now.strftime('%H:%M:%S')}")
    
    def get_cache_status(self):
        """Get overall cache status for dashboard display"""
        daily_usage = self.get_daily_usage()
        remaining_calls = self.max_daily_calls - daily_usage
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Get last update times for all sports
        cursor.execute('''
            SELECT sport, last_updated FROM odds_cache
            ORDER BY last_updated DESC
        ''')
        
        cached_sports = cursor.fetchall()
        conn.close()
        
        status = {
            'daily_calls_used': daily_usage,
            'daily_calls_remaining': remaining_calls,
            'can_refresh': remaining_calls > 0,
            'cached_sports': []
        }
        
        for sport, last_updated_str in cached_sports:
            if last_updated_str:
                last_updated = datetime.fromisoformat(last_updated_str)
                cache_age = datetime.now() - last_updated
                is_fresh = cache_age < timedelta(hours=self.cache_duration_hours)
                
                status['cached_sports'].append({
                    'sport': sport,
                    'last_updated': last_updated,
                    'age_hours': cache_age.total_seconds() / 3600,
                    'is_fresh': is_fresh
                })
        
        return status
    
    def should_refresh_odds(self, sport):
        """Determine if we should refresh odds for a sport"""
        # Check if we have API calls left
        if not self.can_make_api_call():
            print(f"⚠️ Daily API limit reached ({self.max_daily_calls}/day). Using cached data.")
            return False
        
        # Check cache freshness
        cached_odds, last_updated = self.get_cached_odds(sport)
        
        if cached_odds is None:
            print(f"🔄 No cache for {sport} - will fetch fresh data")
            return True
        
        cache_age = datetime.now() - last_updated
        cache_age_hours = cache_age.total_seconds() / 3600
        
        if cache_age_hours >= self.cache_duration_hours:
            print(f"🔄 Cache for {sport} is {cache_age_hours:.1f}h old - will refresh")
            return True
        
        print(f"💾 Using cached {sport} data ({cache_age_hours:.1f}h old)")
        return False
    
    def get_cache_summary_for_display(self):
        """Get cache summary for dashboard display"""
        status = self.get_cache_status()
        
        if not status['cached_sports']:
            return "📊 No cached data - click Analyze Markets to load fresh odds"
        
        latest_update = max(status['cached_sports'], key=lambda x: x['last_updated'])
        latest_time = latest_update['last_updated']
        
        summary = f"📊 Last updated: {latest_time.strftime('%H:%M:%S')} • "
        summary += f"API calls today: {status['daily_calls_used']}/{self.max_daily_calls} • "
        
        if status['can_refresh']:
            summary += f"✅ {status['daily_calls_remaining']} calls remaining"
        else:
            summary += "⚠️ Daily limit reached - using cached data"
        
        return summary

if __name__ == "__main__":
    # Test the cache manager
    manager = OddsCacheManager()
    status = manager.get_cache_status()
    print(f"📊 Cache Status: {status}")
    print(f"📱 Daily usage: {status['daily_calls_used']}/{manager.max_daily_calls}")
    print(f"🔄 Can refresh: {status['can_refresh']}")