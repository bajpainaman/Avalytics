#!/bin/bash
# Stop AvalancheGo node

set -e

echo "Stopping AvalancheGo node..."

# Find and kill avalanchego process
if pgrep -f "avalanchego" > /dev/null; then
    pkill -f "avalanchego"
    echo "✅ Node stopped"
    
    # Wait a bit and check
    sleep 2
    if pgrep -f "avalanchego" > /dev/null; then
        echo "⚠️  Process still running, force killing..."
        pkill -9 -f "avalanchego"
    fi
else
    echo "ℹ️  No running AvalancheGo process found"
fi


