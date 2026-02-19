#!/usr/bin/env python3
"""
🎰 LarlBot Deployment Script
Updates both local AND Railway app
"""

import os
import subprocess
import json
from datetime import datetime

WORKSPACE = "/Users/macmini/.openclaw/workspace"

def deploy_local():
    """Deploy to local dashboard"""
    print("\n📂 DEPLOYING LOCALLY...")
    
    # Kill old dashboard process
    print("   Stopping old dashboard...")
    os.system("pkill -f 'python3 dashboard_server' 2>/dev/null")
    
    import time
    time.sleep(1)
    
    # Start new dashboard
    print("   Starting new dashboard on port 5001...")
    os.system("cd {} && python3 dashboard_server_improved.py > /tmp/dashboard.log 2>&1 &".format(WORKSPACE))
    
    time.sleep(2)
    
    # Verify it's running
    result = os.system("curl -s http://localhost:5001/api/health > /dev/null 2>&1")
    
    if result == 0:
        print("   ✅ Local dashboard started successfully")
        return True
    else:
        print("   ❌ Failed to start local dashboard")
        return False

def deploy_railway():
    """Deploy to Railway app"""
    print("\n🚀 DEPLOYING TO RAILWAY...")
    
    # Check if git repo exists
    if not os.path.exists(f"{WORKSPACE}/.git"):
        print("   ⚠️ Not a git repo, skipping Railway deploy")
        return False
    
    try:
        os.chdir(WORKSPACE)
        
        # Git push to Railway
        print("   Pushing to Railway...")
        result = subprocess.run(["git", "push"], capture_output=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Pushed to Railway successfully")
            return True
        else:
            error = result.stderr.decode() if result.stderr else "Unknown error"
            print(f"   ⚠️ Git push returned: {error[:100]}")
            return False
    except Exception as e:
        print(f"   ⚠️ Railway deploy failed: {e}")
        return False

def verify_deployment():
    """Verify deployment successful"""
    print("\n✅ VERIFICATION...")
    
    import requests
    
    # Check local
    try:
        response = requests.get('http://localhost:5001/api/stats', timeout=5)
        if response.status_code == 200:
            print("   ✅ Local API responding")
        else:
            print(f"   ❌ Local API returned {response.status_code}")
    except:
        print("   ❌ Local API not accessible")

def main():
    print("=" * 70)
    print("🎰 LarlBot Deployment Manager")
    print("=" * 70)
    
    # Deploy locally
    local_ok = deploy_local()
    
    # Deploy to Railway
    railway_ok = deploy_railway()
    
    # Verify
    verify_deployment()
    
    print("\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 70)
    print(f"   Local: {'✅ OK' if local_ok else '❌ FAILED'}")
    print(f"   Railway: {'✅ OK' if railway_ok else '⚠️ SKIPPED'}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
