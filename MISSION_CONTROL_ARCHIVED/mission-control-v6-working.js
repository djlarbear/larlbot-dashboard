#!/opt/homebrew/bin/node
/**
 * Mission Control v5 Frontend Server
 * PORT: 5002
 * Serves HTML + handles no-cache headers
 */

const express = require('express');

const PORT = 5002;
const app = express();

// CORS + No-Cache
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
  const html = `<!DOCTYPE html>
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
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
    }

    .header {
      text-align: center;
      margin-bottom: 30px;
    }

    h1 {
      font-size: 2.5em;
      margin-bottom: 10px;
      background: linear-gradient(135deg, #60a5fa, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .subtitle {
      color: #94a3b8;
      font-size: 1.1em;
    }

    .tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 30px;
      border-bottom: 2px solid rgba(148, 163, 184, 0.1);
      flex-wrap: wrap;
    }

    .tab-button {
      padding: 12px 24px;
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 1em;
      border-bottom: 3px solid transparent;
      transition: all 0.3s ease;
    }

    .tab-button:hover {
      color: #e2e8f0;
    }

    .tab-button.active {
      color: #60a5fa;
      border-bottom-color: #60a5fa;
    }

    .tab-content {
      display: none;
      animation: fadeIn 0.3s ease;
    }

    .tab-content.active {
      display: block;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .card {
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
      backdrop-filter: blur(10px);
    }

    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.85em;
      font-weight: 600;
      margin-right: 10px;
    }

    .status-ok { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    .status-pending { background: rgba(234, 179, 8, 0.2); color: #eab308; }
    .status-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    .status-idle { background: rgba(100, 116, 139, 0.2); color: #cbd5e1; }
    .status-running { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }

    .loading {
      text-align: center;
      color: #94a3b8;
      padding: 40px;
      font-size: 1.1em;
    }

    .error {
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      padding: 15px;
      border-radius: 8px;
      margin-bottom: 20px;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .metric {
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 12px;
      padding: 20px;
      text-align: center;
    }

    .metric-value {
      font-size: 2.5em;
      font-weight: 700;
      color: #60a5fa;
      margin: 10px 0;
    }

    .metric-label {
      color: #94a3b8;
      font-size: 0.9em;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }

    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    }

    th {
      background: rgba(30, 41, 59, 0.5);
      font-weight: 600;
      color: #cbd5e1;
    }

    tr:hover {
      background: rgba(59, 130, 246, 0.1);
    }

    .agent-info {
      display: flex;
      justify-content: space-between;
      align-items: start;
      margin-bottom: 10px;
    }

    .agent-name {
      font-weight: 600;
      color: #e2e8f0;
      margin-bottom: 5px;
    }

    .agent-role {
      color: #94a3b8;
      font-size: 0.9em;
      margin-bottom: 8px;
    }

    .agent-activity {
      color: #cbd5e1;
      font-size: 0.9em;
      margin-bottom: 10px;
    }

    .work-item {
      background: rgba(15, 23, 42, 0.5);
      padding: 8px 12px;
      border-left: 3px solid #60a5fa;
      margin: 5px 0;
      border-radius: 4px;
      font-size: 0.85em;
      color: #cbd5e1;
    }

    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: #94a3b8;
    }

    .empty-state-icon {
      font-size: 3em;
      margin-bottom: 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚙️ Mission Control</h1>
      <p class="subtitle">System Status & Command Center</p>
    </div>

    <div class="tabs">
      <button class="tab-button active" onclick="switchTab(event, 'dashboard')">📊 Dashboard</button>
      <button class="tab-button" onclick="switchTab(event, 'cron')">⏰ Cron Jobs</button>
      <button class="tab-button" onclick="switchTab(event, 'kanban')">📋 Work Items</button>
      <button class="tab-button" onclick="switchTab(event, 'ideas')">💡 Ideas</button>
      <button class="tab-button" onclick="switchTab(event, 'agents')">🤖 Agents</button>
    </div>

    <!-- DASHBOARD TAB -->
    <div id="dashboard" class="tab-content active">
      <div class="loading">Loading metrics...</div>
    </div>

    <!-- CRON JOBS TAB -->
    <div id="cron" class="tab-content">
      <div class="loading">Loading cron jobs...</div>
    </div>

    <!-- KANBAN TAB -->
    <div id="kanban" class="tab-content">
      <div class="loading">Loading work items...</div>
    </div>

    <!-- IDEAS TAB -->
    <div id="ideas" class="tab-content">
      <div class="loading">Loading ideas...</div>
    </div>

    <!-- AGENTS TAB -->
    <div id="agents" class="tab-content">
      <div class="loading">Loading agents...</div>
    </div>
  </div>

  <script>
    const API_URL = 'http://' + window.location.hostname + ':5003';

    // Helper: Convert cron expression to readable EST time
    function parseCronToTime(cronExpr) {
      if (!cronExpr) return 'N/A';
      const parts = cronExpr.split(' ');
      if (parts.length < 5) return cronExpr;
      const minute = parts[0];
      const hour = parts[1];
      if (minute.startsWith('*/')) {
        const interval = minute.substring(2);
        return 'Every ' + interval + ' min';
      }
      if (hour.startsWith('*/')) {
        const interval = hour.substring(2);
        return 'Every ' + interval + ' hours';
      }
      if (hour !== '*' && minute !== '*' && !hour.includes(',')) {
        const h = parseInt(hour);
        const m = parseInt(minute);
        if (!isNaN(h) && !isNaN(m)) {
          const displayHour = h === 0 ? 12 : h > 12 ? h - 12 : h;
          const period = h >= 12 ? 'PM' : 'AM';
          const paddedMin = m < 10 ? '0' + m : m;
          return displayHour + ':' + paddedMin + ' ' + period + ' EST';
        }
      }
      if (hour.includes(',')) {
        const hours = hour.split(',').map(h => {
          const hNum = parseInt(h);
          const displayHour = hNum === 0 ? 12 : hNum > 12 ? hNum - 12 : hNum;
          const period = hNum >= 12 ? 'PM' : 'AM';
          return displayHour + ':00 ' + period;
        });
        return 'Multiple: ' + hours.join(', ') + ' EST';
      }
      return cronExpr;
    }

    // Helper: Clean job name
    function cleanJobName(name) {
      if (!name) return 'N/A';
      let cleaned = name.replace(/^SWORD:\s*/, '');
      cleaned = cleaned.replace(/\s*-\s*\d{1,2}:\d{2}\s*(AM|PM|EST).*$/i, '');
      cleaned = cleaned.replace(/\s*-\s*Every.*$/i, '');
      return cleaned;
    }

    // Helper: Toggle cron group
    function toggleCronGroup(groupId) {
      const table = document.getElementById('table-' + groupId);
      const header = document.getElementById('header-' + groupId);
      if (table) {
        if (table.style.display === 'none') {
          table.style.display = 'table';
          if (header) header.innerHTML = '▼ ' + header.textContent.substring(2);
        } else {
          table.style.display = 'none';
          if (header) header.innerHTML = '▶ ' + header.textContent.substring(2);
        }
      }
    }

    function switchTab(event, tabName) {
      event.preventDefault();
      
      // Hide all tabs
      document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
      });
      document.querySelectorAll('.tab-button').forEach(el => {
        el.classList.remove('active');
      });

      // Show selected tab
      document.getElementById(tabName).classList.add('active');
      event.target.classList.add('active');

      // Load tab content
      loadTab(tabName);
    }

    async function loadTab(tabName) {
      const container = document.getElementById(tabName);
      try {
        if (tabName === 'dashboard') {
          loadDashboard(container);
        } else if (tabName === 'cron') {
          loadCronJobs(container);
        } else if (tabName === 'kanban') {
          loadKanban(container);
        } else if (tabName === 'ideas') {
          loadIdeas(container);
        } else if (tabName === 'agents') {
          loadAgents(container);
        }
      } catch (err) {
        container.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
      }
    }

    async function loadDashboard(container) {
      const res = await fetch(API_URL + '/api/dashboard/metrics');
      const data = await res.json();

      if (!data.success) throw new Error(data.error);

      container.innerHTML = '<div class="card"><h2>System Status</h2><div class="metrics-grid"><div class="metric"><div class="metric-label">Uptime</div><div class="metric-value">' + data.system.uptime.formatted + '</div></div><div class="metric"><div class="metric-label">API Calls</div><div class="metric-value">' + data.system.api_calls_today + '</div></div><div class="metric"><div class="metric-label">Status</div><div class="metric-value" style="color: #22c55e;">✓ OK</div></div></div><p style="color: #94a3b8; font-size: 0.9em;">Last updated: ' + new Date(data.timestamp).toLocaleTimeString() + '</p></div>';
    }

    async function loadCronJobs(container) {
      const res = await fetch(API_URL + '/api/cron/jobs');
      const data = await res.json();

      if (!data.success && data.error) {
        container.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
        return;
      }

      const jobs = data.jobs || [];
      if (jobs.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⏰</div><p>No cron jobs configured</p></div>';
        return;
      }

      // Group jobs by agent
      const groups = {'Sword': [], 'System': [], 'Pixel': [], 'Logic': [], 'Jarvis': []};
      jobs.forEach(job => {
        const jobName = job.name || '';
        if (jobName.includes('SWORD') || jobName.includes('Sword')) {
          groups['Sword'].push(job);
        } else if (jobName.includes('System')) {
          groups['System'].push(job);
        } else if (jobName.includes('Pixel')) {
          groups['Pixel'].push(job);
        } else if (jobName.includes('Logic')) {
          groups['Logic'].push(job);
        } else if (jobName.includes('Jarvis')) {
          groups['Jarvis'].push(job);
        } else {
          groups['System'].push(job);
        }
      });

      let html = '<div class="card"><h2>Cron Jobs (' + jobs.length + ')</h2>';
      Object.keys(groups).forEach(groupName => {
        const groupJobs = groups[groupName];
        if (groupJobs.length === 0) return;
        const groupId = groupName.toLowerCase();
        html += '<div style="margin-bottom: 20px;"><h3 id="header-' + groupId + '" style="cursor: pointer; padding: 10px; background: rgba(60, 120, 216, 0.2); border-radius: 6px; margin-bottom: 10px;" onclick="toggleCronGroup(\'' + groupId + '\')">▼ ' + groupName + ' Jobs (' + groupJobs.length + ')</h3>';
        html += '<table id="table-' + groupId + '" style="width: 100%;"><thead><tr><th>Name</th><th>Schedule (EST)</th><th>Status</th></tr></thead><tbody>';
        groupJobs.forEach(job => {
          const statusClass = job.enabled ? 'status-ok' : 'status-error';
          const status = job.enabled ? '✓ Enabled' : '✗ Disabled';
          const schedule = job.schedule?.expr || job.schedule?.kind || 'N/A';
          const cleanName = cleanJobName(job.name);
          const readableTime = parseCronToTime(schedule);
          html += '<tr><td>' + cleanName + '</td><td><code>' + readableTime + '</code></td><td><span class="status-badge ' + statusClass + '">' + status + '</span></td></tr>';
        });
        html += '</tbody></table></div>';
      });
      html += '</div>';
      container.innerHTML = html;
    }

    async function loadKanban(container) {
      const res = await fetch(API_URL + '/api/kanban-items');
      const data = await res.json();

      if (!data.success) throw new Error(data.error);

      const items = data.items || [];
      const statuses = ['ideas', 'ready', 'done'];
      
      let html = '<h2>Work Items</h2>';
      html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">';

      statuses.forEach(status => {
        const statusItems = items.filter(i => i.status === status);
        const icon = status === 'ideas' ? '💡' : status === 'ready' ? '🔧' : '✅';
        
        html += '<div class="card"><h3>' + icon + ' ' + status.toUpperCase() + ' (' + statusItems.length + ')</h3>';
        
        if (statusItems.length === 0) {
          html += '<p style="color: #94a3b8; text-align: center;">No items</p>';
        } else {
          statusItems.forEach(item => {
            html += '<div class="work-item"><strong>' + item.title + '</strong><br>' + (item.description || '(no description)') + '</div>';
          });
        }
        html += '</div>';
      });

      html += '</div>';
      container.innerHTML = html;
    }

    async function loadIdeas(container) {
      const res = await fetch(API_URL + '/api/ideas');
      const data = await res.json();

      if (!data.success) throw new Error(data.error);

      const ideas = data.ideas || [];
      let html = '<div class="card"><h2>Ideas (' + ideas.length + ')</h2>';

      if (ideas.length === 0) {
        html += '<div class="empty-state"><div class="empty-state-icon">💡</div><p>No ideas yet</p></div>';
      } else {
        ideas.forEach(idea => {
          html += '<div style="border-left: 3px solid #8b5cf6; padding: 15px; margin-bottom: 15px; background: rgba(139, 92, 246, 0.1); border-radius: 6px;"><strong>' + idea.title + '</strong>';
          if (idea.description) {
            html += '<p style="color: #cbd5e1; margin-top: 5px;">' + idea.description + '</p>';
          }
          html += '<small style="color: #64748b;">' + new Date(idea.created_at).toLocaleDateString() + '</small></div>';
        });
      }

      html += '</div>';
      container.innerHTML = html;
    }

    async function loadAgents(container) {
      const res = await fetch(API_URL + '/api/agents');
      const data = await res.json();

      if (!data.success) throw new Error(data.error);

      const agents = data.agents || [];
      let html = '<h2>Agents (' + agents.length + ')</h2>';

      if (agents.length === 0) {
        html += '<div class="card"><div class="empty-state"><div class="empty-state-icon">🤖</div><p>No agents configured</p></div></div>';
      } else {
        agents.forEach(agent => {
          const statusClass = 'status-' + (agent.status || 'idle');
          html += '<div class="card"><div class="agent-info"><div><div class="agent-name">' + agent.name + '</div><div class="agent-role">' + (agent.role || 'N/A') + '</div><span class="status-badge ' + statusClass + '">' + (agent.status || 'idle').toUpperCase() + '</span></div></div>';
          
          if (agent.last_activity) {
            html += '<div class="agent-activity">Last: ' + agent.last_activity + '</div>';
          }

          if (agent.recent_work && agent.recent_work.length > 0) {
            html += '<p style="color: #cbd5e1; margin: 10px 0;">Recent Work:</p>';
            agent.recent_work.forEach(work => {
              html += '<div class="work-item">' + work + '</div>';
            });
          }

          html += '</div>';
        });
      }

      container.innerHTML = html;
    }

    // Load dashboard on page load
    window.addEventListener('load', () => {
      loadDashboard(document.getElementById('dashboard'));
    });
  </script>
</body>
</html>`;
  res.send(html);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Mission Control v5 Frontend running on port ${PORT}`);
  console.log(`   • http://127.0.0.1:${PORT}`);
  console.log(`   • http://localhost:${PORT}`);
});
