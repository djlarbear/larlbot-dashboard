################################################################################
# LarlBot Dashboard - Flask Only
# EXPLICIT: This deploys Flask and NOTHING ELSE
# NO Streamlit, NO compatibility issues, ZERO confusion
################################################################################

# Start with official Python image - NO extra packages
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy ONLY requirements.txt (nothing else at this point)
COPY requirements.txt /app/requirements.txt

# Install dependencies from requirements.txt
# This is the ONLY place packages come from
RUN pip install --no-cache-dir -r requirements.txt

# Verify Python can find Flask (not Streamlit)
RUN python3 << 'EOF'
import sys
try:
    import flask
    print(f"✓ Flask {flask.__version__} installed")
except ImportError:
    print("✗ ERROR: Flask not installed!")
    sys.exit(1)

try:
    import streamlit
    print("✗ ERROR: Streamlit was installed (should not be!)")
    sys.exit(1)
except ImportError:
    print("✓ Streamlit NOT installed (correct)")
EOF

# Copy Flask application
COPY dashboard_server_cache_fixed.py /app/

# Copy startup script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy web assets
COPY templates/ /app/templates/
COPY static/ /app/static/

# Copy data files (bet tracking, rankings, etc.)
# These provide initial data for the dashboard
COPY ranked_bets.json /app/ranked_bets.json
COPY active_bets.json /app/active_bets.json
COPY completed_bets_2026-02-*.json /app/

# Create data directory for runtime files and logs
RUN mkdir -p /app/cache /app/memory

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Force fresh build - update this timestamp to force rebuild
# Timestamp: 2026-02-15 19:47 EST
LABEL build.time="2026-02-15T19:47:00-05:00"
LABEL build.app="larlbot-dashboard-flask-only"
LABEL build.note="NO Streamlit - Flask only"

# Use explicit entrypoint script
# This is the ONLY way the container starts
ENTRYPOINT ["/app/entrypoint.sh"]
