#!/bin/bash
# Run learning engine to update insights
cd /Users/macmini/.openclaw/workspace
python3 learning_engine.py >> learning_engine.log 2>&1
