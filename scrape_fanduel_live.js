const puppeteer = require('puppeteer');

async function scrapeFanDuelLines() {
  let browser;
  try {
    console.log('🌐 Starting browser...');
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    console.log('📱 Navigating to FanDuel...');
    
    // Set timeout
    page.setDefaultTimeout(15000);
    
    // Navigate to FanDuel
    await page.goto('https://www.fanduel.com', { waitUntil: 'networkidle0' });
    
    console.log('✅ Page loaded');
    
    // Look for NCAA basketball or sports section
    console.log('🏀 Looking for NCAA basketball section...');
    
    // Try to find and click sports link
    const sportLinks = await page.$$('a, button');
    console.log(`📍 Found ${sportLinks.length} clickable elements on page`);
    
    // Look for specific text patterns
    const pageText = await page.evaluate(() => document.body.innerText);
    
    // Check if we can find NCAA or basketball
    if (pageText.includes('NCAA')) {
      console.log('✅ Found NCAA on page');
    } else if (pageText.includes('Basketball')) {
      console.log('✅ Found Basketball on page');
    } else if (pageText.includes('College')) {
      console.log('✅ Found College on page');
    } else {
      console.log('⚠️  NCAA/Basketball not immediately visible');
      console.log('📄 Page content preview (first 500 chars):');
      console.log(pageText.substring(0, 500));
    }
    
    // Try to get all game data visible on page
    const allText = await page.evaluate(() => {
      return document.body.innerText;
    });
    
    console.log('\n' + '='.repeat(80));
    console.log('📋 PAGE CONTENT (First 2000 chars):');
    console.log('='.repeat(80));
    console.log(allText.substring(0, 2000));
    
    await browser.close();
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (browser) {
      await browser.close();
    }
  }
}

scrapeFanDuelLines();
