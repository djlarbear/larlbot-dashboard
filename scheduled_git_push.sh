#!/bin/bash
# Scheduled Git Push - Only pushes at specific times (every 4 hours)
# Runs at: 7:00 AM, 11:00 AM, 3:00 PM, 7:00 PM, 11:00 PM EST

WORKSPACE="${WORKSPACE:-$(pwd)}"
cd "$WORKSPACE"

# Get current hour and minute
CURRENT_HOUR=$(date +"%H")
CURRENT_MIN=$(date +"%M")
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S EST")

# Define allowed push hours (in 24-hour format)
ALLOWED_HOURS=(07 11 15 19 23)

# Check if current hour is in allowed list
IS_ALLOWED=false
for hour in "${ALLOWED_HOURS[@]}"; do
    if [ "$CURRENT_HOUR" = "$hour" ]; then
        IS_ALLOWED=true
        break
    fi
done

echo "======================================================================"
echo "🕐 Scheduled Git Push Check"
echo "======================================================================"
echo "⏰ Current Time: $TIMESTAMP (Hour: $CURRENT_HOUR)"

if [ "$IS_ALLOWED" = false ]; then
    echo "⏭️  Not a scheduled push time - skipping"
    echo "📅 Scheduled push times: 7:00 AM, 11:00 AM, 3:00 PM, 7:00 PM, 11:00 PM"
    echo "======================================================================"
    exit 0
fi

echo "✅ Scheduled push time - proceeding with Git push"
echo ""

# Run the actual production sync
exec /bin/bash "$WORKSPACE/production_sync.sh"
