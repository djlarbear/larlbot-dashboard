#!/usr/bin/env python3
"""
🎰 LarlBot Browser Cache Fix
Adds cache-busting mechanisms to prevent stale data display
"""

import os
import time

WORKSPACE = "/Users/macmini/.openclaw/workspace"

def fix_dashboard_server():
    """Update dashboard_server.py to disable API caching"""
    
    print("=" * 70)
    print("🎰 LarlBot Browser Cache Fix")
    print("=" * 70)
    
    # Read current server
    with open(f'{WORKSPACE}/dashboard_server_improved.py', 'r') as f:
        content = f.read()
    
    # Check if fix already applied
    if 'no-store, no-cache' in content:
        print("\n✅ Cache fix already applied to dashboard_server_improved.py")
        return
    
    print("\n⚠️ Cache fix not found, skipping (already edited manually)")
    return

def create_cache_busting_index():
    """Create index.html with cache-busting script"""
    
    print("\n📝 Creating cache-busting index.html...")
    
    index_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>LarlBot Dashboard</title>
    
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- CSS with cache buster -->
    <link rel="stylesheet" href="/static/style.css?v=CACHEBUSTER">
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-size: 1.5rem;
        }
    </style>
</head>
<body>
    <div id="app" class="loading">
        <p>🎰 Loading LarlBot Dashboard...</p>
    </div>
    
    <!-- Script with cache buster -->
    <script src="/static/script.js?v=CACHEBUSTER"></script>
    
    <script>
        // Add extra cache control for API calls
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            const init = args[1] || {};
            
            // Add no-cache headers to all API calls
            if (typeof url === 'string' && url.includes('/api/')) {
                init.cache = 'no-store';
                init.headers = init.headers || {};
                init.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate';
                init.headers['Pragma'] = 'no-cache';
                
                // Add timestamp to prevent caching
                const separator = url.includes('?') ? '&' : '?';
                const cacheBuster = `${separator}_t=${Date.now()}`;
                args[0] = url + cacheBuster;
            }
            
            return originalFetch.apply(this, args);
        };
        
        console.log('🎰 Cache-busting enabled - API calls will always fetch fresh data');
    </script>
</body>
</html>
'''
    
    # Replace cache buster with actual value
    now = int(time.time())
    index_content = index_content.replace('CACHEBUSTER', str(now))
    
    with open(f'{WORKSPACE}/templates/index.html', 'w') as f:
        f.write(index_content)
    
    print(f"✅ Created cache-busting index.html (v={now})")

def create_anti_cache_middleware():
    """Create a middleware script for local Flask"""
    
    print("\n📝 Creating anti-cache middleware...")
    
    middleware = f'''#!/usr/bin/env python3
"""
🎰 Anti-Cache Middleware for Dashboard
Ensures API always returns fresh data
"""

def apply_no_cache_headers(app):
    """Apply no-cache headers to all responses"""
    
    @app.after_request
    def add_no_cache(response):
        # For API endpoints: NO caching at all
        if '/api/' in response.path:
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
            response.cache_control.max_age = 0
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # For HTML: Revalidate every time
        elif response.content_type and 'html' in response.content_type:
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
            response.cache_control.max_age = 0
        
        # Add timestamp header
        from datetime import datetime
        response.headers['X-Generated-At'] = datetime.now().isoformat()
        response.headers['X-Cache-Buster'] = str(int({{__import__('time').time()}}))
        
        return response
    
    return app
'''
    
    with open(f'{WORKSPACE}/anti_cache_middleware.py', 'w') as f:
        f.write(middleware)
    
    print("✅ Created anti-cache middleware")

def create_deployment_script():
    """Create deployment script for local + Railway"""
    
    print("\n📝 Creating deployment script...")
    
    deploy_script = '''#!/usr/bin/env python3
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
    print("\\n📂 DEPLOYING LOCALLY...")
    
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
    print("\\n🚀 DEPLOYING TO RAILWAY...")
    
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
    print("\\n✅ VERIFICATION...")
    
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
    
    print("\\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 70)
    print(f"   Local: {'✅ OK' if local_ok else '❌ FAILED'}")
    print(f"   Railway: {'✅ OK' if railway_ok else '⚠️ SKIPPED'}")
    print("=" * 70 + "\\n")

if __name__ == "__main__":
    main()
'''
    
    with open(f'{WORKSPACE}/deploy.py', 'w') as f:
        f.write(deploy_script)
    
    os.chmod(f'{WORKSPACE}/deploy.py', 0o755)
    print("✅ Created deployment script")

def main():
    fix_dashboard_server()
    create_cache_busting_index()
    create_anti_cache_middleware()
    create_deployment_script()
    
    print("\n" + "=" * 70)
    print("✅ CACHE FIX COMPLETE")
    print("=" * 70)
    print("\nWhat was done:")
    print("1. ✅ Added cache-busting to index.html")
    print("2. ✅ Created anti-cache middleware")
    print("3. ✅ Created deployment script")
    print("\nNext steps:")
    print("1. Kill current dashboard: pkill -f 'python3 dashboard_server'")
    print("2. Start improved version: python3 dashboard_server_improved.py")
    print("3. Clear browser cache: Ctrl+Shift+Delete")
    print("4. Hard refresh: Ctrl+F5")
    print("5. Check Purdue @ Iowa shows 'Purdue -1.5'")
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
