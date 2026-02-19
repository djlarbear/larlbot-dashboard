#!/usr/bin/env python3
"""
DraftKings Odds Scraper - Backup odds source 🎰
Legal for personal use, research, and analysis
"""

import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime

class DraftKingsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        
        # DraftKings sport mapping
        self.sport_paths = {
            'nba': 'basketball/nba',
            'ncb': 'basketball/ncaab', 
            'nfl': 'football/nfl',
            'mlb': 'baseball/mlb'
        }
    
    def get_dk_odds(self, sport='nba'):
        """Scrape odds from DraftKings"""
        if sport not in self.sport_paths:
            print(f"❌ Sport {sport} not supported for DK scraping")
            return []
        
        sport_path = self.sport_paths[sport]
        url = f"https://sportsbook.draftkings.com/{sport_path}"
        
        try:
            print(f"🎯 Scraping DraftKings {sport.upper()} odds...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # DraftKings loads data via JavaScript/API calls
            # Look for embedded JSON data in the page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the data script tag
            scripts = soup.find_all('script')
            game_data = []
            
            for script in scripts:
                if script.string and 'offerings' in script.string:
                    try:
                        # Extract JSON data (simplified approach)
                        script_content = script.string
                        if 'window.__INITIAL_STATE__' in script_content:
                            # Parse the initial state data
                            start = script_content.find('{')
                            end = script_content.rfind('}') + 1
                            if start > -1 and end > start:
                                data_str = script_content[start:end]
                                initial_data = json.loads(data_str)
                                game_data = self.parse_dk_data(initial_data, sport)
                                break
                    except (json.JSONDecodeError, KeyError) as e:
                        continue
            
            if not game_data:
                # Fallback: try to parse from visible HTML elements
                game_data = self.parse_dk_html(soup, sport)
            
            print(f"📊 Scraped {len(game_data)} {sport.upper()} games from DraftKings")
            return game_data
            
        except Exception as e:
            print(f"❌ DraftKings scraping failed: {e}")
            return []
    
    def parse_dk_data(self, data, sport):
        """Parse DraftKings JSON data structure"""
        games = []
        
        # This is a simplified parser - DK's structure is complex
        # In production, you'd need to reverse engineer their current API structure
        
        try:
            # Look for offerings/events data
            if 'sportsbook' in data and 'offerings' in data['sportsbook']:
                offerings = data['sportsbook']['offerings']
                
                for offering in offerings:
                    if offering.get('eventGroupName', '').lower() == sport:
                        # Extract game info
                        games.append({
                            'source': 'draftkings',
                            'game_id': offering.get('eventId', 'unknown'),
                            'home_team': offering.get('homeTeamName', ''),
                            'away_team': offering.get('awayTeamName', ''),
                            'spread': self.extract_spread(offering),
                            'total': self.extract_total(offering),
                            'timestamp': datetime.now().isoformat()
                        })
        
        except Exception as e:
            print(f"⚠️ Error parsing DK JSON data: {e}")
        
        return games
    
    def parse_dk_html(self, soup, sport):
        """Fallback HTML parsing if JSON extraction fails"""
        games = []
        
        # Look for game containers in the HTML
        game_containers = soup.find_all('div', {'data-testid': 'event-cell'}) or \
                         soup.find_all('div', class_=lambda x: x and 'game' in x.lower()) or \
                         soup.find_all('table', class_=lambda x: x and 'sportsbook' in x.lower())
        
        print(f"🔍 Found {len(game_containers)} potential game containers in HTML")
        
        for container in game_containers[:10]:  # Limit to prevent spam
            try:
                # Try to extract team names and odds
                team_elements = container.find_all(text=True)
                text_content = ' '.join([text.strip() for text in team_elements if text.strip()])
                
                # Very basic pattern matching - would need refinement
                if '@' in text_content and any(keyword in text_content.lower() 
                    for keyword in ['spread', 'point', 'total', 'over', 'under']):
                    
                    games.append({
                        'source': 'draftkings_html',
                        'game_id': f"dk_html_{len(games)}",
                        'raw_text': text_content[:200],  # For debugging
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                continue
        
        return games
    
    def extract_spread(self, offering):
        """Extract spread from DK offering data"""
        # Placeholder - would need to match DK's current data structure
        return offering.get('pointSpread', {}).get('homePointSpread')
    
    def extract_total(self, offering):
        """Extract total from DK offering data"""
        # Placeholder - would need to match DK's current data structure  
        return offering.get('totalPoints', {}).get('total')
    
    def scrape_all_sports(self):
        """Scrape odds for all supported sports"""
        all_odds = {}
        
        for sport in self.sport_paths.keys():
            odds = self.get_dk_odds(sport)
            if odds:
                all_odds[sport] = odds
            time.sleep(2)  # Be respectful to their servers
        
        return all_odds

if __name__ == "__main__":
    # Test the scraper
    scraper = DraftKingsScraper()
    odds = scraper.get_dk_odds('nba')
    print(f"\n📊 Scraping Results:")
    for game in odds:
        print(f"  {game}")