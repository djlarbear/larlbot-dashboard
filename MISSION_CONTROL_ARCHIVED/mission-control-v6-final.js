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
      <button class="tab-button active" onclick="handleTabClick(event, 'dashboard')">📊 Dashboard</button>
      <button class="tab-button" onclick="handleTabClick(event, 'cron')">⏰ Cron Jobs</button>
      <button class="tab-button" onclick="handleTabClick(event, 'kanban')">📋 Work Items</button>
      <button class="tab-button" onclick="handleTabClick(event, 'ideas')">💡 Ideas</button>
      <button class="tab-button" onclick="handleTabClick(event, 'agents')">🤖 Agents</button>
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

    // Wrapper to handle async onclick
    window.handleTabClick = function(event, tabName) {
      switchTab(event, tabName).catch(err => {
        console.error('switchTab error:', err);
      });
    };

    async function switchTab(event, tabName) {
      event.preventDefault();
      
      // Hide all tabs
      document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
      });
      document.querySelectorAll('.tab-button').forEach(el => {
        el.classList.remove('active');
      });

      // Show selected tab
      const tabContainer = document.getElementById(tabName);
      const tabButton = event.target;
      
      tabContainer.classList.add('active');
      tabButton.classList.add('active');

      // Show loading state
      tabContainer.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 40px;">Loading...</div>';

      // Load tab content (with proper error handling)
      try {
        await loadTab(tabName);
      } catch (err) {
        console.error('Tab load error:', err);
        tabContainer.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;">Error loading ' + tabName + ': ' + err.message + '</div>';
      }
    }

    async function loadTab(tabName) {
      const container = document.getElementById(tabName);
      try {
        if (tabName === 'dashboard') {
          await loadDashboard(container);
        } else if (tabName === 'cron') {
          await loadCronJobs(container);
        } else if (tabName === 'kanban') {
          await loadKanban(container);
        } else if (tabName === 'ideas') {
          await loadIdeas(container);
        } else if (tabName === 'agents') {
          await loadAgents(container);
        }
      } catch (err) {
        console.error('Load tab error:', err);
        container.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;">Error: ' + err.message + '</div>';
      }
    }

    async function loadDashboard(container) {
      try {
        const res = await fetch(API_URL + '/api/dashboard/metrics');
        if (!res.ok) throw new Error('API returned ' + res.status);
        const data = await res.json();

        if (!data.success) throw new Error(data.error || 'Unknown error');
        if (!data.system) throw new Error('No system data in response');

        const uptime = data.system.uptime?.formatted || 'unknown';
        const calls = data.system.api_calls_today || 0;

        container.innerHTML = '<div class="card"><h2>System Status</h2><div class="metrics-grid"><div class="metric"><div class="metric-label">Uptime</div><div class="metric-value">' + uptime + '</div></div><div class="metric"><div class="metric-label">API Calls</div><div class="metric-value">' + calls + '</div></div><div class="metric"><div class="metric-label">Status</div><div class="metric-value" style="color: #22c55e;">✓ OK</div></div></div><p style="color: #94a3b8; font-size: 0.9em;">Last updated: ' + new Date(data.timestamp).toLocaleTimeString() + '</p></div>';
      } catch (err) {
        console.error('loadDashboard error:', err);
        container.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444;"><strong>Dashboard Error</strong><br>' + err.message + '<br><small>(Check browser console for details)</small></div>';
      }
    }

    function parseCronToTime(cronExpr) {
      if (!cronExpr) return 'Manual';
      const parts = cronExpr.trim().split(/\s+/);
      if (parts.length < 5) return cronExpr;
      const [minute, hour] = parts;
      if (cronExpr.includes('*/15')) return 'Every 15 min';
      if (cronExpr.includes('*/30')) return 'Every 30 min';
      if (cronExpr.includes('*/6')) return 'Every 6h';
      if (cronExpr.includes('*/4')) return 'Every 4h';
      if (minute !== '*' && hour !== '*') {
        const h = parseInt(hour);
        const m = parseInt(minute);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const display_h = h > 12 ? h - 12 : (h === 0 ? 12 : h);
        return display_h + ':' + String(m).padStart(2, '0') + ' ' + ampm + ' EST';
      }
      return cronExpr;
    }

    function cleanJobName(fullName, groupName) {
      let name = fullName;
      if (groupName === 'Sword' && name.startsWith('SWORD:')) name = name.substring(6).trim();
      name = name.replace(/\s*-\s*\d{1,2}:\d{2}\s*(AM|PM)?\s*$/i, '');
      name = name.replace(/\s*-\s*Every.*$/i, '');
      return name;
    }

    async function loadCronJobs(container) {
      try {
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

        const agentGroups = [
          { name: 'Sword', keywords: ['SWORD', 'sword'] },
          { name: 'System', keywords: ['Pre-Sync', 'GitHub', 'Deploy'] },
          { name: 'Pixel', keywords: ['Pixel', 'pixel'] },
          { name: 'Logic', keywords: ['Logic', 'logic'] },
          { name: 'Jarvis', keywords: ['Jarvis', 'jarvis'] }
        ];
        let html = '';

        agentGroups.forEach(group => {
          const agentJobs = jobs.filter(j => group.keywords.some(kw => j.name?.includes(kw)));
          if (agentJobs.length === 0) return;
          const groupId = 'cron-' + group.name.toLowerCase();
          html += '<div class="card"><div onclick="toggleCronGroup(\'' + groupId + '\')" style="cursor: pointer; display: flex; justify-content: space-between; padding: 12px; background: rgba(96, 165, 250, 0.1); border-radius: 8px; margin-bottom: 12px; user-select: none;"><h3 style="margin: 0; flex: 1; font-size: 1.1em;">' + group.name + ' Jobs <span style="color: #94a3b8;">(' + agentJobs.length + ')</span></h3><span id="cron-toggle-' + groupId + '" style="color: #60a5fa;">▼</span></div>';
          html += '<div id="' + groupId + '" style="display: none;"><table style="margin-top: 8px;"><thead><tr><th>Name</th><th>Schedule (EST)</th><th>Status</th></tr></thead><tbody>';
          agentJobs.forEach(j => {
            const cleanName = cleanJobName(j.name, group.name);
            const schedule = parseCronToTime(j.schedule?.expr);
            const statusClass = j.enabled ? 'status-ok' : 'status-error';
            const status = j.enabled ? 'ON' : 'OFF';
            html += '<tr><td>' + cleanName + '</td><td><code style="font-size: 0.85em;">' + schedule + '</code></td><td><span class="status-badge ' + statusClass + '">' + status + '</span></td></tr>';
          });
          html += '</tbody></table></div></div>';
        });

        container.innerHTML = html;
      } catch (err) {
        container.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;">Error loading cron jobs: ' + err.message + '</div>';
      }
    }

    function toggleCronGroup(id) {
      const el = document.getElementById(id);
      const toggle = document.getElementById('cron-toggle-' + id);
      if (el.style.display === 'none') {
        el.style.display = 'block';
        toggle.textContent = '▲';
      } else {
        el.style.display = 'none';
        toggle.textContent = '▼';
      }
    }

    async function loadKanban(container) {
      try {
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
      } catch (err) {
        container.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;">Error loading work items: ' + err.message + '</div>';
      }
    }

    async function loadIdeas(container) {
      try {
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
      } catch (err) {
        container.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;">Error loading ideas: ' + err.message + '</div>';
      }
    }

    async function loadAgents(container) {
      try {
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
      } catch (err) {
        container.innerHTML = '<div style="color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;">Error loading agents: ' + err.message + '</div>';
      }
    }

    // Load dashboard on page load
    window.addEventListener('load', async () => {
      try {
        await loadDashboard(document.getElementById('dashboard'));
      } catch (err) {
        console.error('Failed to load dashboard:', err);
        document.getElementById('dashboard').innerHTML = '<div style="color: #ef4444;">Failed to load dashboard: ' + err.message + '</div>';
      }
    });
  </script>
</body>
</html>`);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Mission Control v6 Frontend running on port ${PORT}`);
  console.log(`   • http://127.0.0.1:${PORT}`);
  console.log(`   • http://localhost:${PORT}`);
});
