#!/usr/bin/env node
/**
 * Mission Control Backend API Server
 * PORT: 5003
 * SCOPE: LOCAL + TAILSCALE
 * PURPOSE: Serve KanBan, Ideas, Cron metadata, system metrics (NO Sword data)
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { v4: uuidv4 } = require('uuid');

const PORT = 5003;
const DATA_DIR = path.join(__dirname, 'data');
const app = express();

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Middleware
app.use(cors());
app.use(express.json());
app.use((req, res, next) => {
  res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.header('Pragma', 'no-cache');
  res.header('Expires', '0');
  next();
});

// Data file paths
const KANBAN_FILE = path.join(DATA_DIR, 'kanban.json');
const IDEAS_FILE = path.join(DATA_DIR, 'ideas.json');

const SYSTEM_START_TIME = new Date();
let apiCallCount = 0;

// Utility functions
function readJSON(filePath, defaultValue = []) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  } catch (err) {
    console.error(`Error reading ${filePath}:`, err.message);
  }
  return defaultValue;
}

function writeJSON(filePath, data) {
  try {
    const tmpFile = filePath + '.tmp';
    fs.writeFileSync(tmpFile, JSON.stringify(data, null, 2));
    fs.renameSync(tmpFile, filePath);
    return true;
  } catch (err) {
    console.error(`Error writing ${filePath}:`, err.message);
    return false;
  }
}

// ===========================
// API Endpoints
// ===========================

// Dashboard Metrics (LOCAL ONLY - no Sword data)
app.get('/api/dashboard/metrics', (req, res) => {
  apiCallCount++;
  res.json({
    success: true,
    timestamp: new Date().toISOString(),
    system: {
      uptime: {
        seconds: Math.floor((Date.now() - SYSTEM_START_TIME) / 1000),
        formatted: formatUptime(SYSTEM_START_TIME),
      },
      api_calls_today: apiCallCount,
      start_time: SYSTEM_START_TIME.toISOString(),
    },
    note: 'Mission Control local metrics only - no Sword betting data',
  });
});

// Cron Jobs (fetch from Gateway)
app.get('/api/cron/jobs', async (req, res) => {
  apiCallCount++;
  try {
    // Fetch from gateway
    const gatewayRes = await fetch('http://127.0.0.1:18789/api/cron/jobs', {
      headers: { 'Authorization': 'Bearer ' + (process.env.OPENCLAW_TOKEN || '') },
    }).catch(() => null);

    if (gatewayRes?.ok) {
      const data = await gatewayRes.json();
      return res.json({
        success: true,
        jobs: data.jobs || [],
        count: (data.jobs || []).length,
        source: 'gateway',
        timestamp: new Date().toISOString(),
      });
    }

    // Fallback if gateway unavailable
    res.json({
      success: true,
      jobs: [],
      count: 0,
      source: 'offline',
      message: 'Gateway unavailable - no cron data',
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// KanBan Items
app.get('/api/kanban-items', (req, res) => {
  apiCallCount++;
  const items = readJSON(KANBAN_FILE);
  const status = req.query.status;

  const filtered = status ? items.filter(i => i.status === status) : items;

  res.json({
    success: true,
    items: filtered,
    count: filtered.length,
    timestamp: new Date().toISOString(),
  });
});

app.post('/api/kanban-items', (req, res) => {
  apiCallCount++;
  const { title, description = '', status = 'ideas', priority = 'medium', flags = [] } = req.body;

  if (!title) {
    return res.status(400).json({ error: 'Title required' });
  }

  const items = readJSON(KANBAN_FILE);
  const newItem = {
    id: uuidv4(),
    title,
    description,
    status,
    priority,
    flags,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  items.push(newItem);
  if (writeJSON(KANBAN_FILE, items)) {
    return res.status(201).json({ success: true, item: newItem });
  }

  res.status(500).json({ error: 'Failed to save' });
});

app.put('/api/kanban-items/:id', (req, res) => {
  apiCallCount++;
  const { id } = req.params;
  const items = readJSON(KANBAN_FILE);
  const index = items.findIndex(i => i.id === id);

  if (index === -1) {
    return res.status(404).json({ error: 'Not found' });
  }

  items[index] = {
    ...items[index],
    ...req.body,
    updated_at: new Date().toISOString(),
  };

  if (writeJSON(KANBAN_FILE, items)) {
    return res.json({ success: true, item: items[index] });
  }

  res.status(500).json({ error: 'Failed to save' });
});

// Ideas
app.get('/api/ideas', (req, res) => {
  apiCallCount++;
  const ideas = readJSON(IDEAS_FILE);
  res.json({
    success: true,
    ideas,
    count: ideas.length,
    timestamp: new Date().toISOString(),
  });
});

app.post('/api/ideas', (req, res) => {
  apiCallCount++;
  const { title, description = '' } = req.body;

  if (!title) {
    return res.status(400).json({ error: 'Title required' });
  }

  const ideas = readJSON(IDEAS_FILE);
  const newIdea = {
    id: uuidv4(),
    title,
    description,
    created_at: new Date().toISOString(),
  };

  ideas.push(newIdea);
  if (writeJSON(IDEAS_FILE, ideas)) {
    return res.status(201).json({ success: true, idea: newIdea });
  }

  res.status(500).json({ error: 'Failed to save' });
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: formatUptime(SYSTEM_START_TIME),
    timestamp: new Date().toISOString(),
  });
});

// ===========================
// Utilities
// ===========================

function formatUptime(startTime) {
  const seconds = Math.floor((Date.now() - startTime) / 1000);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

// ===========================
// Start Server - BIND TO 0.0.0.0 FOR NETWORK ACCESS
// ===========================

app.listen(PORT, '0.0.0.0', () => {
  const interfaces = os.networkInterfaces();
  let ips = ['127.0.0.1:' + PORT];
  
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        ips.push(iface.address + ':' + PORT);
      }
    }
  }
  
  console.log(`✅ Mission Control Backend running on port ${PORT}`);
  console.log(`   Accessible at:`);
  ips.forEach(ip => console.log(`   • http://${ip}`));
  console.log('   Scope: LOCAL + TAILSCALE (no Sword data mixing)');
  console.log('   APIs: /api/dashboard/metrics, /api/cron/jobs, /api/kanban-items, /api/ideas');
});
