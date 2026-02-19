#!/bin/bash
################################################################################
# EXPLICIT FLASK ENTRYPOINT - NO STREAMLIT EVER
################################################################################

set -e  # Exit on any error
set -u  # Exit on undefined variables

echo "╔════════════════════════════════════════════════════════╗"
echo "║           LarlBot Flask Dashboard Entrypoint            ║"
echo "║              NO Streamlit - Flask Only                  ║"
echo "╚════════════════════════════════════════════════════════╝"

# Verify Streamlit is NOT installed
echo "Checking that Streamlit is NOT installed..."
if python3 -c "import streamlit" 2>/dev/null; then
    echo "✗ CRITICAL ERROR: Streamlit found in environment!"
    echo "  This should NEVER happen. Aborting."
    exit 1
fi
echo "✓ Confirmed: Streamlit NOT installed"

# Verify Flask IS installed
echo "Checking that Flask IS installed..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "✗ CRITICAL ERROR: Flask not found!"
    exit 1
fi
echo "✓ Confirmed: Flask is installed"

# Get configuration
PORT=${PORT:-5001}
WORKSPACE=${WORKSPACE:-/app}

echo ""
echo "Configuration:"
echo "  Application: LarlBot Dashboard"
echo "  Framework: Flask"
echo "  Port: $PORT"
echo "  Workspace: $WORKSPACE"
echo "  Python: $(python3 --version)"
echo ""

# Final confirmation
echo "Starting Flask application..."
echo "  Command: python3 -u $WORKSPACE/dashboard_server_cache_fixed.py"
echo ""

# START FLASK
# The -u flag ensures unbuffered output
# exec replaces this shell process with Python
exec python3 -u "$WORKSPACE/dashboard_server_cache_fixed.py"

# If we get here, something went wrong
echo "✗ FATAL: Entrypoint script exited unexpectedly"
exit 1
