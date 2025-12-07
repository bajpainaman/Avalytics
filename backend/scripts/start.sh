#!/bin/bash
# Start AvalancheGo node for Avalytics

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="${BIN_DIR:-$BACKEND_DIR/bin}"
DATA_DIR="${DATA_DIR:-$BACKEND_DIR/data}"
CONFIG_DIR="${CONFIG_DIR:-$BACKEND_DIR/config}"

# Check if binary exists
if [ ! -f "$BIN_DIR/avalanchego" ]; then
    echo "AvalancheGo binary not found. Running install script..."
    "$SCRIPT_DIR/install.sh"
fi

# Create data directory
mkdir -p "$DATA_DIR/db"

echo "Starting AvalancheGo node..."
echo "  Binary: $BIN_DIR/avalanchego"
echo "  Data: $DATA_DIR"
echo "  Config: $CONFIG_DIR"
echo ""

cd "$BACKEND_DIR"

# Start node with configuration
exec "$BIN_DIR/avalanchego" \
    --network-id=1 \
    --http-host=0.0.0.0 \
    --http-port=9650 \
    --staking-port=9651 \
    --db-dir="$DATA_DIR/db" \
    --log-level=info \
    --pruning-enabled=false \
    --state-sync-enabled=false \
    --chain-config-dir="$CONFIG_DIR/chains"


