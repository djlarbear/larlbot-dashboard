#!/usr/bin/env python3
"""
POC: NCAA-API (henrygd) - Test Division coverage
Tests if NCAA-API works for D1, D2, D3 basketball
"""
import requests
import json
from datetime import datetime, timedelta

# Test date: Feb 16, 2026 (yesterday)
test_date = "2026-02-16"

def test_ncaa_api_divisions():
    """Test NCAA-API for different divisions"""
    base_url = "https://ncaa-api.henrygd.me"
    
    # Test endpoints for different divisions
    divisions = [
        ("d1", "Division I"),
        ("d2", "Division II"),
        ("d3", "Division III"),
    ]
    
    results = {}
    
    for div_code, div_name in divisions:
        endpoint = f"{base_url}/scoreboard/basketball-men/{div_code}/{test_date}"
        print(f"\n{'='*60}")
        print(f"Testing: {div_name} ({div_code})")
        print(f"URL: {endpoint}")
        print('='*60)
        
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Count games
                games = data.get('games', [])
                print(f"✓ SUCCESS: Found {len(games)} games")
                
                # Show sample game if available
                if games:
                    sample = games[0]['game']
                    print(f"\nSample Game:")
                    print(f"  Away: {sample['away']['names']['full']} ({sample['away']['score']})")
                    print(f"  Home: {sample['home']['names']['full']} ({sample['home']['score']})")
                    print(f"  Status: {sample['gameState']}")
                
                results[div_name] = {
                    "available": True,
                    "game_count": len(games),
                    "sample": games[0] if games else None
                }
            else:
                print(f"✗ FAILED: HTTP {response.status_code}")
                results[div_name] = {
                    "available": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            print(f"✗ EXCEPTION: {str(e)}")
            results[div_name] = {
                "available": False,
                "error": str(e)
            }
    
    return results

def test_ncaa_api_endpoints():
    """Test what endpoints NCAA-API actually supports"""
    print("\n" + "="*60)
    print("TESTING NCAA-API ENDPOINT STRUCTURE")
    print("="*60)
    
    base_url = "https://ncaa-api.henrygd.me"
    
    # Try to get schools list
    try:
        response = requests.get(f"{base_url}/schools-index", timeout=10)
        if response.status_code == 200:
            schools = response.json()
            print(f"\n✓ Schools Index works")
            print(f"  Available schools: {len(schools.get('data', []))}")
        else:
            print(f"\n✗ Schools Index failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"\n✗ Schools Index error: {str(e)}")
    
    return

if __name__ == "__main__":
    print("NCAA-API POC: Testing Division Coverage")
    print(f"Test Date: {test_date}")
    
    # Test divisions
    division_results = test_ncaa_api_divisions()
    
    # Test endpoints
    test_ncaa_api_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for div_name, result in division_results.items():
        if result['available']:
            print(f"✓ {div_name}: {result.get('game_count', 0)} games found")
        else:
            print(f"✗ {div_name}: {result.get('error', 'Not available')}")
    
    print("\n" + "="*60)
    print("KEY FINDINGS:")
    print("- NCAA-API coverage (D1 vs D2/D3)")
    print("- Game count for {test_date}")
    print("- Data freshness and availability")
    print("="*60)
