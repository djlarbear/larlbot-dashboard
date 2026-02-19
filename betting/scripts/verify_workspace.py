#!/usr/bin/env python3
"""
Workspace Verification Script
Checks file permissions, dependencies, and configuration health
Run: python3 verify_workspace.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = '/Users/macmini/.openclaw/workspace'
CRITICAL_FILES = [
    'dashboard_server.py',
    'daily_recommendations.py',
    'learning_engine.py',
    'bet_processor.py',
    'browser_result_checker_full.py',
    'cache_manager.py',
    'active_bets.json',
    'bet_tracker_input.json',
]

CRITICAL_DIRS = [
    'templates',
    'static',
    'memory',
    'cache',
]

def check_permissions():
    """Check file and directory permissions"""
    print("\n📋 CHECKING PERMISSIONS...")
    issues = []
    
    # Check critical files
    for fname in CRITICAL_FILES:
        fpath = Path(WORKSPACE) / fname
        if fpath.exists():
            stat = fpath.stat()
            # Check if readable
            if not os.access(fpath, os.R_OK):
                issues.append(f"❌ {fname}: Not readable")
            # Check if writable
            if not os.access(fpath, os.W_OK):
                issues.append(f"❌ {fname}: Not writable")
            else:
                print(f"✅ {fname}: Readable & Writable")
        else:
            issues.append(f"⚠️ {fname}: File not found")
    
    # Check critical directories
    for dname in CRITICAL_DIRS:
        dpath = Path(WORKSPACE) / dname
        if dpath.exists():
            if not os.access(dpath, os.R_OK):
                issues.append(f"❌ {dname}/: Not readable")
            if not os.access(dpath, os.W_OK):
                issues.append(f"❌ {dname}/: Not writable")
            else:
                print(f"✅ {dname}/: Readable & Writable")
        else:
            issues.append(f"⚠️ {dname}/: Directory not found")
    
    return issues

def check_executables():
    """Check if critical scripts are executable"""
    print("\n⚙️ CHECKING EXECUTABLES...")
    issues = []
    
    scripts = [
        'dashboard_server.py',
        'daily_recommendations.py',
        'learning_engine.py',
        'bet_processor.py',
    ]
    
    for script in scripts:
        fpath = Path(WORKSPACE) / script
        if fpath.exists():
            if os.access(fpath, os.X_OK):
                print(f"✅ {script}: Executable")
            else:
                issues.append(f"⚠️ {script}: Not executable (can still run with python3)")
        else:
            issues.append(f"❌ {script}: Not found")
    
    return issues

def check_json_files():
    """Validate critical JSON files"""
    print("\n📦 CHECKING JSON FILES...")
    issues = []
    
    json_files = [
        'active_bets.json',
        'bet_tracker_input.json',
    ]
    
    for fname in json_files:
        fpath = Path(WORKSPACE) / fname
        if fpath.exists():
            try:
                with open(fpath, 'r') as f:
                    json.load(f)
                print(f"✅ {fname}: Valid JSON")
            except json.JSONDecodeError as e:
                issues.append(f"❌ {fname}: Invalid JSON - {str(e)}")
            except Exception as e:
                issues.append(f"❌ {fname}: Error reading - {str(e)}")
        else:
            issues.append(f"⚠️ {fname}: Not found")
    
    return issues

def check_dependencies():
    """Check if critical Python packages are installed"""
    print("\n📚 CHECKING DEPENDENCIES...")
    issues = []
    
    packages = [
        'flask',
        'requests',
        'pandas',
        'numpy',
    ]
    
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg}: Installed")
        except ImportError:
            issues.append(f"⚠️ {pkg}: Not installed (may be optional)")
    
    return issues

def check_cron_jobs():
    """Check if cron jobs are configured"""
    print("\n⏰ CHECKING CRON JOBS...")
    issues = []
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        cron_output = result.stdout
        
        required_jobs = [
            'bet_processor.py',
            'daily_recommendations.py',
            'learning_engine.py',
        ]
        
        for job in required_jobs:
            if job in cron_output:
                print(f"✅ Cron job for {job}: Found")
            else:
                issues.append(f"⚠️ Cron job for {job}: Not found")
    except Exception as e:
        issues.append(f"⚠️ Could not check cron jobs: {str(e)}")
    
    return issues

def check_disk_space():
    """Check available disk space"""
    print("\n💾 CHECKING DISK SPACE...")
    issues = []
    
    try:
        result = subprocess.run(['df', WORKSPACE], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            available_gb = int(parts[3]) / 1024 / 1024
            print(f"✅ Available disk: {available_gb:.1f} GB")
            
            if available_gb < 1:
                issues.append(f"❌ Low disk space: Only {available_gb:.1f} GB available")
    except Exception as e:
        issues.append(f"⚠️ Could not check disk space: {str(e)}")
    
    return issues

def generate_report(all_issues):
    """Generate summary report"""
    print("\n" + "="*60)
    print("WORKSPACE VERIFICATION REPORT")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}")
    print(f"Workspace: {WORKSPACE}")
    
    if not all_issues:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nNo permission issues detected.")
        print("Workspace is healthy and ready to use.")
        return True
    else:
        print(f"\n⚠️ FOUND {len(all_issues)} ISSUES:")
        print("-" * 60)
        
        errors = [i for i in all_issues if i.startswith('❌')]
        warnings = [i for i in all_issues if i.startswith('⚠️')]
        
        if errors:
            print("\nCritical Issues:")
            for issue in errors:
                print(f"  {issue}")
        
        if warnings:
            print("\nWarnings:")
            for issue in warnings:
                print(f"  {issue}")
        
        print("\n" + "-" * 60)
        print("Run: chmod -R u+rw /Users/macmini/.openclaw/workspace")
        print("To fix permission issues.")
        return False

def main():
    """Run all checks"""
    print("🔍 LARLBOT WORKSPACE VERIFICATION")
    print("=" * 60)
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_permissions())
    all_issues.extend(check_executables())
    all_issues.extend(check_json_files())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_cron_jobs())
    all_issues.extend(check_disk_space())
    
    # Generate report
    success = generate_report(all_issues)
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
