#!/bin/bash
# Test connection to AvalancheGo node

set -e

HTTP_PORT="${HTTP_PORT:-9650}"
RPC_URL="http://localhost:${HTTP_PORT}/ext/bc/C/rpc"
HEALTH_URL="http://localhost:${HTTP_PORT}/ext/health"

echo "Testing AvalancheGo node connection..."
echo ""

# Check health endpoint
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Health check passed"
    curl -s "$HEALTH_URL" | head -5
else
    echo "❌ Health check failed - node might not be running"
    echo "   Start with: ./scripts/start.sh"
    exit 1
fi

echo ""
echo "Testing RPC endpoint..."

# Test basic RPC call
if command -v curl > /dev/null; then
    response=$(curl -s -X POST "$RPC_URL" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}')
    
    if echo "$response" | grep -q "result"; then
        echo "✅ RPC endpoint working"
        block_num=$(echo "$response" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
        echo "   Latest block: $block_num"
    else
        echo "⚠️  RPC endpoint responded but might have issues"
        echo "   Response: $response"
    fi
else
    echo "⚠️  curl not found, skipping RPC test"
fi

echo ""
echo "Connection test complete!"

