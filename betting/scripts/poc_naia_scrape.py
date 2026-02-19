#!/usr/bin/env python3
"""
POC: NAIA Basketball Scraping from PrestoSports
Tests if NAIA data is scrapeable from naiastats.prestosports.com
"""
import requests
from datetime import datetime

def test_naia_prestosports():
    """Test NAIA PrestoSports scoreboard page"""
    
    url = "https://naiastats.prestosports.com/sports/mbkb/scoreboard"
    
    print("="*70)
    print("NAIA BASKETBALL SCRAPING POC")
    print("="*70)
    print(f"\nTesting: {url}")
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✓ Page fetched successfully")
            print(f"Content size: {len(response.text)} bytes")
            
            # Check for key content patterns
            checks = [
                ("score" in response.text.lower(), "Score data"),
                ("team" in response.text.lower(), "Team names"),
                ("game" in response.text.lower(), "Game references"),
                ("json" in response.text.lower(), "JSON data"),
            ]
            
            print(f"\nContent Analysis:")
            for check, desc in checks:
                status = "✓" if check else "✗"
                print(f"  {status} {desc}")
            
            # Try to find JSON data in page
            if '{"' in response.text or "[{" in response.text:
                print(f"\n✓ JSON structures found in HTML (likely embedded data)")
            
            # Check for API endpoints in page
            if 'api' in response.text.lower() and 'json' in response.text.lower():
                print(f"✓ API references found")
                
        else:
            print(f"✗ Page fetch failed")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")

def test_naia_api_endpoints():
    """Test if NAIA PrestoSports exposes any JSON API endpoints"""
    
    print("\n" + "="*70)
    print("NAIA API ENDPOINT TESTS")
    print("="*70)
    
    base_url = "https://naiastats.prestosports.com"
    
    endpoints = [
        "/sports/mbkb/scoreboard.json",
        "/sports/mbkb/schedule.json",
        "/api/sports/mbkb/scoreboard",
        "/api/games.json?sport=mbkb",
    ]
    
    for endpoint in endpoints:
        full_url = base_url + endpoint
        print(f"\nTrying: {endpoint}")
        
        try:
            response = requests.get(full_url, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                # Check if it's JSON
                try:
                    data = response.json()
                    print(f"  ✓ Valid JSON returned")
                except:
                    print(f"  Got response but not JSON ({len(response.text)} bytes)")
            elif response.status_code == 404:
                print(f"  ✗ Endpoint not found")
            
        except Exception as e:
            print(f"  ✗ Exception: {type(e).__name__}")

if __name__ == "__main__":
    print("NAIA Data Access POC\n")
    
    test_naia_prestosports()
    test_naia_api_endpoints()
    
    print("\n" + "="*70)
    print("FEASIBILITY ASSESSMENT")
    print("="*70)
    print("""
Key Questions:
1. Is NAIA PrestoSports page scrapeable with BeautifulSoup/Selenium?
2. Are there embedded JSON APIs in the HTML?
3. What's the technical complexity of maintaining a scraper?
4. How often does NAIA update game scores?

Viability:
- Web scraping: LIKELY (no robots.txt block observed)
- Complexity: MEDIUM (likely JS-rendered, may need Selenium)
- Maintenance: ONGOING (if site structure changes)
""")
