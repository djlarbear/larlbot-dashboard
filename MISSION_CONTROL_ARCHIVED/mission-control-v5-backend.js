#!/opt/homebrew/bin/node
/**
 * Mission Control v5 Backend (WORKING VERSION)
 * PORT: 5003
 * PURPOSE: Serve real APIs for Dashboard, Cron Jobs, KanBan, Ideas, and Agents
 * 
 * This version uses DIRECT system calls (openclaw cron list, etc.)
 * No broken gateway API proxies.
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { v4: uuidv4 } = require('uuid');

const PORT = 5003;
const DATA_DIR = path.join(__dirname, 'data');
const KANBAN_FILE = path.join(DATA_DIR, 'kanban.json');
const IDEAS_FILE = path.join(DATA_DIR, 'ideas.json');
const AGENTS_FILE = path.join(DATA_DIR, 'agents.json');

const app = express();
const SYSTEM_START_TIME = Date.now();
let apiCallCount = 0;

// Middleware
app.use(cors());
app.use(express.json());
app.use((req, res, next) => {
  res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.header('Pragma', 'no-cache');
  res.header('Expires', '0');
  next();
});

// Ensure data directory
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// ===========================
// FILE I/O HELPERS
// ===========================

function readJSON(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return [];
    }
    const data = fs.readFileSync(filePath, 'utf8');
    return data ? JSON.parse(data) : [];
  } catch (err) {
    console.error(`[readJSON] Error reading ${filePath}:`, err.message);
    return [];
  }
}

function writeJSON(filePath, data) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
    return true;
  } catch (err) {
    console.error(`[writeJSON] Error writing ${filePath}:`, err.message);
    return false;
  }
}

// ===========================
// CRON JOBS API (Uses openclaw cron list --json)
// ===========================

app.get('/api/cron/jobs', (req, res) => {
  apiCallCount++;
  try {
    const output = execSync('/opt/homebrew/bin/openclaw cron list --json 2>&1', {
      encoding: 'utf8',
      timeout: 5000,
    });

    const data = JSON.parse(output);
    res.json({
      success: true,
      jobs: data.jobs || [],
      count: (data.jobs || []).length,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error('[cron/jobs] Error:', err.message);
    res.status(500).json({
      error: 'Failed to fetch cron jobs',
      details: err.message,
      fallback: [],
    });
  }
});

// ===========================
// DASHBOARD METRICS
// ===========================

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
      start_time: new Date(SYSTEM_START_TIME).toISOString(),
    },
    note: 'Mission Control local metrics only',
  });
});

// ===========================
// KANBAN ITEMS
// ===========================

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
  const { title, description = '', status = 'ideas', priority = 'medium' } = req.body;

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

// ===========================
// IDEAS
// ===========================

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

// ===========================
// AGENTS (NEW)
// ===========================

app.get('/api/agents', (req, res) => {
  apiCallCount++;
  const agents = readJSON(AGENTS_FILE);
  res.json({
    success: true,
    agents,
    count: agents.length,
    timestamp: new Date().toISOString(),
  });
});

app.post('/api/agents', (req, res) => {
  apiCallCount++;
  const { name, role, status = 'idle', last_activity = '', recent_work = [] } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'Name required' });
  }

  const agents = readJSON(AGENTS_FILE);
  const newAgent = {
    id: uuidv4(),
    name,
    role,
    status,
    last_activity,
    recent_work,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  agents.push(newAgent);
  if (writeJSON(AGENTS_FILE, agents)) {
    return res.status(201).json({ success: true, agent: newAgent });
  }

  res.status(500).json({ error: 'Failed to save' });
});

app.put('/api/agents/:id', (req, res) => {
  apiCallCount++;
  const { id } = req.params;
  const agents = readJSON(AGENTS_FILE);
  const index = agents.findIndex(a => a.id === id);

  if (index === -1) {
    return res.status(404).json({ error: 'Not found' });
  }

  agents[index] = {
    ...agents[index],
    ...req.body,
    updated_at: new Date().toISOString(),
  };

  if (writeJSON(AGENTS_FILE, agents)) {
    return res.json({ success: true, agent: agents[index] });
  }

  res.status(500).json({ error: 'Failed to save' });
});

// ===========================
// HEALTH CHECK
// ===========================

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: formatUptime(SYSTEM_START_TIME),
    timestamp: new Date().toISOString(),
  });
});

// ===========================
// UTILITIES
// ===========================

function formatUptime(startTime) {
  const seconds = Math.floor((Date.now() - startTime) / 1000);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

// ===========================
// START SERVER
// ===========================

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Mission Control v5 Backend running on port ${PORT}`);
  console.log(`   • http://127.0.0.1:${PORT}`);
  console.log(`   • http://localhost:${PORT}`);
  console.log('\n📡 Available APIs:');
  console.log(`   • /api/dashboard/metrics`);
  console.log(`   • /api/cron/jobs`);
  console.log(`   • /api/kanban-items`);
  console.log(`   • /api/ideas`);
  console.log(`   • /api/agents`);
  console.log(`   • /health`);
});
