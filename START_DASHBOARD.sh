#!/bin/bash
# Start LarlBot Dashboard on port 5001 (port 5000 conflicts with AirPlay)
cd /Users/macmini/.openclaw/workspace
PORT=5001 python3 dashboard_server.py
