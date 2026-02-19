#!/usr/bin/env python3
"""
🎰 LarlBot Cache Manager v1.0
Comprehensive caching to minimize API token usage

Caches:
- Daily picks (regenerated once per day)
- Learning insights (6-hour cache)
- ESPN game data (24-hour cache)
- Bet calculations (persistent)
- Adaptive model state (persistent)
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

CACHE_DIR = "/Users/macmini/.openclaw/workspace/cache"
os.makedirs(CACHE_DIR, exist_ok=True)


class CacheManager:
    """Manages all caching operations"""
    
    # Cache durations (in seconds)
    CACHE_DURATIONS = {
        'daily_picks': 86400,      # 24 hours (once per day)
        'learning_insights': 21600,  # 6 hours
        'espn_games': 3600,        # 1 hour (ESPN updates frequently)
        'bet_stats': 300,          # 5 minutes (for dashboard)
        'active_bets': 300,        # 5 minutes
        'completed_bets': 3600,    # 1 hour
    }
    
    @staticmethod
    def get_cache_path(name: str) -> str:
        """Get path to cache file"""
        return os.path.join(CACHE_DIR, f"{name}.json")
    
    @staticmethod
    def is_cache_valid(cache_name: str) -> bool:
        """Check if cache is still valid"""
        cache_path = CacheManager.get_cache_path(cache_name)
        
        if not os.path.exists(cache_path):
            return False
        
        # Check age
        file_age = time.time() - os.path.getmtime(cache_path)
        max_age = CacheManager.CACHE_DURATIONS.get(cache_name, 3600)
        
        if file_age > max_age:
            return False
        
        return True
    
    @staticmethod
    def get_cache(cache_name: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if not CacheManager.is_cache_valid(cache_name):
            return None
        
        try:
            cache_path = CacheManager.get_cache_path(cache_name)
            with open(cache_path, 'r') as f:
                data = json.load(f)
                print(f"✅ Cache hit: {cache_name}")
                return data
        except Exception as e:
            print(f"⚠️  Cache read error ({cache_name}): {e}")
            return None
    
    @staticmethod
    def set_cache(cache_name: str, data: Dict) -> bool:
        """Save data to cache"""
        try:
            cache_path = CacheManager.get_cache_path(cache_name)
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Cache saved: {cache_name}")
            return True
        except Exception as e:
            print(f"❌ Cache write error ({cache_name}): {e}")
            return False
    
    @staticmethod
    def clear_cache(cache_name: Optional[str] = None) -> bool:
        """Clear specific cache or all caches"""
        try:
            if cache_name:
                cache_path = CacheManager.get_cache_path(cache_name)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    print(f"🗑️  Cache cleared: {cache_name}")
            else:
                # Clear all
                for file in os.listdir(CACHE_DIR):
                    os.remove(os.path.join(CACHE_DIR, file))
                print(f"🗑️  All caches cleared")
            return True
        except Exception as e:
            print(f"❌ Cache clear error: {e}")
            return False
    
    @staticmethod
    def get_cache_stats() -> Dict:
        """Get cache statistics"""
        stats = {
            'cache_dir': CACHE_DIR,
            'total_files': 0,
            'total_size_kb': 0,
            'caches': {}
        }
        
        try:
            for file in os.listdir(CACHE_DIR):
                filepath = os.path.join(CACHE_DIR, file)
                size = os.path.getsize(filepath)
                age = time.time() - os.path.getmtime(filepath)
                
                cache_name = file.replace('.json', '')
                max_age = CacheManager.CACHE_DURATIONS.get(cache_name, 3600)
                valid = age < max_age
                
                stats['caches'][cache_name] = {
                    'size_kb': round(size / 1024, 2),
                    'age_seconds': int(age),
                    'valid': valid,
                    'expires_in_seconds': max(0, int(max_age - age))
                }
                
                stats['total_files'] += 1
                stats['total_size_kb'] += size / 1024
        except Exception as e:
            print(f"⚠️  Error getting cache stats: {e}")
        
        stats['total_size_kb'] = round(stats['total_size_kb'], 2)
        return stats


def print_cache_status():
    """Print cache manager status"""
    stats = CacheManager.get_cache_stats()
    
    print("\n" + "=" * 80)
    print("📦 CACHE MANAGER STATUS")
    print("=" * 80)
    print(f"\nCache Directory: {stats['cache_dir']}")
    print(f"Total Files: {stats['total_files']}")
    print(f"Total Size: {stats['total_size_kb']} KB")
    
    if stats['caches']:
        print("\nCache Details:")
        for name, info in sorted(stats['caches'].items()):
            status = "✅ VALID" if info['valid'] else "❌ EXPIRED"
            expires = f"{info['expires_in_seconds']}s" if info['valid'] else "NOW"
            print(f"  {name:20s} | {status} | {info['size_kb']:6.2f} KB | Expires: {expires}")
    else:
        print("\nNo caches yet.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_cache_status()
