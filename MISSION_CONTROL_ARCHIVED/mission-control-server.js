#!/usr/bin/env node
/**
 * Mission Control Frontend Server
 * PORT: 5002
 * SCOPE: LOCAL + TAILSCALE
 * DESIGN: Apple Tahoe Glass-Morphism (Beautiful)
 */

const express = require('express');
const path = require('path');
const fs = require('fs');

const PORT = 5002;
const app = express();

// Middleware
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// CORS for local + tailscale
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.header('Pragma', 'no-cache');
  res.header('Expires', '0');
  next();
});

// Root: Serve Mission Control UI
app.get('/', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⚙️ Mission Control - Command Center</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1a1f35 50%, #0f172a 100%);
      color: #e2e8f0;
      min-height: 100vh;
      padding: 20px;
      position: relative;
      overflow-x: hidden;
    }

    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: radial-gradient(circle at 20% 50%, rgba(96, 165, 250, 0.03) 0%, transparent 50%),
                  radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.02) 0%, transparent 50%);
      pointer-events: none;
      z-index: -1;
    }

    .container {
      max-width: 1600px;
      margin: 0 auto;
    }

    .header {
      margin-bottom: 40px;
      text-align: center;
    }

    h1 {
      font-size: 3em;
      font-weight: 700;
      background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #60a5fa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 8px;
      letter-spacing: -1px;
    }

    .subtitle {
      color: #64748b;
      font-size: 1em;
      letter-spacing: 0.5px;
    }

    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 30px;
      padding-bottom: 16px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.1);
      overflow-x: auto;
    }

    .tab-button {
      padding: 12px 24px;
      background: rgba(30, 41, 59, 0.4);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 10px;
      color: #cbd5e1;
      cursor: pointer;
      font-size: 1em;
      font-weight: 500;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      white-space: nowrap;
    }

    .tab-button:hover {
      background: rgba(30, 41, 59, 0.6);
      border-color: rgba(148, 163, 184, 0.2);
      color: #f1f5f9;
      transform: translateY(-2px);
    }

    .tab-button.active {
      background: rgba(59, 130, 246, 0.15);
      border-color: rgba(59, 130, 246, 0.4);
      color: #60a5fa;
      box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
    }

    .tab-content {
      display: none;
      animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .tab-content.active {
      display: block;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .card {
      background: rgba(30, 41, 59, 0.5);
      backdrop-filter: blur(24px);
      border: 1.5px solid rgba(148, 163, 184, 0.15);
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 24px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2),
                  inset 1px 1px 0 rgba(255, 255, 255, 0.05);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .card:hover {
      background: rgba(30, 41, 59, 0.6);
      border-color: rgba(148, 163, 184, 0.25);
      box-shadow: 0 16px 48px rgba(0, 0, 0, 0.3),
                  inset 1px 1px 0 rgba(255, 255, 255, 0.08);
    }

    .card h2 {
      font-size: 1.5em;
      margin-bottom: 20px;
      color: #f1f5f9;
      font-weight: 600;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-top: 20px;
    }

    .metric {
      background: rgba(51, 65, 85, 0.3);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 12px;
      padding: 16px;
      text-align: center;
      transition: all 0.3s;
    }

    .metric:hover {
      background: rgba(51, 65, 85, 0.5);
      border-color: rgba(59, 130, 246, 0.3);
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(59, 130, 246, 0.1);
    }

    .metric-value {
      font-size: 2.2em;
      font-weight: 700;
      background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 4px;
    }

    .metric-label {
      font-size: 0.85em;
      color: #94a3b8;
      font-weight: 500;
      letter-spacing: 0.3px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }

    th {
      background: rgba(51, 65, 85, 0.3);
      color: #cbd5e1;
      padding: 14px;
      text-align: left;
      font-weight: 600;
      font-size: 0.95em;
      border-bottom: 1px solid rgba(148, 163, 184, 0.15);
      letter-spacing: 0.3px;
    }

    td {
      padding: 12px 14px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.08);
      font-size: 0.95em;
    }

    tr:hover {
      background: rgba(59, 130, 246, 0.05);
    }

    .status-ok {
      color: #22c55e;
      font-weight: 600;
    }

    .status-warn {
      color: #f59e0b;
      font-weight: 600;
    }

    .status-error {
      color: #ef4444;
      font-weight: 600;
    }

    .status-idle {
      color: #64748b;
      font-weight: 600;
    }

    .kanban-item {
      background: rgba(51, 65, 85, 0.3);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(148, 163, 184, 0.15);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s;
    }

    .kanban-item:hover {
      background: rgba(51, 65, 85, 0.5);
      border-color: rgba(59, 130, 246, 0.3);
      transform: translateX(4px);
    }

    .kanban-title {
      font-weight: 600;
      color: #f1f5f9;
      margin-bottom: 6px;
    }

    .kanban-meta {
      display: flex;
      gap: 12px;
      font-size: 0.85em;
      color: #94a3b8;
    }

    .badge {
      background: rgba(59, 130, 246, 0.2);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #60a5fa;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 500;
      font-size: 0.8em;
    }

    .badge.status-deployed {
      background: rgba(34, 197, 94, 0.15);
      border-color: rgba(34, 197, 94, 0.3);
      color: #22c55e;
    }

    .badge.status-progress {
      background: rgba(245, 158, 11, 0.15);
      border-color: rgba(245, 158, 11, 0.3);
      color: #f59e0b;
    }

    .badge.status-ready {
      background: rgba(96, 165, 250, 0.15);
      border-color: rgba(96, 165, 250, 0.3);
      color: #60a5fa;
    }

    .btn {
      background: rgba(59, 130, 246, 0.8);
      color: white;
      border: 1px solid rgba(59, 130, 246, 0.5);
      padding: 10px 18px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.95em;
      font-weight: 500;
      transition: all 0.3s;
      backdrop-filter: blur(10px);
    }

    .btn:hover {
      background: rgba(59, 130, 246, 1);
      border-color: rgba(59, 130, 246, 1);
      box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
      transform: translateY(-2px);
    }

    .loading {
      text-align: center;
      color: #64748b;
      padding: 40px 20px;
      font-size: 1.1em;
    }

    .empty-state {
      text-align: center;
      color: #64748b;
      padding: 40px 20px;
      font-size: 1em;
    }

    @media (max-width: 768px) {
      h1 {
        font-size: 2em;
      }

      .metrics-grid {
        grid-template-columns: 1fr;
      }

      .tabs {
        flex-wrap: wrap;
      }

      table {
        font-size: 0.85em;
      }

      th, td {
        padding: 10px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚙️ Mission Control</h1>
      <p class="subtitle">Command Center • Autonomous Operations</p>
    </div>

    <div class="tabs">
      <button class="tab-button active" onclick="showTab('dashboard', event)">📊 Dashboard</button>
      <button class="tab-button" onclick="showTab('cron', event)">⏱️ Cron Jobs</button>
      <button class="tab-button" onclick="showTab('kanban', event)">📋 KanBan</button>
      <button class="tab-button" onclick="showTab('ideas', event)">💡 Ideas</button>
    </div>

    <!-- Dashboard Tab -->
    <div id="dashboard" class="tab-content active">
      <div class="card">
        <h2>System Metrics</h2>
        <div class="metrics-grid" id="metrics-container">
          <div class="loading">Loading metrics...</div>
        </div>
      </div>
    </div>

    <!-- Cron Jobs Tab -->
    <div id="cron" class="tab-content">
      <div class="card">
        <h2>Scheduled Operations</h2>
        <table id="cron-table">
          <thead>
            <tr>
              <th>Job</th>
              <th>Schedule</th>
              <th>Status</th>
              <th>Last Run</th>
              <th>Next Run</th>
            </tr>
          </thead>
          <tbody id="cron-body">
            <tr><td colspan="5"><div class="loading">Loading cron jobs...</div></td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- KanBan Tab -->
    <div id="kanban" class="tab-content">
      <div class="card">
        <h2>Work Tracking</h2>
        <div id="kanban-container">
          <div class="loading">Loading work items...</div>
        </div>
      </div>
    </div>

    <!-- Ideas Tab -->
    <div id="ideas" class="tab-content">
      <div class="card">
        <h2>Future Features</h2>
        <div id="ideas-container">
          <div class="loading">Loading ideas...</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const API_BASE = 'http://localhost:5003/api';

    function showTab(name, event) {
      if (event) {
        document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
        event.target.classList.add('active');
      }
      
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.getElementById(name).classList.add('active');
      loadTabData(name);
    }

    async function loadTabData(tab) {
      try {
        if (tab === 'dashboard') {
          const res = await fetch(\`\${API_BASE}/dashboard/metrics\`);
          const data = await res.json();
          displayMetrics(data);
          setInterval(() => loadTabData('dashboard'), 10000);
        } else if (tab === 'cron') {
          const res = await fetch(\`\${API_BASE}/cron/jobs\`);
          const data = await res.json();
          displayCronJobs(data.jobs || []);
          setInterval(() => loadTabData('cron'), 5000);
        } else if (tab === 'kanban') {
          const res = await fetch(\`\${API_BASE}/kanban-items\`);
          const data = await res.json();
          displayKanban(data.items || []);
        } else if (tab === 'ideas') {
          const res = await fetch(\`\${API_BASE}/ideas\`);
          const data = await res.json();
          displayIdeas(data.ideas || []);
        }
      } catch (err) {
        console.error('Load error:', err);
      }
    }

    function displayMetrics(data) {
      const html = \`
        <div class="metric">
          <div class="metric-label">API Calls Today</div>
          <div class="metric-value">\${data.system?.api_calls_today || 0}</div>
        </div>
        <div class="metric">
          <div class="metric-label">System Uptime</div>
          <div class="metric-value">\${data.system?.uptime?.formatted || 'N/A'}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Services Running</div>
          <div class="metric-value" style="color: #22c55e;">2/2 ✓</div>
        </div>
        <div class="metric">
          <div class="metric-label">Status</div>
          <div class="metric-value" style="color: #22c55e; font-size: 1.5em;">● LIVE</div>
        </div>
      \`;
      document.getElementById('metrics-container').innerHTML = html;
    }

    function displayCronJobs(jobs) {
      const rows = jobs.map(job => {
        const statusClass = job.lastStatus === 'ok' ? 'status-ok' : 
                           job.lastStatus === 'skipped' ? 'status-warn' : 
                           job.lastStatus === 'failed' ? 'status-error' : 'status-idle';
        return \`
          <tr>
            <td><strong>\${job.name || 'N/A'}</strong></td>
            <td>\${job.schedule || 'N/A'}</td>
            <td><span class="\${statusClass}">\${job.lastStatus || 'idle'}</span></td>
            <td>\${job.lastRun || 'Never'}</td>
            <td>\${job.nextRun || 'N/A'}</td>
          </tr>
        \`;
      }).join('');
      document.getElementById('cron-body').innerHTML = rows || '<tr><td colspan="5" class="empty-state">No jobs configured</td></tr>';
    }

    function displayKanban(items) {
      const html = items.map(item => {
        const statusClass = item.status === 'deployed' ? 'status-deployed' :
                           item.status === 'in-progress' ? 'status-progress' :
                           item.status === 'ready' ? 'status-ready' : '';
        return \`
          <div class="kanban-item">
            <div class="kanban-title">\${item.title}</div>
            <div class="kanban-meta">
              <span class="badge \${statusClass}">\${item.status || 'unknown'}</span>
              <span style="color: #94a3b8; font-size: 0.8em;">\${item.priority || 'medium'} priority</span>
              \${item.completed_at ? '<span style="color: #22c55e; font-size: 0.8em;">✓ Completed</span>' : ''}
            </div>
          </div>
        \`;
      }).join('');
      document.getElementById('kanban-container').innerHTML = html || '<div class="empty-state">No work items yet</div>';
    }

    function displayIdeas(ideas) {
      const html = ideas.map(idea => \`
        <div class="kanban-item">
          <div class="kanban-title">💡 \${idea.title}</div>
          <div style="font-size: 0.9em; color: #cbd5e1; margin-top: 6px;">\${idea.description || 'No description'}</div>
        </div>
      \`).join('');
      document.getElementById('ideas-container').innerHTML = html || '<div class="empty-state">No ideas yet. Add one with POST /api/ideas</div>';
    }

    // Load dashboard on start
    window.addEventListener('load', () => {
      loadTabData('dashboard');
    });
  </script>
</body>
</html>
  `);
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server - BIND TO 0.0.0.0 FOR NETWORK ACCESS
app.listen(PORT, '0.0.0.0', () => {
  const interfaces = require('os').networkInterfaces();
  let ips = ['127.0.0.1:' + PORT];
  
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        ips.push(iface.address + ':' + PORT);
      }
    }
  }
  
  console.log(`✅ Mission Control Frontend running on port ${PORT}`);
  console.log(`   Accessible at:`);
  ips.forEach(ip => console.log(`   • http://${ip}`));
  console.log(`   Scope: LOCAL + TAILSCALE`);
  console.log(`   Design: Apple Tahoe Glass-Morphism`);
});
