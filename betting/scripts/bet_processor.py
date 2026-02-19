#!/usr/bin/env python3
"""
🎰 LarlBot Bet Processor v1.0
Master orchestration: Scrape ESPN → Process results → Update records
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

WORKSPACE = "/Users/macmini/.openclaw/workspace"


def run_scraper(date_str: str) -> bool:
    """Run ESPN scraper for a specific date"""
    print(f"\n📡 Step 1: Scraping ESPN ({date_str})...")
    print("-" * 70)
    
    try:
        # Try Node.js Puppeteer approach
        result = subprocess.run(
            [sys.executable, "-c", f"""
import subprocess
result = subprocess.run(['node', '{WORKSPACE}/scrape_espn.js', '{date_str}'], 
                       capture_output=False)
exit(result.returncode)
"""],
            cwd=WORKSPACE,
            capture_output=False
        )
        
        if result.returncode == 0:
            print("✅ Scraping complete")
            return True
    except Exception as e:
        print(f"⚠️  Puppeteer scraping failed: {e}")
    
    # Fallback: Check if espn_scores_cache.json exists
    cache_file = f"{WORKSPACE}/espn_scores_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            data = json.load(f)
            if data.get('date') == date_str:
                print(f"✅ Using cached ESPN data ({len(data.get('games', []))} games)")
                return True
    
    print(f"❌ No ESPN data available for {date_str}")
    return False


def run_result_checker(bet_file: str) -> bool:
    """Run result checker on a bet file"""
    print(f"\n📊 Step 2: Processing bets ({os.path.basename(bet_file)})...")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, f"{WORKSPACE}/browser_result_checker_full.py", bet_file],
            cwd=WORKSPACE,
            capture_output=True,
            text=True
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running result checker: {e}")
        return False


def find_completed_bets_for_date(date_str: str) -> str:
    """Find completed_bets file for a given date"""
    pattern = f"completed_bets_{date_str}.json"
    filepath = f"{WORKSPACE}/{pattern}"
    
    if os.path.exists(filepath):
        return filepath
    
    return None


def verify_all_games() -> Dict:
    """
    Verify all completed bets in database against ESPN scores
    """
    print(f"\n🔍 Step 3: Comprehensive database verification...")
    print("-" * 70)
    
    results = {
        "total_dates": 0,
        "total_bets": 0,
        "total_processed": 0,
        "total_unprocessed": 0,
        "dates": []
    }
    
    # Find all completed_bets files
    completed_files = sorted(Path(WORKSPACE).glob("completed_bets_*.json"))
    
    if not completed_files:
        print("❌ No completed bets files found")
        return results
    
    print(f"📂 Found {len(completed_files)} date(s) with bets:")
    
    for bet_file in completed_files:
        date_match = str(bet_file).split('_')[-1].replace('.json', '')
        
        with open(bet_file) as f:
            bets_data = json.load(f)
        
        bets = bets_data.get('bets', [])
        processed = sum(1 for b in bets if b.get('result') not in [None, 'PENDING'])
        
        date_result = {
            "date": date_match,
            "total_bets": len(bets),
            "processed": processed,
            "unprocessed": len(bets) - processed
        }
        results["dates"].append(date_result)
        results["total_bets"] += len(bets)
        results["total_processed"] += processed
        results["total_unprocessed"] += len(bets) - processed
        
        status = "✅" if processed == len(bets) else "⏳"
        print(f"  {status} {date_match}: {processed}/{len(bets)} bets processed")
    
    results["total_dates"] = len(completed_files)
    
    return results


def generate_report(stats: Dict):
    """Generate summary report"""
    print(f"\n{'=' * 70}")
    print("📋 REPORT: Bet Processing Status")
    print(f"{'=' * 70}")
    
    print(f"\n📊 Database Summary:")
    print(f"   Dates with bets: {stats['total_dates']}")
    print(f"   Total bets: {stats['total_bets']}")
    print(f"   Processed: {stats['total_processed']}")
    print(f"   Unprocessed: {stats['total_unprocessed']}")
    
    if stats['total_bets'] > 0:
        pct = 100 * stats['total_processed'] / stats['total_bets']
        print(f"   Completion rate: {pct:.1f}%")
    
    print(f"\n📅 By Date:")
    for date_info in stats['dates']:
        pct = 100 * date_info['processed'] / date_info['total_bets'] if date_info['total_bets'] > 0 else 0
        print(f"   {date_info['date']}: {date_info['processed']}/{date_info['total_bets']} ({pct:.1f}%)")
    
    print(f"\n{'=' * 70}")


def main():
    """Main execution"""
    print(f"{'=' * 70}")
    print("🎰 LarlBot Bet Processor v1.0")
    print(f"{'=' * 70}")
    
    # Parse arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else 'verify'  # process, verify, or both
    date_str = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y-%m-%d")
    
    print(f"📅 Date: {date_str}")
    print(f"🎯 Mode: {mode}")
    
    if mode in ['process', 'both']:
        # Step 1: Scrape
        if not run_scraper(date_str):
            print("\n⚠️  Continuing without fresh ESPN data...")
        
        # Step 2: Process results
        bet_file = find_completed_bets_for_date(date_str)
        if bet_file:
            if not run_result_checker(bet_file):
                print("❌ Result checker failed")
                return
        else:
            print(f"⚠️  No bets file found for {date_str}")
    
    # Step 3: Verify all games
    stats = verify_all_games()
    generate_report(stats)
    
    # Summary
    if stats['total_unprocessed'] == 0:
        print("\n✅ All games verified and processed!")
    else:
        print(f"\n⏳ {stats['total_unprocessed']} games still need ESPN data")


if __name__ == "__main__":
    main()
