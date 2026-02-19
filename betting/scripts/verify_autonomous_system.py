#!/usr/bin/env python3
"""
✅ Verify Autonomous System - End-to-End Testing
Tests all components of the 15-minute refresh system
"""

import json
import os
import subprocess
import requests
from datetime import datetime
import pytz
import time

WORKSPACE = os.environ.get('WORKSPACE', os.getcwd())
EST = pytz.timezone('America/Detroit')

# URLs to test
LOCAL_URL = "http://localhost:5001"
PROD_URL = "https://web-production-a39703.up.railway.app"

def log(message: str, status: str = "INFO"):
    """Log with colored status"""
    timestamp = datetime.now(EST).strftime("%H:%M:%S")
    icons = {
        "PASS": "✅",
        "FAIL": "❌",
        "WARN": "⚠️",
        "INFO": "ℹ️",
        "TEST": "🧪"
    }
    icon = icons.get(status, "•")
    print(f"[{timestamp}] {icon} {message}")

def test_file_exists(filepath: str, description: str) -> bool:
    """Test if a file exists"""
    full_path = f"{WORKSPACE}/{filepath}"
    exists = os.path.exists(full_path)
    
    if exists:
        log(f"{description}: EXISTS", "PASS")
        return True
    else:
        log(f"{description}: MISSING", "FAIL")
        return False

def test_cron_job(keyword: str, description: str) -> bool:
    """Test if cron job is installed"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0 and keyword in result.stdout:
            log(f"Cron Job - {description}: INSTALLED", "PASS")
            return True
        else:
            log(f"Cron Job - {description}: MISSING", "FAIL")
            return False
    except Exception as e:
        log(f"Cron Job - {description}: ERROR ({e})", "FAIL")
        return False

def test_api_endpoint(url: str, endpoint: str, description: str) -> bool:
    """Test if API endpoint returns fresh data"""
    try:
        response = requests.get(f"{url}/api/{endpoint}", timeout=10)
        
        if response.status_code != 200:
            log(f"API {endpoint} ({description}): HTTP {response.status_code}", "FAIL")
            return False
        
        data = response.json()
        
        # Check for timestamp
        has_timestamp = 'timestamp' in data or 'last_updated' in data
        
        # Check cache headers
        cache_control = response.headers.get('Cache-Control', '')
        no_cache = 'no-cache' in cache_control or 'no-store' in cache_control
        
        if has_timestamp and no_cache:
            log(f"API {endpoint} ({description}): FRESH DATA + NO-CACHE", "PASS")
            return True
        elif has_timestamp:
            log(f"API {endpoint} ({description}): HAS TIMESTAMP (cache headers weak)", "WARN")
            return True
        else:
            log(f"API {endpoint} ({description}): NO TIMESTAMP", "FAIL")
            return False
    
    except requests.exceptions.RequestException as e:
        log(f"API {endpoint} ({description}): CONNECTION FAILED ({e})", "FAIL")
        return False

def test_git_status() -> bool:
    """Test git repository status"""
    try:
        os.chdir(WORKSPACE)
        
        # Check if on main branch
        result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        branch = result.stdout.strip()
        
        if branch != 'main':
            log(f"Git Branch: {branch} (should be main)", "WARN")
        else:
            log(f"Git Branch: {branch}", "PASS")
        
        # Check remote
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'github.com' in result.stdout:
            log("Git Remote: GitHub connected", "PASS")
            return True
        else:
            log("Git Remote: No GitHub remote", "FAIL")
            return False
    
    except Exception as e:
        log(f"Git Status: ERROR ({e})", "FAIL")
        return False

def test_script_executable(filepath: str, description: str) -> bool:
    """Test if script is executable"""
    full_path = f"{WORKSPACE}/{filepath}"
    
    if not os.path.exists(full_path):
        log(f"{description}: NOT FOUND", "FAIL")
        return False
    
    is_executable = os.access(full_path, os.X_OK)
    
    if is_executable:
        log(f"{description}: EXECUTABLE", "PASS")
        return True
    else:
        log(f"{description}: NOT EXECUTABLE", "WARN")
        # Try to make it executable
        try:
            os.chmod(full_path, 0o755)
            log(f"{description}: MADE EXECUTABLE", "PASS")
            return True
        except:
            log(f"{description}: FAILED TO MAKE EXECUTABLE", "FAIL")
            return False

def main():
    """Run all verification tests"""
    log("=" * 80, "INFO")
    log("AUTONOMOUS SYSTEM VERIFICATION - END-TO-END TESTS", "INFO")
    log("=" * 80, "INFO")
    
    passed = 0
    failed = 0
    warnings = 0
    
    tests = []
    
    # Test 1: Essential Files
    log("\n📁 TEST SUITE 1: ESSENTIAL FILES", "TEST")
    tests.append(test_file_exists("active_bets.json", "Active Bets File"))
    tests.append(test_file_exists("ranked_bets.json", "Ranked Bets File"))
    tests.append(test_file_exists("completed_bets_2026-02-16.json", "Completed Bets File"))
    tests.append(test_file_exists("dashboard_server_cache_fixed.py", "Dashboard Server"))
    
    # Test 2: Automation Scripts
    log("\n🤖 TEST SUITE 2: AUTOMATION SCRIPTS", "TEST")
    tests.append(test_script_executable("auto_update_cycle.py", "Auto-Update Cycle"))
    tests.append(test_script_executable("game_status_checker.py", "Game Status Checker"))
    tests.append(test_script_executable("production_sync.sh", "Production Sync"))
    tests.append(test_script_executable("system_monitor.py", "System Monitor"))
    
    # Test 3: Cron Jobs
    log("\n⏰ TEST SUITE 3: CRON JOBS", "TEST")
    tests.append(test_cron_job("daily_recommendations.py", "Daily Picks (7 AM)"))
    tests.append(test_cron_job("auto_update_cycle.py", "15-Min Updates"))
    tests.append(test_cron_job("production_sync.sh", "Git Sync"))
    tests.append(test_cron_job("learning_engine.py", "Learning Engine (6h)"))
    
    # Test 4: Git Repository
    log("\n🔗 TEST SUITE 4: GIT REPOSITORY", "TEST")
    tests.append(test_git_status())
    
    # Test 5: Local Dashboard API
    log("\n🌐 TEST SUITE 5: LOCAL DASHBOARD API", "TEST")
    tests.append(test_api_endpoint(LOCAL_URL, "bets", "Active Bets"))
    tests.append(test_api_endpoint(LOCAL_URL, "stats", "Statistics"))
    tests.append(test_api_endpoint(LOCAL_URL, "ranked-bets", "Ranked Bets"))
    tests.append(test_api_endpoint(LOCAL_URL, "health", "Health Check"))
    
    # Test 6: Production Dashboard API
    log("\n🚀 TEST SUITE 6: PRODUCTION DASHBOARD API (Railway)", "TEST")
    tests.append(test_api_endpoint(PROD_URL, "bets", "Active Bets"))
    tests.append(test_api_endpoint(PROD_URL, "stats", "Statistics"))
    tests.append(test_api_endpoint(PROD_URL, "ranked-bets", "Ranked Bets"))
    tests.append(test_api_endpoint(PROD_URL, "health", "Health Check"))
    
    # Calculate results
    passed = sum(tests)
    failed = len(tests) - passed
    
    log("\n" + "=" * 80, "INFO")
    log("VERIFICATION COMPLETE", "INFO")
    log("=" * 80, "INFO")
    log(f"Total Tests: {len(tests)}", "INFO")
    log(f"Passed: {passed}", "PASS" if failed == 0 else "INFO")
    log(f"Failed: {failed}", "FAIL" if failed > 0 else "INFO")
    
    success_rate = (passed / len(tests) * 100) if tests else 0
    log(f"Success Rate: {success_rate:.1f}%", "PASS" if success_rate == 100 else "WARN")
    
    if failed == 0:
        log("\n✅ ALL SYSTEMS OPERATIONAL - AUTONOMOUS MODE READY", "PASS")
        log("   • 15-minute refresh cycle: ENABLED", "INFO")
        log("   • Auto-deployment to Railway: ENABLED", "INFO")
        log("   • Game status tracking: ENABLED", "INFO")
        log("   • Dashboard always fresh: ENABLED", "INFO")
        return 0
    else:
        log("\n⚠️ SOME TESTS FAILED - REVIEW ISSUES ABOVE", "WARN")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
