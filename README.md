# Avalytics

Professional blockchain intelligence platform for Avalanche. A Palantir/Gotham-style analytics system for on-chain data.

## Features

- **Blockchain Indexing**: Real-time and historical data extraction from Avalanche C-Chain
- **Wallet Profiling**: AI-powered behavioral analysis and classification
- **Cohort Detection**: ML-based wallet segmentation
- **Professional CLI**: Foundry-style interface with extensive customization
- **CRM Integration**: Manage and track wallet contacts
- **Structured AI**: Pydantic-based models for wallet intelligence
- **Pattern Detection**: Identify trading patterns, arbitrage, wash trading

## Installation

\`\`\`bash
git clone https://github.com/bajpainaman/Avalytics.git
cd Avalytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python db/init.py
\`\`\`

## Quick Start

\`\`\`bash
source venv/bin/activate

# View statistics
python cli/avalytics.py stats

# List top wallets
python cli/avalytics.py wallets --limit 10 --sort volume

# Deep wallet analysis
python cli/avalytics.py inspect 0x... --ai --patterns

# CRM
python cli/avalytics.py crm add 0x... --name "Whale Alpha" --tags "high-value"
\`\`\`

## CLI Commands

- \`wallets\` - List top wallets
- \`inspect <address>\` - Deep wallet analysis
- \`cohorts\` - View wallet segments
- \`stats\` - Platform statistics
- \`crm\` - Wallet contact management
- \`config\` - Configuration management

## License

MIT
