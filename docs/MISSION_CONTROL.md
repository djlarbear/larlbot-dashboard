# Mission Control - OpenClaw GUI Documentation

## Overview
Mission Control is a self-hosted web dashboard for managing OpenClaw AI agents. Created by [@robsannaa](https://github.com/robsannaa/openclaw-mission-control), it provides a visual interface for everything that normally requires CLI commands.

**URL:** http://127.0.0.1:3000 (dev) or http://127.0.0.1:3333 (production)  
**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui  
**Privacy:** 100% local - no data leaves your machine

---

## Key Features (Organized by Section)

### 🏠 Dashboard
**Location:** `/?section=dashboard`

**Overview Cards:**
- Gateway status (online/offline, version, port, ping time)
- Agent count and token usage
- Cron job health (2/4 OK)
- Device count (paired nodes)
- Skills installed

**Real-Time Monitoring:**
- CPU usage (89%, 10 cores, Apple M4)
- Memory breakdown (App, Wired, Compressed, Cached Files, Free)
- Disk usage (42.6 GB / 228.3 GB)
- System uptime, processes, hostname

**Recent Cron Results:**
- Shows last 5-10 cron runs with timestamps
- Click to jump to job editor
- Visual indicators for success/failure/warnings

**Gateway Log:**
- Live websocket activity stream
- Last ~30 log entries with timestamps

**OpenClaw Storage:**
- Workspace size (32 MB)
- File count (12,407 files)
- Session count (4 sessions, 7 MB)
- Today's log size (2 MB)

---

### 💬 Chat
**Location:** `/?section=chat`

Talk directly to your OpenClaw agents from the browser. No need to use CLI or external chat apps.

---

### 📡 Channels
**Location:** `/?section=channels`

Manage messaging integrations:
- Telegram
- Discord
- WhatsApp
- Signal
- IRC
- Google Chat
- Slack
- iMessage

View connection status, configure credentials, enable/disable channels.

---

### 🤖 Agents
**Location:** `/?section=agents`

**Org Chart View:**
- Visualize agent hierarchy
- See channels assigned to each agent
- View workspace paths
- Click workspace nodes to see file lists
- Jump directly to Docs for editing

**Agent Details:**
- Sessions active
- Token usage
- Last activity timestamp
- Model aliases configured

**Subagents Tab:**
- Spawn new subagents with task payloads
- List active subagents
- Kill subagents
- Run `/subagents` commands
- Direct agent-send dispatch

---

### ✅ Tasks
**Location:** `/?section=tasks`

Built-in Kanban board that syncs with your workspace. Manage to-dos, track progress across columns (To Do, In Progress, Done).

---

### 💾 Sessions
**Location:** `/?section=sessions`

View chat history and agent interactions:
- Session list with timestamps
- Message counts
- Token usage per session
- Click to view full conversation history

---

### ⏰ Cron Jobs
**Location:** `/?section=cron`

**View all scheduled tasks:**
- Job name, schedule (cron expression), timezone
- Next run time countdown
- Last run timestamp + duration
- Enable/disable toggle
- Run now button
- Edit job (schedule, payload, delivery)

**Create new jobs:**
- Schedule types: `at` (one-time), `every` (interval), `cron` (expression)
- Payload types: `systemEvent` (main session), `agentTurn` (isolated subagent)
- Delivery modes: `none`, `announce` (Telegram/chat), `webhook` (HTTP POST)

**Current Jobs (Jarvis's System):**
1. Daily Memory Review (2 AM) - Haiku subagent
2. Daily Betting Workflow (5 AM) - Main session script runner
3. Morning Betting Report (5:15 AM) - Haiku subagent → Telegram
4. Error Monitor (every 6h) - Haiku subagent → Telegram (only if issues)

---

### 🧠 Memory
**Location:** `/?section=memory`

Edit agent long-term memory files:
- `MEMORY.md` (main memory file)
- `memory/YYYY-MM-DD.md` (daily journals)
- Topic-specific memory files

Direct editing interface with save/discard buttons.

---

### 📚 Docs
**Location:** `/?section=docs`

Browse workspace documentation across all agents:
- Navigate folder structure
- Read markdown files
- View agent SOUL.md, USER.md, AGENTS.md, etc.
- Jump here from Agents Org Chart workspace nodes

---

### 🗂️ Vector DB
**Location:** `/?section=vectors`

Browse and search semantic memory (like Pinecone, but local):
- Powered by OpenClaw's vector database
- Semantic search with similarity scores
- View indexed documents
- Cmd+K global search integration

---

### 🎯 Skills
**Location:** `/?section=skills`

Manage installed agent skills:
- View system skills (`/opt/homebrew/lib/node_modules/openclaw/skills/`)
- Install new skills from clawhub.com
- Update existing skills
- View skill documentation (SKILL.md)

**ClawHub Tab:**
- Browse public skill registry
- One-click install from community
- Search skills by keyword

---

### 🤖 Models
**Location:** `/?section=models`

**Unified model runtime controls:**
- View configured models (primary + fallbacks)
- Model aliases (opus, haiku, etc.)
- Provider authentication status
- Token usage analytics
- Cost tracking per model

**Provider Auth:**
- Anthropic API keys
- OpenAI API keys
- Other provider credentials
- Env-backed model keys

---

### 🔑 Accounts & Keys
**Location:** `/?section=accounts`

**Integration credentials:**
- Channel tokens (Telegram bot token, Discord bot token, etc.)
- API keys for external services (OddsAPI, weather, etc.)
- Environment variable editing
- Vercel-style double-input secret editing
- Reveal/hide toggles
- Auto-discovered skill credentials

---

### 🎤 Audio & Voice
**Location:** `/?section=audio`

Configure TTS (text-to-speech) settings:
- Voice selection
- Speaker/device output
- ElevenLabs integration
- Volume, pitch, speed controls

---

### 🌐 Browser Relay
**Location:** `/?section=browser`

Inspect Chrome extension relay state:
- Connection status (attached/detached)
- Active tab info
- Profile selection (chrome vs openclaw)
- Debug connectivity issues
- Runtime health checks

---

### 🔗 Tailscale
**Location:** `/?section=tailscale`

Manage network exposure:
- View configured exposure mode
- Tunnel state (active/inactive)
- Toggle Tailscale on/off
- Run runtime actions without CLI
- Serve/exposure status

---

### 🔐 Permissions
**Location:** `/?section=permissions`

Control tool and resource access:
- File system permissions
- Network access
- Command execution security
- Tool allowlists/denylists

---

### 📊 Usage
**Location:** `/?section=usage`

Deep analytics:
- Model usage over time
- Token consumption by model
- Session breakdown
- Cost tracking ($ per model)
- Historical charts

---

### 💻 Terminal
**Location:** `/?section=terminal`

Built-in terminal:
- Run any command directly in dashboard
- No need to switch to external terminal
- Full shell access to workspace

---

### 📋 Logs
**Location:** `/?section=logs`

View system logs:
- Gateway logs
- Agent logs
- Cron job outputs
- Error logs
- Filter by level (info, warn, error)

---

### ⚙️ Config
**Location:** `/?section=config`

Edit `openclaw.json` configuration:
- Agents settings
- Model configuration
- Channel setup
- Tool permissions
- Gateway settings
- Direct JSON editing with validation

---

## Power-User Workflows

### Workspace Node Inspector
1. Go to Agents section (Org Chart view)
2. Click a workspace node
3. See file list modal
4. Click "Open in Docs" for detailed editing

### Subagent Command Center
1. Go to Agents → Subagents tab
2. Spawn with task payloads
3. Run direct commands
4. List only active sessions
5. Kill quickly from one panel

### Credential Control
1. Go to Accounts & Keys
2. Vercel-style double-input secret editing
3. Reveal/hide toggles
4. Auto-discovered integration credentials

### Tailscale Control Plane
1. Go to Tailscale section
2. View exposure mode + tunnel state
3. Toggle on/off without CLI
4. Run runtime actions directly

---

## Keyboard Shortcuts

- **Cmd+K** (Mac) / **Ctrl+K** (Windows/Linux) - Global search (semantic vector search)
- Navigation via sidebar always available

---

## Auto-Discovery

Mission Control automatically finds:
- **OpenClaw binary:** Checks `which openclaw`, then common paths
- **Home directory:** `~/.openclaw` (or `OPENCLAW_HOME` env var)
- **Agents:** Reads `openclaw.json` and scans agent directories
- **Workspaces:** Discovers all workspace directories from config

**Zero configuration needed.** Just start the server and it connects instantly.

---

## Installation

**Recommended location:** `~/.openclaw/openclaw-mission-control`

```bash
cd ~/.openclaw
git clone https://github.com/robsannaa/openclaw-mission-control.git
cd openclaw-mission-control
./setup.sh
```

**Manual dev mode:**
```bash
npm install
npm run dev
```

**Custom port:**
```bash
PORT=8080 ./setup.sh
# or
npm run dev -- --port 8080
```

---

## Environment Variables (Optional)

Everything auto-discovers, but you can override:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_HOME` | `~/.openclaw` | Path to OpenClaw home |
| `OPENCLAW_BIN` | Auto-detected | Path to openclaw binary |
| `OPENCLAW_WORKSPACE` | Auto-detected | Default workspace path |
| `OPENCLAW_SKILLS_DIR` | Auto-detected | System skills directory |

---

## Troubleshooting

### "OpenClaw not found"
```bash
openclaw --version  # Verify it's in PATH
OPENCLAW_BIN=$(which openclaw) npm run dev  # Manual override
```

### Port 3000 already in use
```bash
npm run dev -- --port 8080
```

### Runtime TypeError in Cron view
Fixed Feb 19, 2026 - all jobs now have `delivery` config.

---

## Integration with Jarvis's Betting System

Mission Control is actively used for:
- **Dashboard monitoring:** Real-time system health, CPU/memory/disk
- **Cron job management:** View/edit 4 automated betting jobs
- **Recent results:** Quick access to last cron run outputs
- **Error detection:** Click recent cron results to see warnings (e.g., NHL API 404)
- **Gateway log:** Watch live websocket activity
- **Config editing:** Modify `openclaw.json` without CLI

---

## Key Benefits

✅ **Visual workflow** - No more juggling CLI commands  
✅ **Real-time monitoring** - Live CPU/memory/disk/gateway stats  
✅ **100% local & private** - No cloud, no telemetry  
✅ **Intuitive UX** - Wizards, guided setup, smart defaults  
✅ **Direct editing** - Memory files, config, credentials  
✅ **Cron visualization** - See schedules, next runs, enable/disable  
✅ **Subagent control** - Spawn/kill/list from GUI  
✅ **Built-in terminal** - Run commands without switching apps

---

## Links

- **GitHub:** https://github.com/robsannaa/openclaw-mission-control
- **OpenClaw Docs:** https://docs.openclaw.ai
- **Local URL:** http://127.0.0.1:3000 (dev) or http://127.0.0.1:3333 (production)

---

*Last updated: Feb 19, 2026, 12:37 AM EST*
