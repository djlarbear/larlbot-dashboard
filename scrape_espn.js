#!/usr/bin/env node
/**
 * 🎰 LarlBot ESPN Scraper - Node.js/Puppeteer
 * Headless browser scraping of ESPN scoreboard
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const CACHE_FILE = path.join(process.env.HOME, '.openclaw/workspace/espn_scores_cache.json');

async function scrapeESPNDate(dateStr) {
  const dateObj = new Date(dateStr);
  const espnDate = dateObj.getFullYear().toString() + 
                   String(dateObj.getMonth() + 1).padStart(2, '0') + 
                   String(dateObj.getDate()).padStart(2, '0');
  
  const url = `https://www.espn.com/mens-college-basketball/scoreboard/_/group/50/date/${espnDate}`;
  
  console.log(`[Puppeteer] Launching browser...`);
  const browser = await puppeteer.launch({ headless: true });
  
  try {
    const page = await browser.newPage();
    
    console.log(`[Puppeteer] Navigating to ${url}`);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    
    console.log(`[Puppeteer] Extracting game data...`);
    const games = await page.evaluate(() => {
      const games = [];
      const text = document.body.innerText;
      const lines = text.split('\n');
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Look for Final status lines
        if (line === 'FINAL' || line === 'FINAL/OT' || line.startsWith('FINAL/')) {
          const status = line;
          
          // Collect next ~40 lines to find team/score info
          let awayTeam = null;
          let awayScore = null;
          let homeTeam = null;
          let homeScore = null;
          let scoreCount = 0;
          
          for (let j = i + 1; j < Math.min(i + 40, lines.length); j++) {
            const curr = lines[j].trim();
            
            if (!curr) continue;
            
            // Look for team names (contain letters, usually followed by record in parens)
            const hasTeamName = /[A-Z][a-zA-Z\s&'-]{2,}/.test(curr) && 
                              (curr.includes('(') || /^\d+$/.test(lines[j + 1]?.trim()));
            
            if (hasTeamName && curr.match(/[A-Z][a-z]/)) {
              const teamName = curr.split('(')[0].split(/\d{1,3}$/)[0].trim();
              
              if (!awayTeam) {
                awayTeam = teamName;
              } else if (!homeTeam) {
                homeTeam = teamName;
                
                // Collect scores for both teams
                const scores = [];
                for (let k = j; k < Math.min(j + 15, lines.length); k++) {
                  const testLine = lines[k].trim();
                  if (/^\d{1,3}$/.test(testLine)) {
                    scores.push(parseInt(testLine));
                  } else if (testLine.match(/^\d/) && !testLine.match(/^\d{1,3}$/)) {
                    // Stop if we hit something that's not a pure number
                    break;
                  }
                }
                
                // Extract away and home totals (usually last 2-4 numbers, accounting for H1, H2, [OT])
                if (scores.length >= 4) {
                  // Pattern: away H1, away H2, [away OT], away total, home H1, home H2, [home OT], home total
                  // Find totals by looking for pattern where they're highest or at the end
                  const half = Math.floor(scores.length / 2);
                  awayScore = scores[half - 1];
                  homeScore = scores[scores.length - 1];
                  
                  // Validate
                  if (awayScore > 0 && homeScore > 0 && awayScore < 200 && homeScore < 200) {
                    break;
                  }
                }
              }
            }
          }
          
          if (awayTeam && homeTeam && awayScore && homeScore) {
            games.push({
              away_team: awayTeam.trim(),
              home_team: homeTeam.trim(),
              away_score: awayScore,
              home_score: homeScore,
              status: status
            });
          }
        }
      }
      
      return games;
    });
    
    console.log(`[Puppeteer] ✅ Found ${games.length} games`);
    return games;
    
  } finally {
    await browser.close();
  }
}

async function main() {
  const dateStr = process.argv[2] || new Date().toISOString().split('T')[0];
  
  console.log('='.repeat(70));
  console.log('🎰 LarlBot ESPN Scraper (Puppeteer)');
  console.log('='.repeat(70));
  console.log(`📅 Date: ${dateStr}`);
  
  try {
    const games = await scrapeESPNDate(dateStr);
    
    const output = {
      date: dateStr,
      source: 'ESPN Division I Scoreboard',
      scraped_at: new Date().toISOString(),
      games: games
    };
    
    fs.writeFileSync(CACHE_FILE, JSON.stringify(output, null, 2));
    
    console.log(`\n✅ Saved ${games.length} games to espn_scores_cache.json`);
    console.log('='.repeat(70));
    
  } catch (err) {
    console.error(`\n❌ Error: ${err.message}`);
    process.exit(1);
  }
}

main();
