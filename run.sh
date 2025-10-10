#!/bin/bash
# Avalytics Quick Start

echo "🚀 Avalytics - Crypto Palantir for Avalanche"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Copy .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file (edit if needed)"
fi

# Initialize database
echo "Initializing database..."
python3 db/init.py

echo ""
echo "Choose an option:"
echo "1. Index latest 100 blocks"
echo "2. Build wallet profiles"
echo "3. Detect cohorts"
echo "4. Launch terminal"
echo "5. Full pipeline (all of the above)"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "Indexing blocks..."
        python3 indexer/extract_blocks.py 100
        ;;
    2)
        echo "Building profiles..."
        python3 analytics/wallet_profiler.py
        ;;
    3)
        echo "Detecting cohorts..."
        python3 analytics/cohort_detector.py
        ;;
    4)
        echo "Launching terminal..."
        python3 cli/terminal.py
        ;;
    5)
        echo "Running full pipeline..."
        python3 indexer/extract_blocks.py 100
        python3 analytics/wallet_profiler.py
        python3 analytics/cohort_detector.py
        python3 cli/terminal.py
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
