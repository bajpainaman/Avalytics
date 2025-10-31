#!/bin/bash
# Check AvalancheGo node status

set -e

HTTP_PORT="${HTTP_PORT:-9650}"
HEALTH_URL="http://localhost:${HTTP_PORT}/ext/health"

echo "Checking AvalancheGo node status..."
echo ""

# Check if node is running
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Node is running and healthy"
    echo ""
    
    # Get health status
    echo "Health check response:"
    curl -s "$HEALTH_URL" | jq '.' 2>/dev/null || curl -s "$HEALTH_URL"
    echo ""
    
    # Check if process is running
    if pgrep -f "avalanchego" > /dev/null; then
        echo "Process status: Running"
        ps aux | grep -E "avalanchego" | grep -v grep | head -1
    fi
else
    echo "❌ Node is not responding"
    echo "   URL: $HEALTH_URL"
    echo ""
    
    if pgrep -f "avalanchego" > /dev/null; then
        echo "⚠️  Process is running but not responding to health checks"
        ps aux | grep -E "avalanchego" | grep -v grep
    else
        echo "⚠️  No AvalancheGo process found"
        echo "   Start the node with: ./scripts/start.sh"
    fi
fi

