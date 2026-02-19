#!/opt/homebrew/bin/node
/**
 * Mission Control v6 Frontend - FIXED
 * Larry's Vision: Beautiful Tahoe glass + Full Interactivity
 * Tabs: Dashboard → Agents → Cron Jobs → Ideas → KanBan
 */

const express = require('express');
const PORT = 5002;
const app = express();

app.use((req, res, next) => {
  res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.header('Pragma', 'no-cache');
  res.header('Expires', '0');
  next();
});

app.get('/', (req, res) => {
  res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⚙️ Mission Control</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1a1f35 50%, #0f172a 100%);
      color: #e2e8f0;
      min-height: 100vh;
      padding: 20px;
    }

    .container { max-width: 1600px; margin: 0 auto; }

    .header {
      text-align: center;
      margin-bottom: 40px;
      background: rgba(30, 41, 59, 0.4);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 16px;
      padding: 30px;
    }

    h1 {
      font-size: 2.8em;
      background: linear-gradient(135deg, #60a5fa, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }

    .subtitle { color: #94a3b8; font-size: 1.05em; }

    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 30px;
      border-bottom: 2px solid rgba(148, 163, 184, 0.1);
      overflow-x: auto;
      padding-bottom: 10px;
    }

    .tab-button {
      padding: 12px 24px;
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 0.95em;
      font-weight: 500;
      border-bottom: 3px solid transparent;
      transition: all 0.3s ease;
      white-space: nowrap;
    }

    .tab-button:hover { color: #e2e8f0; }
    .tab-button.active {
      color: #60a5fa;
      border-bottom-color: #60a5fa;
    }

    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.3s ease; }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    /* UNIFORM CARD DESIGN */
    .card {
      background: rgba(30, 41, 59, 0.6);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(148, 163, 184, 0.15);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 20px;
      transition: all 0.3s ease;
      position: relative;
    }

    .card:hover {
      border-color: rgba(148, 163, 184, 0.25);
      background: rgba(30, 41, 59, 0.8);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }

    .card-title { font-size: 1.1em; font-weight: 600; color: #e2e8f0; }

    .status-badge {
      display: inline-block;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.75em;
      font-weight: 600;
    }

    .status-running { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    .status-idle { background: rgba(100, 116, 139, 0.2); color: #cbd5e1; }
    .status-working { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }

    h2 { font-size: 1.6em; margin-bottom: 20px; color: #e2e8f0; }
    h3 { font-size: 1.2em; color: #cbd5e1; margin-bottom: 12px; }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }

    .agent-card {
      background: rgba(59, 130, 246, 0.05);
      border: 1.5px solid rgba(96, 165, 250, 0.2);
      border-radius: 16px;
      padding: 20px;
      position: relative;
      transition: all 0.3s ease;
    }

    .agent-card:hover {
      border-color: rgba(96, 165, 250, 0.4);
      background: rgba(59, 130, 246, 0.1);
    }

    .agent-name { font-weight: 600; font-size: 1.05em; color: #e2e8f0; margin-bottom: 8px; }
    .agent-role { color: #94a3b8; font-size: 0.9em; margin-bottom: 8px; }
    .agent-activity { color: #cbd5e1; font-size: 0.9em; margin: 12px 0; }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }

    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid rgba(148, 163, 184, 0.1);
      font-size: 0.9em;
    }

    th {
      background: rgba(30, 41, 59, 0.5);
      font-weight: 600;
      color: #cbd5e1;
    }

    tr:hover { background: rgba(59, 130, 246, 0.1); }

    .kanban-board {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .kanban-column {
      background: rgba(30, 41, 59, 0.4);
      border: 1.5px solid rgba(148, 163, 184, 0.1);
      border-radius: 16px;
      padding: 16px;
      min-height: 600px;
    }

    .kanban-column h3 {
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 2px solid rgba(148, 163, 184, 0.2);
    }

    .kanban-card {
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 12px;
      cursor: move;
      transition: all 0.2s ease;
      position: relative;
    }

    .kanban-card:hover {
      border-color: rgba(96, 165, 250, 0.4);
      background: rgba(30, 41, 59, 1);
      box-shadow: 0 4px 12px rgba(96, 165, 250, 0.1);
    }

    .kanban-card.expanded {
      background: rgba(59, 130, 246, 0.1);
      border-color: rgba(96, 165, 250, 0.4);
    }

    .kanban-title { font-weight: 600; margin-bottom: 6px; color: #e2e8f0; }
    .kanban-desc { font-size: 0.85em; color: #cbd5e1; margin-bottom: 8px; line-height: 1.4; }

    .kanban-details {
      display: none;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(148, 163, 184, 0.2);
    }

    .kanban-card.expanded .kanban-details { display: block; }

    .kanban-actions {
      display: flex;
      gap: 8px;
      margin-top: 12px;
      flex-wrap: wrap;
      justify-content: center;
    }

    button {
      background: rgba(96, 165, 250, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(96, 165, 250, 0.3);
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85em;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    button:hover {
      background: rgba(96, 165, 250, 0.3);
      border-color: rgba(96, 165, 250, 0.5);
      transform: translateY(-2px);
    }

    button:active { transform: translateY(0); }

    .form-group {
      margin-bottom: 16px;
    }

    label {
      display: block;
      margin-bottom: 6px;
      color: #cbd5e1;
      font-weight: 500;
    }

    input, textarea {
      width: 100%;
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid rgba(148, 163, 184, 0.2);
      color: #e2e8f0;
      padding: 10px 12px;
      border-radius: 8px;
      font-family: inherit;
    }

    input:focus, textarea:focus {
      outline: none;
      border-color: rgba(96, 165, 250, 0.5);
      background: rgba(30, 41, 59, 0.9);
    }

    .button-group {
      display: flex;
      gap: 12px;
      justify-content: center;
      margin-top: 20px;
    }

    .submit-btn {
      width: 100%;
      background: linear-gradient(135deg, rgba(96, 165, 250, 0.3), rgba(139, 92, 246, 0.2));
      color: #60a5fa;
      border: 1px solid rgba(96, 165, 250, 0.3);
      padding: 12px 24px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s ease;
    }

    .submit-btn:hover {
      background: linear-gradient(135deg, rgba(96, 165, 250, 0.4), rgba(139, 92, 246, 0.3));
      border-color: rgba(96, 165, 250, 0.5);
    }

    .loading { text-align: center; color: #94a3b8; padding: 40px; }
    .empty { text-align: center; color: #64748b; padding: 20px; }
    .error { color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 20px; }

    .idea-item {
      border-left: 4px solid #8b5cf6;
      padding: 14px;
      margin-bottom: 12px;
      background: rgba(139, 92, 246, 0.08);
      border-radius: 8px;
      transition: all 0.2s ease;
    }

    .idea-item:hover { background: rgba(139, 92, 246, 0.12); }

    .idea-title { font-weight: 600; color: #e2e8f0; margin-bottom: 6px; }
    .idea-desc { color: #cbd5e1; font-size: 0.9em; margin-bottom: 8px; line-height: 1.4; }
    .idea-date { color: #64748b; font-size: 0.8em; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚙️ Mission Control</h1>
      <p class="subtitle">System Status & Workflow Management</p>
    </div>

    <div class="tabs">
      <button class="tab-button active" onclick="switchTab(event, 'dashboard')">📊 Dashboard</button>
      <button class="tab-button" onclick="switchTab(event, 'agents')">🤖 Agents</button>
      <button class="tab-button" onclick="switchTab(event, 'cron')">⏰ Cron Jobs</button>
      <button class="tab-button" onclick="switchTab(event, 'ideas')">💡 Ideas</button>
      <button class="tab-button" onclick="switchTab(event, 'kanban')">📋 KanBan</button>
    </div>

    <div id="dashboard" class="tab-content active"><div class="loading">Loading...</div></div>
    <div id="agents" class="tab-content"><div class="loading">Loading...</div></div>
    <div id="cron" class="tab-content"><div class="loading">Loading...</div></div>
    <div id="ideas" class="tab-content"><div class="loading">Loading...</div></div>
    <div id="kanban" class="tab-content"><div class="loading">Loading...</div></div>
  </div>

  <script>
    const API = 'http://' + window.location.hostname + ':5003';

    function switchTab(e, tab) {
      e.preventDefault();
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
      document.getElementById(tab).classList.add('active');
      e.target.classList.add('active');
      loadTab(tab);
    }

    async function loadTab(tab) {
      const el = document.getElementById(tab);
      try {
        if (tab === 'dashboard') loadDashboard(el);
        else if (tab === 'agents') loadAgents(el);
        else if (tab === 'cron') loadCronJobs(el);
        else if (tab === 'ideas') loadIdeas(el);
        else if (tab === 'kanban') loadKanban(el);
      } catch (err) {
        el.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
      }
    }

    async function loadDashboard(el) {
      const [metrics, agents] = await Promise.all([
        fetch(API + '/api/dashboard/metrics').then(r => r.json()),
        fetch(API + '/api/agents').then(r => r.json())
      ]);

      let html = '<div class="card"><h2>Agent Status Overview</h2><div class="grid">';
      agents.agents?.forEach(a => {
        const statusClass = 'status-' + a.status;
        html += '<div class="agent-card"><div class="card-header"><div class="card-title">' + a.name + '</div><span class="status-badge ' + statusClass + '">' + a.status.toUpperCase() + '</span></div><div class="agent-role">' + a.role + '</div><div class="agent-activity">Last: ' + a.last_activity + '</div></div>';
      });
      html += '</div></div>';

      html += '<div class="card"><h2>System Status</h2><p style="margin-bottom: 8px;"><strong>API Calls Today:</strong> ' + metrics.system.api_calls_today + '</p><p><strong>Uptime:</strong> ' + metrics.system.uptime.formatted + '</p></div>';

      const kanbanData = JSON.parse(localStorage.getItem('kanban') || '[]');
      const done = kanbanData.filter(i => i.status === 'done').slice(-5);
      html += '<div class="card"><h2>Recently Completed</h2>';
      if (done.length === 0) {
        html += '<p class="empty">No completed tasks yet</p>';
      } else {
        html += '<div>';
        done.reverse().forEach(item => {
          html += '<p style="color: #cbd5e1; margin: 8px 0; padding: 8px 0; border-bottom: 1px solid rgba(148, 163, 184, 0.1);">✅ ' + item.title + '</p>';
        });
        html += '</div>';
      }
      html += '</div>';

      el.innerHTML = html;
    }

    async function loadAgents(el) {
      const data = await fetch(API + '/api/agents').then(r => r.json());
      let html = '<div class="grid">';
      data.agents?.forEach(a => {
        const statusClass = 'status-' + a.status;
        html += '<div class="card agent-card"><div class="card-header"><div><div class="agent-name">' + a.name + '</div><div class="agent-role">' + a.role + '</div></div><span class="status-badge ' + statusClass + '">' + a.status.toUpperCase() + '</span></div><div class="agent-activity">Last Activity: ' + a.last_activity + '</div>';
        if (a.recent_work?.length > 0) {
          html += '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(148, 163, 184, 0.1);">';
          a.recent_work.forEach(w => html += '<p style="font-size: 0.85em; color: #cbd5e1; margin: 4px 0;">▪ ' + w + '</p>');
          html += '</div>';
        }
        html += '</div>';
      });
      html += '</div>';
      el.innerHTML = html;
    }

    function parseCronToTime(cronExpr) {
      if (!cronExpr) return 'Manual';
      
      const parts = cronExpr.trim().split(/\s+/);
      if (parts.length < 5) return cronExpr;
      
      const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
      
      // Handle common patterns
      if (cronExpr.includes('*/15')) return 'Every 15 minutes';
      if (cronExpr.includes('*/30')) return 'Every 30 minutes';
      if (cronExpr.includes('*/6')) return 'Every 6 hours';
      if (cronExpr.includes('*/4')) return 'Every 4 hours';
      if (cronExpr.includes('*/2')) return 'Every 2 hours';
      
      // Handle specific times like "0 23 * * *"
      if (minute !== '*' && hour !== '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
        const h = parseInt(hour);
        const m = parseInt(minute);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const display_h = h > 12 ? h - 12 : (h === 0 ? 12 : h);
        return `${String(display_h).padStart(2, '0')}:${String(m).padStart(2, '0')} ${ampm} EST`;
      }
      
      if (dayOfWeek === '0' && minute !== '*' && hour !== '*') {
        const h = parseInt(hour);
        const m = parseInt(minute);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const display_h = h > 12 ? h - 12 : (h === 0 ? 12 : h);
        return `Sunday ${String(display_h).padStart(2, '0')}:${String(m).padStart(2, '0')} ${ampm} EST`;
      }
      
      return cronExpr;
    }

    function cleanJobName(fullName, groupName) {
      let name = fullName;
      
      // Remove agent prefix if it matches the group
      if (groupName === 'Sword' && name.startsWith('SWORD:')) {
        name = name.substring(6).trim();
      }
      
      // Remove time suffix like " - 11:00 PM" or " - 7:00 AM"
      name = name.replace(/\s*-\s*\d{1,2}:\d{2}\s*(AM|PM)?\s*$/i, '');
      
      // Remove " - Every X" patterns
      name = name.replace(/\s*-\s*Every.*$/i, '');
      
      return name;
    }

    async function loadCronJobs(el) {
      const data = await fetch(API + '/api/cron/jobs').then(r => r.json());
      const jobs = data.jobs || [];

      if (jobs.length === 0) {
        el.innerHTML = '<div class="card"><p class="empty">No cron jobs configured</p></div>';
        return;
      }

      const agentGroups = [
        { name: 'Sword', keywords: ['SWORD', 'sword'] },
        { name: 'System', keywords: ['Pre-Sync', 'GitHub', 'Deploy'] },
        { name: 'Pixel', keywords: ['Pixel', 'pixel', 'Frontend'] },
        { name: 'Logic', keywords: ['Logic', 'logic', 'Backend'] },
        { name: 'Jarvis', keywords: ['Jarvis', 'jarvis', 'CEO'] }
      ];
      let html = '';

      agentGroups.forEach(group => {
        const agentJobs = jobs.filter(j => {
          const jobName = j.name || '';
          return group.keywords.some(kw => jobName.includes(kw));
        });
        if (agentJobs.length === 0) return;

        const groupId = 'cron-' + group.name.toLowerCase();
        html += '<div class="card"><div onclick="toggleCronGroup(\\'' + groupId + '\\')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(96, 165, 250, 0.1); border-radius: 8px; margin-bottom: 16px; user-select: none;"><h3 style="margin: 0; flex: 1;">' + group.name + ' Jobs <span style="color: #94a3b8;">(' + agentJobs.length + ')</span></h3><span style="color: #60a5fa; font-size: 1.2em;" id="cron-toggle-' + groupId + '">▼</span></div><div id="' + groupId + '" style="display: none;"><table><thead><tr><th>Name</th><th>Schedule (EST)</th><th>Status</th></tr></thead><tbody>';
        
        agentJobs.forEach(j => {
          const cleanName = cleanJobName(j.name, group.name);
          const schedule = parseCronToTime(j.schedule?.expr || j.schedule?.kind || 'manual');
          const statusClass = j.enabled ? 'status-running' : 'status-idle';
          html += '<tr><td><strong>' + cleanName + '</strong></td><td><code style="font-size: 0.8em; color: #cbd5e1;">' + schedule + '</code></td><td><span class="status-badge ' + statusClass + '">' + (j.enabled ? 'ON' : 'OFF') + '</span></td></tr>';
        });
        
        html += '</tbody></table></div></div>';
      });

      el.innerHTML = html || '<div class="card"><p class="empty">No jobs found</p></div>';
    }

    function toggleCronGroup(id) {
      const groupEl = document.getElementById(id);
      const toggleEl = document.getElementById('cron-toggle-' + id);
      if (groupEl.style.display === 'none') {
        groupEl.style.display = 'block';
        toggleEl.textContent = '▲';
      } else {
        groupEl.style.display = 'none';
        toggleEl.textContent = '▼';
      }
    }

    async function loadIdeas(el) {
      const data = await fetch(API + '/api/ideas').then(r => r.json());
      let html = '<div class="card"><h2>Create New Idea</h2><form onsubmit="submitIdea(event)"><div class="form-group"><label>Title</label><input type="text" id="idea-title" required></div><div class="form-group"><label>Description</label><textarea id="idea-desc" rows="3"></textarea></div><button type="submit" class="submit-btn">Create Idea</button></form></div>';

      html += '<div class="card"><h2>All Ideas (' + data.ideas.length + ')</h2>';
      if (data.ideas.length === 0) {
        html += '<p class="empty">No ideas yet. Create one above!</p>';
      } else {
        data.ideas.forEach(idea => {
          html += '<div class="idea-item"><div class="idea-title">' + idea.title + '</div><div class="idea-desc">' + idea.description + '</div><div class="idea-date">' + new Date(idea.created_at).toLocaleDateString() + '</div></div>';
        });
      }
      html += '</div>';

      el.innerHTML = html;
    }

    async function loadKanban(el) {
      const ideaRes = await fetch(API + '/api/ideas').then(r => r.json());
      let kanbanData = JSON.parse(localStorage.getItem('kanban') || '[]');

      ideaRes.ideas?.forEach(idea => {
        const exists = kanbanData.find(i => i.id === idea.id);
        if (!exists) {
          kanbanData.push({
            id: idea.id,
            title: idea.title,
            description: idea.description,
            status: 'ideas',
            created_at: idea.created_at,
            updated_at: new Date().toISOString()
          });
        }
      });
      localStorage.setItem('kanban', JSON.stringify(kanbanData));

      const statuses = ['ideas', 'ready', 'in_progress', 'done'];
      const icons = { ideas: '💡', ready: '🔧', in_progress: '▶️', done: '✅' };
      const labels = { ideas: 'Idea', ready: 'Ready', in_progress: 'In Progress', done: 'Done' };

      let html = '<div class="kanban-board">';
      statuses.forEach(status => {
        const items = kanbanData.filter(i => i.status === status);
        html += '<div class="kanban-column"><h3>' + icons[status] + ' ' + labels[status] + ' (' + items.length + ')</h3>';
        items.forEach(item => {
          html += '<div class="kanban-card" id="card-' + item.id + '" onclick="toggleExpand(event, \\'' + item.id + '\\')" draggable="true" ondragstart="dragStart(event)" ondrop="dropCard(event, \\'' + status + '\\')" ondragover="dragOver(event)">';
          html += '<div class="kanban-title">' + item.title + '</div>';
          html += '<div class="kanban-desc">' + (item.description?.substring(0, 50) || 'No description') + '...</div>';
          html += '<div class="kanban-details"><p style="color: #cbd5e1; font-size: 0.85em; margin: 8px 0;"><strong>Description:</strong></p><p style="color: #cbd5e1;">' + item.description + '</p><p style="color: #64748b; font-size: 0.8em; margin-top: 8px;">Created: ' + new Date(item.created_at).toLocaleDateString() + '</p></div>';
          html += '<div class="kanban-actions"><button onclick="editCard(\\'' + item.id + '\\')">✏️ Edit</button><button onclick="deleteCard(\\'' + item.id + '\\')">🗑️ Delete</button></div>';
          html += '</div>';
        });
        html += '</div>';
      });
      html += '</div>';

      el.innerHTML = html;
    }

    function toggleExpand(e, id) {
      if (e.target.closest('button')) return;
      document.getElementById('card-' + id).classList.toggle('expanded');
    }

    function editCard(id) {
      const kanban = JSON.parse(localStorage.getItem('kanban') || '[]');
      const item = kanban.find(i => i.id === id);
      const newTitle = prompt('Edit title:', item.title);
      if (newTitle) {
        item.title = newTitle;
        item.updated_at = new Date().toISOString();
        localStorage.setItem('kanban', JSON.stringify(kanban));
        loadKanban(document.getElementById('kanban'));
      }
    }

    function deleteCard(id) {
      if (confirm('Delete this item?')) {
        const kanban = JSON.parse(localStorage.getItem('kanban') || '[]').filter(i => i.id !== id);
        localStorage.setItem('kanban', JSON.stringify(kanban));
        loadKanban(document.getElementById('kanban'));
      }
    }

    let draggedItem = null;
    function dragStart(e) {
      draggedItem = e.currentTarget.id.replace('card-', '');
    }
    function dragOver(e) { e.preventDefault(); }
    function dropCard(e, status) {
      e.preventDefault();
      if (!draggedItem) return;
      const kanban = JSON.parse(localStorage.getItem('kanban') || '[]');
      const item = kanban.find(i => i.id === draggedItem);
      if (item) {
        item.status = status;
        item.updated_at = new Date().toISOString();
        localStorage.setItem('kanban', JSON.stringify(kanban));
        loadKanban(document.getElementById('kanban'));
      }
      draggedItem = null;
    }

    async function submitIdea(e) {
      e.preventDefault();
      const title = document.getElementById('idea-title').value;
      const desc = document.getElementById('idea-desc').value;
      
      await fetch(API + '/api/ideas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, description: desc }) });
      
      document.getElementById('idea-title').value = '';
      document.getElementById('idea-desc').value = '';
      loadIdeas(document.getElementById('ideas'));
      loadKanban(document.getElementById('kanban'));
    }

    window.addEventListener('load', () => {
      loadDashboard(document.getElementById('dashboard'));
    });
  </script>
</body>
</html>`);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Mission Control v6 Frontend running on :${PORT}`);
});
