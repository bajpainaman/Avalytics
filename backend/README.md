# Avalytics Backend - AvalancheGo Node

This directory contains the backend infrastructure for running an AvalancheGo archive node for the Avalytics platform.

## Overview

The backend provides:
- Local AvalancheGo node setup and management
- Archive node configuration for complete chain history
- Integration with the Avalytics indexer and ETL pipeline
- Health monitoring and status checks

## Structure

```
backend/
├── scripts/          # Setup and management scripts
│   ├── install.sh   # Download and install AvalancheGo binary
│   ├── start.sh     # Start the node
│   ├── stop.sh      # Stop the node
│   └── status.sh    # Check node health and status
├── config/          # Node configuration files
│   ├── config.json  # Main node configuration
│   └── chains/      # Chain-specific configurations
│       └── C.json   # C-Chain (EVM) configuration
└── data/            # Node data directory (gitignored)
    └── db/          # Blockchain database
```

## Requirements

- Linux/macOS
- 1TB+ disk space for archive node (grows over time)
- 32GB+ RAM recommended for archive mode
- Network connectivity for syncing

## Quick Start

```bash
# 1. Install AvalancheGo binary
cd backend
./scripts/install.sh

# 2. Start the node (runs in foreground)
./scripts/start.sh

# In another terminal, check status
./scripts/status.sh

# Stop the node
./scripts/stop.sh
```

## Configuration

### Main Configuration (`config/config.json`)

- `network-id`: 1 (Mainnet)
- `http-port`: 9650 (RPC endpoint)
- `staking-port`: 9651 (P2P networking)
- `pruning-enabled`: false (archive mode)
- `state-sync-enabled`: false (full sync)

### C-Chain Configuration (`config/chains/C.json`)

- Archive mode enabled (no pruning)
- Full transaction history
- Debug and trace APIs enabled
- Unfinalized queries allowed

## Integration with Avalytics

The node exposes RPC endpoints that the Avalytics indexer uses:

- **HTTP RPC**: `http://localhost:9650/ext/bc/C/rpc`
- **Index API**: `http://localhost:9650/ext/index/C/block`
- **Health Check**: `http://localhost:9650/ext/health`

The indexer (`go/indexer/main.go`) connects to these endpoints to:
1. Fetch historical blocks and transactions
2. Monitor new blocks in real-time
3. Extract transaction data for analytics

## Monitoring

Check node health:
```bash
curl http://localhost:9650/ext/health
```

View node logs:
The node logs to stdout when started with `start.sh`. For production, consider redirecting to a log file or using a process manager.

## Troubleshooting

**Node won't start:**
- Check disk space: `df -h`
- Check if port 9650 is already in use: `lsof -i :9650`
- Verify binary exists: `ls -la bin/avalanchego`

**Node not syncing:**
- Check network connectivity
- Verify firewall allows port 9651 (staking port)
- Check logs for errors

**Out of disk space:**
- Archive node requires significant storage
- Consider using pruning for non-archive nodes (not recommended for Avalytics)

## Performance Notes

- Initial sync can take 24-48 hours
- Archive mode requires ~1TB+ disk space
- RAM usage scales with chain state size
- Network bandwidth: ~10-50 Mbps during sync

