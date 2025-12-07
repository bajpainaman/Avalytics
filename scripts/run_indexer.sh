#!/bin/bash
# Avalytics Reliable Indexer Runner

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   Avalytics Reliable Indexer        ${NC}"
echo -e "${GREEN}======================================${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Create data directory
mkdir -p data

# Check command
COMMAND=${1:-"help"}

case $COMMAND in
    latest)
        BLOCKS=${2:-1000}
        echo -e "\n${YELLOW}Indexing latest $BLOCKS blocks...${NC}\n"
        python3 -m indexer.reliable_indexer latest -n "$BLOCKS"
        ;;
        
    range)
        START=$2
        END=$3
        if [ -z "$START" ] || [ -z "$END" ]; then
            echo "Usage: $0 range <start_block> <end_block>"
            exit 1
        fi
        echo -e "\n${YELLOW}Indexing blocks $START to $END...${NC}\n"
        python3 -m indexer.reliable_indexer range -s "$START" -e "$END"
        ;;
        
    resume)
        echo -e "\n${YELLOW}Resuming from last checkpoint...${NC}\n"
        python3 -m indexer.reliable_indexer resume
        ;;
        
    sync)
        INTERVAL=${2:-12}
        echo -e "\n${YELLOW}Starting continuous sync (interval: ${INTERVAL}s)...${NC}\n"
        python3 -m indexer.reliable_indexer sync -i "$INTERVAL"
        ;;
        
    stats)
        python3 -m indexer.reliable_indexer stats
        ;;
        
    help|*)
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  latest [n]          - Index latest N blocks (default: 1000)"
        echo "  range <start> <end> - Index specific block range"
        echo "  resume              - Resume from last checkpoint"
        echo "  sync [interval]     - Continuous sync (default: 12s)"
        echo "  stats               - Show indexer statistics"
        echo ""
        echo "Examples:"
        echo "  $0 latest 5000      # Index last 5000 blocks"
        echo "  $0 range 40000000 40100000  # Index specific range"
        echo "  $0 resume           # Resume from checkpoint"
        echo "  $0 sync 30          # Sync every 30 seconds"
        echo ""
        ;;
esac
