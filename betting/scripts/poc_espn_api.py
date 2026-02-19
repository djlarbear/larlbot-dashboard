#!/usr/bin/env python3
"""
POC: ESPN Hidden API - Test college basketball coverage
Tests if ESPN's undocumented API covers small colleges/divisions
"""
import requests
import json
from datetime import datetime, timedelta

test_date = "20260216"  # Feb 16, 2026 in YYYYMMDD format

def test_espn_hidden_api():
    """Test ESPN's hidden API endpoints for college basketball"""
    
    # ESPN Hidden API endpoint for college basketball
    base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
    
    endpoints_to_test = [
        {
            "name": "Scoreboard (No Date Filter)",
            "url": f"{base_url}/scoreboard",
            "desc": "Latest scores, no date specified"
        },
        {
            "name": "Scoreboard (With Date)",
            "url": f"{base_url}/scoreboard?dates={test_date}",
            "desc": "Scores for specific date"
        },
        {
            "name": "Teams List",
            "url": f"{base_url}/teams",
            "desc": "All teams available"
        },
    ]
    
    results = {}
    
    print("="*70)
    print("ESPN HIDDEN API POC: College Basketball Coverage")
    print("="*70)
    
    for test in endpoints_to_test:
        print(f"\n{'-'*70}")
        print(f"Test: {test['name']}")
        print(f"Desc: {test['desc']}")
        print(f"URL: {test['url']}")
        print('-'*70)
        
        try:
            response = requests.get(test['url'], timeout=15)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse based on endpoint type
                if 'scoreboard' in test['url']:
                    events = data.get('events', [])
                    print(f"✓ SUCCESS: Found {len(events)} games/events")
                    
                    # Analyze games
                    if events:
                        game_sample = events[0]
                        competitions = game_sample.get('competitions', [])
                        if competitions:
                            comp = competitions[0]
                            away = comp['competitors'][1]  # away team
                            home = comp['competitors'][0]  # home team
                            
                            print(f"\nSample Game:")
                            print(f"  Away: {away['team']['displayName']}")
                            print(f"  Home: {home['team']['displayName']}")
                            print(f"  Score: {away['score']} - {home['score']}")
                            print(f"  Status: {comp['status']['type']['description']}")
                        
                        # Check for divisions in team info
                        if 'teams' in data:
                            team_count = len(data.get('teams', []))
                            print(f"\nTeams in response: {team_count}")
                            
                            # Sample team
                            sample_team = data['teams'][0]
                            print(f"\nSample Team: {sample_team.get('displayName')}")
                            print(f"  Conference: {sample_team.get('conference', {}).get('displayName', 'N/A')}")
                    
                elif 'teams' in test['url']:
                    teams = data.get('teams', [])
                    print(f"✓ SUCCESS: Found {len(teams)} teams")
                    
                    # Analyze team divisions/conferences
                    conferences = {}
                    for team in teams:
                        conf = team.get('conference', {}).get('displayName', 'Unknown')
                        conferences[conf] = conferences.get(conf, 0) + 1
                    
                    print(f"\nConferences found: {len(conferences)}")
                    for conf, count in sorted(conferences.items(), key=lambda x: -x[1])[:10]:
                        print(f"  {conf}: {count} teams")
                
                results[test['name']] = {
                    "success": True,
                    "status": response.status_code
                }
                
            else:
                print(f"✗ FAILED: HTTP {response.status_code}")
                results[test['name']] = {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            print(f"✗ EXCEPTION: {str(e)}")
            results[test['name']] = {
                "success": False,
                "error": str(e)
            }
    
    return results

def test_espn_direct_scrape():
    """Test scraping ESPN.com directly for college basketball"""
    print("\n" + "="*70)
    print("ESPN.COM DIRECT SCRAPE TEST")
    print("="*70)
    
    # Try to fetch ESPN college basketball scoreboard page
    url = "https://www.espn.com/college-basketball/scoreboard"
    
    print(f"\nAttempting to fetch: {url}")
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Check if we got content
            content_length = len(response.text)
            print(f"✓ Page fetched successfully: {content_length} bytes")
            
            # Look for game data patterns in HTML
            if 'score' in response.text.lower():
                print(f"✓ Score data found in page content")
                # Try to find JSON data in page
                if 'espn' in response.text.lower() and 'api' in response.text.lower():
                    print(f"✓ API references found in page")
            else:
                print(f"✗ No score data found in page")
        else:
            print(f"✗ FAILED: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")

if __name__ == "__main__":
    print("ESPN API POC: Testing College Basketball Coverage")
    print(f"Test Date: {test_date}\n")
    
    # Test ESPN hidden API
    api_results = test_espn_hidden_api()
    
    # Test direct ESPN scrape
    test_espn_direct_scrape()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY: ESPN API Coverage Analysis")
    print("="*70)
    print("Key Questions:")
    print("  1. Does ESPN API include D2/D3 basketball?")
    print("  2. Are NAIA schools covered?")
    print("  3. How fresh/real-time is the data?")
    print("  4. Can we reliably parse team divisions from ESPN?")
    print("="*70)
