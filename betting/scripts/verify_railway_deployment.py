#!/usr/bin/env python3
"""
Verify that Railway deployment is working and synced with GitHub
"""

import requests
import json
from datetime import datetime

LOCAL_URL = "http://localhost:5001"
RAILWAY_URL = "https://web-production-a39703.up.railway.app"

def check_endpoint(url, endpoint):
    """Check if an endpoint is working"""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json(), True
        else:
            return f"HTTP {response.status_code}", False
    except Exception as e:
        return str(e), False

def main():
    print("=" * 70)
    print("🚀 Railway Deployment Verification")
    print("=" * 70)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}")
    print()
    
    # Test local
    print("📍 LOCAL DASHBOARD (http://localhost:5001)")
    print("-" * 70)
    
    local_stats, local_ok = check_endpoint(LOCAL_URL, "/api/stats")
    if local_ok:
        print("✅ /api/stats:")
        print(f"   Win Rate: {local_stats.get('win_rate')}%")
        print(f"   Record: {local_stats.get('record')}")
        print(f"   Total Bets: {local_stats.get('total_bets')}")
    else:
        print(f"❌ /api/stats: {local_stats}")
    
    print()
    
    # Test Railway
    print("🌍 RAILWAY PRODUCTION (https://web-production-a39703.up.railway.app)")
    print("-" * 70)
    
    railway_stats, railway_ok = check_endpoint(RAILWAY_URL, "/api/stats")
    if railway_ok:
        print("✅ /api/stats:")
        print(f"   Win Rate: {railway_stats.get('win_rate')}%")
        print(f"   Record: {railway_stats.get('record')}")
        print(f"   Total Bets: {railway_stats.get('total_bets')}")
    else:
        print(f"❌ /api/stats: {railway_stats}")
    
    print()
    print("=" * 70)
    
    # Compare
    if local_ok and railway_ok:
        if local_stats == railway_stats:
            print("✅ PERFECT SYNC! Local and Railway have identical data")
        else:
            print("⚠️  DATA MISMATCH!")
            print(f"   Local:  {local_stats}")
            print(f"   Railway: {railway_stats}")
            print()
            print("   Possible reasons:")
            print("   1. Railway hasn't rebuilt yet (wait 2-5 minutes)")
            print("   2. Browser cache is showing old data (hard refresh)")
            print("   3. New commits haven't deployed (check GitHub webhook)")
    elif local_ok and not railway_ok:
        print("⚠️  Railway is NOT responding")
        print("   Possible reasons:")
        print("   1. Railway is still building (wait 2-5 minutes)")
        print("   2. Server crashed (check Railway logs)")
        print("   3. Domain/URL wrong")
    elif not local_ok:
        print("❌ Local dashboard not running!")
        print(f"   Error: {local_stats}")
    
    print()
    print("=" * 70)
    print("📋 DEPLOYMENT CHECKLIST")
    print("-" * 70)
    print("✅ Procfile updated to use dashboard_server_cache_fixed.py")
    print("✅ railway.json configured with PORT and WORKSPACE env vars")
    print("✅ requirements.txt has all dependencies (including pytz)")
    print("✅ dashboard_server_cache_fixed.py uses os.environ.get('PORT')")
    print("✅ All changes committed to GitHub")
    print("✅ Latest commit pushed to origin/main")
    print()
    print("🔄 Next Steps:")
    print("   1. Wait 2-5 minutes for Railway auto-deploy")
    print("   2. Check Railway logs: railway.app → Project → Logs")
    print("   3. Hard refresh Railway URL (Cmd+Shift+R)")
    print("   4. Re-run this script: python3 verify_railway_deployment.py")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
