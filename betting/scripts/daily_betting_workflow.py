#!/usr/bin/env python3
"""
Daily Betting Workflow - Batched execution
Runs all 4 morning tasks sequentially in single cron job.
Saves 3 cron invocations, reduces token overhead.

5:00 AM: Fetch scores (NCAA API)
5:15 AM: Learning engine
5:30 AM: Update weights
5:45 AM: Generate picks
"""
import subprocess
import sys
from datetime import datetime

SCRIPTS = [
    ("Fetch Scores", "/Users/macmini/.openclaw/agents/backend-dev/ncaa_hybrid_score_fetcher.py"),
    ("Learning Engine", "/Users/macmini/.openclaw/workspace/betting/scripts/learning_engine.py"),
    ("Update Weights", "/Users/macmini/.openclaw/workspace/betting/scripts/update_adaptive_weights.py"),
    ("Generate Picks", "/Users/macmini/.openclaw/workspace/betting/scripts/initialize_daily_bets.py"),
]

def run_workflow():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 DAILY BETTING WORKFLOW START")
    failed = []
    
    for name, script in SCRIPTS:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ▶️  {name}...")
            result = subprocess.run([sys.executable, script], capture_output=True, timeout=300)
            # Success if returncode 0 OR only warnings in stderr
            stderr = result.stderr.decode()
            if result.returncode == 0 or 'Warning' in stderr and 'Error' not in stderr:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {name}")
            else:
                err_msg = stderr.split('\n')[0]  # First line only
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {name}: {err_msg[:150]}")
                failed.append(name)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {name}: {str(e)[:150]}")
            failed.append(name)
    
    if failed:
        print(f"\n⚠️  FAILED: {', '.join(failed)}")
        return 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WORKFLOW COMPLETE")
    return 0

if __name__ == "__main__":
    sys.exit(run_workflow())
