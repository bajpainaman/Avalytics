# Avalytics

> **The Palantir for Crypto** - Professional blockchain intelligence platform for Avalanche

Transform raw blockchain data into actionable intelligence. Avalytics is a comprehensive CLI-first analytics platform that combines on-chain data extraction, AI-powered profiling, and CRM integration to help you identify, analyze, and engage with high-value wallet holders.

[![Blockchain Analytics Dashboard](https://raw.githubusercontent.com/bajpainaman/Avalytics/main/dash.png)](https://view.monday.com/embed/18159692247-c0ef45d2f94a1157e7768d03a0dc2929?r=use1)

---

## What is Avalytics?

Avalytics is a production-ready blockchain intelligence platform designed for:
- **Crypto VCs & Funds**: Identify whale wallets and track smart money movements
- **DeFi Protocols**: Discover power users and growth opportunities
- **Security Teams**: Detect suspicious activity and risk patterns
- **Business Development**: Build targeted outreach lists with AI-powered insights

Think Gotham (Palantir's crypto tool) meets Foundry (Ethereum dev toolkit) - a professional CLI that processes millions of transactions to surface the wallets that matter.

---

## Core Features

### 🔗 **Blockchain Indexing**
- Extract blocks and transactions from Avalanche C-Chain
- Parallel processing with configurable workers
- SQLite storage optimized for large wei values
- Support for multi-subnet architecture (coming soon)

### 🧠 **AI-Powered Intelligence**
- **Local AI**: Ollama integration (llama3.1:8b) for on-premise analysis
- **Structured Outputs**: Pydantic models ensure consistent, parseable insights
- **Web Research**: Grok and Perplexity APIs for real-time entity identification
- **Pattern Detection**: Identify accumulation, distribution, wash trading, arbitrage

### 👤 **Wallet Profiling**
Automatically classify wallets into behavioral segments:
- **Whales**: Wallets with >100 AVAX volume
- **Bots**: High-frequency traders (>50 tx/day)
- **DEX Users**: Active DeFi participants (>10 unique contracts)
- **Risk Scoring**: HIGH/MEDIUM/LOW based on activity patterns

### 📊 **ML-Based Cohort Detection**
- K-means clustering segments wallets by behavior
- Automatic cohort tagging for targeted analysis
- Export cohorts to CRM for campaigns

### 💼 **Monday.com CRM Integration**
Sync wallet intelligence directly to Monday.com boards:
- Auto-created columns: Address, Volume, TX Count, Type, Risk, Last Active
- AI analysis field with full research reports
- Web research integration (entity ID, scam checks)
- Batch sync with rate limiting

### 🛠️ **Professional CLI**
Foundry-style command structure:
```bash
avalytics wallets --limit 10 --sort volume --format json
avalytics inspect <address> --ai --patterns
avalytics cohorts
avalytics monday sync <board> --with-research
avalytics crm add <address> --name "Whale Alpha" --tags "high-value"
```

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AVALYTICS PLATFORM                        │
└─────────────────────────────────────────────────────────────────┘

   Data Sources              Processing              Intelligence
   ────────────              ──────────              ────────────

┌──────────────┐         ┌──────────────┐        ┌──────────────┐
│  Avalanche   │────────▶│   Indexer    │───────▶│   SQLite     │
│   C-Chain    │         │ (Web3.py)    │        │   Database   │
└──────────────┘         └──────────────┘        └──────────────┘
                                                         │
                                                         ▼
                         ┌──────────────┐        ┌──────────────┐
                         │   Wallet     │───────▶│   Cohort     │
                         │  Profiler    │        │  Detector    │
                         └──────────────┘        └──────────────┘
                                                         │
                                                         ▼
┌──────────────┐         ┌──────────────┐        ┌──────────────┐
│    Ollama    │────────▶│      AI      │───────▶│  Structured  │
│ (llama3.1)   │         │   Analysis   │        │   Insights   │
└──────────────┘         └──────────────┘        └──────────────┘
                                                         │
┌──────────────┐         ┌──────────────┐               │
│    Grok /    │────────▶│     Web      │───────────────┤
│ Perplexity   │         │   Research   │               │
└──────────────┘         └──────────────┘               ▼

                         ┌──────────────┐        ┌──────────────┐
                         │     CLI      │───────▶│  Monday.com  │
                         │   Terminal   │        │     CRM      │
                         └──────────────┘        └──────────────┘
```

### Data Flow

1. **Extraction**: Blocks pulled from Avalanche RPC in parallel batches
2. **Storage**: Transactions stored in SQLite with optimized schema
3. **Profiling**: Wallet behaviors analyzed (volume, frequency, contracts)
4. **Clustering**: ML algorithms segment wallets into cohorts
5. **AI Analysis**: Ollama generates behavioral insights and recommendations
6. **Web Research**: Grok/Perplexity search for entity information and risks
7. **Export**: Enriched data synced to Monday.com or exported as JSON/CSV

---

## Installation

### Prerequisites
- Python 3.10+
- Avalanche RPC endpoint (default: public API)
- Optional: Ollama server, Grok API, Perplexity API, Monday.com account

### Quick Start

```bash
# Clone repository
git clone https://github.com/bajpainaman/Avalytics.git
cd Avalytics

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python db/init.py

# Configure environment (copy and edit)
cp .env.example .env
# Edit .env with your API keys

# Index your first blocks
python indexer/extract_blocks.py 100

# Build wallet profiles
python analytics/wallet_profiler.py

# Detect cohorts
python analytics/cohort_detector.py
```

---

## CLI Reference

### Overview Commands

#### `stats`
Display platform statistics
```bash
python cli/avalytics.py stats
```
Output:
```
Avalytics Platform Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Wallets Tracked       1,094
Total Transactions    3,587
Blocks Indexed          146
Total Volume    22,696.53 AVAX
Whale Wallets       31 (2.8%)
Bot Wallets                 1
DEX Users                   1
```

#### `wallets`
List top wallets with filtering
```bash
# Top 10 by volume
python cli/avalytics.py wallets --limit 10 --sort volume

# Top 20 by transaction count as JSON
python cli/avalytics.py wallets --limit 20 --sort txs --format json

# Export to CSV
python cli/avalytics.py wallets --limit 100 --format csv > wallets.csv
```

Options:
- `--limit, -n`: Number of results (default: 10)
- `--sort, -s`: Sort by `volume`, `txs`, or `contracts`
- `--format, -f`: Output format `table`, `json`, or `csv`

### Deep Analysis

#### `inspect`
Deep dive into specific wallet
```bash
# Basic inspection
python cli/avalytics.py inspect 0x7a4bfF8A27b6CEAb894b3A0a04D28e198e1b66f7

# With AI analysis
python cli/avalytics.py inspect 0x7a4bfF8A27b6CEAb894b3A0a04D28e198e1b66f7 --ai

# With transaction pattern detection
python cli/avalytics.py inspect 0x7a4bfF8A27b6CEAb894b3A0a04D28e198e1b66f7 --ai --patterns
```

Output includes:
- Transaction count and volume
- Contract interactions
- Wallet classification (WHALE/BOT/DEX/RETAIL)
- AI behavioral analysis
- Transaction patterns (accumulation, distribution, etc)
- Recommended engagement approach

#### `cohorts`
View wallet segments
```bash
# Table view
python cli/avalytics.py cohorts

# JSON export
python cli/avalytics.py cohorts --format json
```

### CRM Integration

#### `crm add`
Add wallet to local CRM
```bash
python cli/avalytics.py crm add 0x... \
  --name "Whale Alpha" \
  --tags "high-value,active,whale" \
  --notes "Identified via large AVAX transfers"
```

#### `crm list`
List CRM contacts
```bash
# All contacts
python cli/avalytics.py crm list

# Filter by tag
python cli/avalytics.py crm list --tag high-value
```

### Monday.com Integration

#### `monday create`
Create new Monday.com board
```bash
python cli/avalytics.py monday create --name "Avalanche Whales Q1"
```

Creates board with columns:
- Wallet Address (text)
- Total Volume (AVAX) (number)
- Transaction Count (number)
- Wallet Type (status: WHALE/BOT/DEX/RETAIL)
- Risk Level (status: HIGH/MEDIUM/LOW)
- Last Active (date)
- AI Analysis (long text)
- Contact Status (status: NEW/CONTACTED/QUALIFIED/CLOSED)

#### `monday sync`
Sync wallets to Monday.com board
```bash
# Sync top 50 whales
python cli/avalytics.py monday sync <board_id> --limit 50 --whale-only

# Sync with AI analysis (slower)
python cli/avalytics.py monday sync <board_id> --limit 20 --with-ai

# Sync with web research (Grok/Perplexity)
python cli/avalytics.py monday sync <board_id> --limit 10 --with-research

# Custom filters
python cli/avalytics.py monday sync <board_id> \
  --limit 100 \
  --min-volume 100 \
  --whale-only
```

Options:
- `--limit, -n`: Number of wallets to sync
- `--whale-only`: Only sync whale wallets (>100 AVAX)
- `--min-volume`: Minimum volume threshold in AVAX
- `--with-ai`: Include Ollama AI analysis
- `--with-research`: Include Grok/Perplexity web research

#### `monday list`
View all Monday.com boards
```bash
python cli/avalytics.py monday list
```

### Configuration

#### `config get`
View configuration
```bash
# All settings
python cli/avalytics.py config get

# Specific setting
python cli/avalytics.py config get db_path
```

#### `config set`
Update configuration
```bash
python cli/avalytics.py config set db_path /custom/path/db.sqlite
python cli/avalytics.py config set ollama_url http://localhost:11434
python cli/avalytics.py config set output_format json
```

---

## Configuration

Configuration is stored in `~/.avalytics/config.json` and `.env` file.

### Environment Variables

Create `.env` file:
```bash
# Avalanche RPC
RPC_URL=https://api.avax.network/ext/bc/C/rpc

# Database
DB_PATH=./data/avalytics.db

# Indexer settings
START_BLOCK=0
BATCH_SIZE=100
MAX_WORKERS=4

# Ollama AI
OLLAMA_URL=http://10.246.250.44:11434
OLLAMA_MODEL=llama3.1:8b

# Monday.com CRM
MONDAY_API_TOKEN=your_token_here
MONDAY_CLIENT_ID=your_client_id
MONDAY_CLIENT_SECRET=your_client_secret

# AI Research APIs (optional)
GROK_API_KEY=your_grok_key
PERPLEXITY_API_KEY=your_perplexity_key
```

### Config File

Located at `~/.avalytics/config.json`:
```json
{
  "db_path": "./data/avalytics.db",
  "rpc_url": "https://api.avax.network/ext/bc/C/rpc",
  "ollama_url": "http://10.246.250.44:11434",
  "output_format": "table",
  "color_scheme": "default",
  "verbose": false
}
```

---

## AI Integration

### Ollama (Local AI)

Run Ollama locally for privacy and cost savings:
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.1:8b

# Start server
ollama serve
```

Configure in `.env`:
```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

Ollama provides:
- Wallet behavior profiling
- Sophistication scoring (1-10)
- Transaction pattern detection
- Engagement recommendations

### Grok API (Web-Connected AI)

Get API key from https://x.ai

Grok provides:
- Web search for wallet information
- Entity identification (exchanges, projects)
- Threat assessment
- Similar wallet discovery
- Outreach strategy generation

### Perplexity API (Real-Time Search)

Get API key from https://perplexity.ai

Perplexity provides:
- Real-time web research
- Scam/fraud checking
- Entity verification with sources
- Risk assessment with citations

---

## Database Schema

### `transactions`
Raw blockchain transaction data
```sql
CREATE TABLE transactions (
    tx_hash TEXT PRIMARY KEY,
    block_number INTEGER NOT NULL,
    from_address TEXT NOT NULL,
    to_address TEXT,
    value TEXT,              -- Large integers stored as TEXT
    gas_price TEXT,
    gas_used INTEGER,
    status INTEGER,
    timestamp DATETIME,
    input_data TEXT
);
```

### `wallet_profiles`
Behavioral wallet profiles
```sql
CREATE TABLE wallet_profiles (
    wallet_address TEXT PRIMARY KEY,
    first_seen DATETIME,
    last_active DATETIME,
    total_txs INTEGER DEFAULT 0,
    total_volume_wei TEXT DEFAULT '0',
    unique_contracts INTEGER DEFAULT 0,
    is_whale INTEGER DEFAULT 0,
    is_bot INTEGER DEFAULT 0,
    is_dex_user INTEGER DEFAULT 0,
    avg_tx_value_wei TEXT,
    behavior_score REAL,
    last_updated DATETIME
);
```

### `wallet_tags`
Cohort and custom tags
```sql
CREATE TABLE wallet_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address TEXT NOT NULL,
    tag TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at DATETIME,
    UNIQUE(wallet_address, tag)
);
```

### `crm_contacts`
CRM contact management
```sql
CREATE TABLE crm_contacts (
    wallet_address TEXT PRIMARY KEY,
    contact_name TEXT,
    tags TEXT,
    notes TEXT,
    added_at DATETIME,
    last_contact DATETIME
);
```

---

## Use Cases

### Crypto VC: Identify Smart Money
```bash
# Find whale wallets
python cli/avalytics.py wallets --limit 50 --sort volume --format json > whales.json

# Deep analysis on top whale
python cli/avalytics.py inspect 0x... --ai --patterns

# Sync to Monday.com for team collaboration
python cli/avalytics.py monday sync <board> --limit 50 --whale-only --with-research
```

### DeFi Protocol: Find Power Users
```bash
# Find DEX users
python cli/avalytics.py wallets --sort contracts

# Segment into cohorts
python analytics/cohort_detector.py

# Export cohort for outreach
python cli/avalytics.py cohorts --format json
```

### Security Team: Risk Monitoring
```bash
# Profile suspicious wallet
python cli/avalytics.py inspect 0x... --ai --patterns

# Check for scam indicators
python integrations/perplexity_client.py 0x...

# Monitor bot activity
python cli/avalytics.py wallets --sort txs | grep BOT
```

---

## Advanced Usage

### Custom Indexing Scripts

```python
from indexer.extract_blocks import BlockExtractor

extractor = BlockExtractor(
    rpc_url="https://api.avax.network/ext/bc/C/rpc",
    db_path="./custom.db"
)

# Index specific range
extractor.extract_range(start_block=1000000, end_block=1001000)

# Index latest 1000 blocks
extractor.extract_latest(num_blocks=1000)
```

### Programmatic Analysis

```python
from ai.structured_analyzer import StructuredAnalyzer

analyzer = StructuredAnalyzer()

# Get structured wallet profile
profile = analyzer.analyze_wallet_structured("0x...")

print(f"Type: {profile.wallet_type}")
print(f"Risk: {profile.risk_level}")
print(f"Sophistication: {profile.sophistication_score}/10")
print(f"Insights: {profile.key_insights}")
```

### Web Research

```python
from integrations.perplexity_client import PerplexityClient

client = PerplexityClient()

# Research wallet
result = client.research_wallet_entity("0x...")
print(result["entity_info"])
print(f"Sources: {result['sources']}")

# Check for scams
scam_check = client.check_scam_indicators("0x...")
print(f"Risk Level: {scam_check['risk_level']}")
```

---

## Performance

- **Indexing**: ~100 blocks/minute with 4 workers
- **Profiling**: ~1000 wallets/minute
- **Cohort Detection**: ~10,000 wallets in <30 seconds
- **AI Analysis**: ~5-10 seconds per wallet (local Ollama)
- **Web Research**: ~3-5 seconds per wallet (Perplexity)

### Optimization Tips
- Use `--whale-only` to reduce dataset size
- Run Ollama locally for faster AI analysis
- Batch Monday.com syncs to avoid rate limits
- Index incrementally (latest blocks) for real-time monitoring

---

## Troubleshooting

### Rate Limits
Monday.com API has rate limits. The platform automatically:
- Adds 0.5s delay between requests
- Retries on 429 errors with exponential backoff

### Large Integers
Avalanche uses wei (10^18), which exceeds SQLite INTEGER. Solution:
- Values stored as TEXT
- Converted to int() for calculations
- Displayed as AVAX (value / 10^18)

### AI Analysis Timeout
Web research can be slow. Solutions:
- Use `--with-ai` sparingly (top 20 wallets)
- Run research separately with dedicated scripts
- Increase timeout in client configs

---

## Roadmap

### Phase 1 (Complete ✅)
- [x] Blockchain indexing
- [x] Wallet profiling
- [x] ML cohort detection
- [x] Professional CLI
- [x] Monday.com CRM
- [x] AI analysis (Ollama)
- [x] Web research (Grok/Perplexity)

### Phase 2 (In Progress 🚧)
- [ ] Real-time websocket streaming
- [ ] Graph database (Neo4j) for relationships
- [ ] Web dashboard (Next.js)
- [ ] Multi-subnet support
- [ ] DeFi protocol-specific analytics

### Phase 3 (Planned 📋)
- [ ] ENS/Lens profile integration
- [ ] API server with authentication
- [ ] Webhook notifications
- [ ] Telegram/Discord bots
- [ ] Cross-chain wallet tracking
- [ ] MEV and sandwich attack detection

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details

---

## Support

- **Issues**: https://github.com/bajpainaman/Avalytics/issues
- **Discussions**: https://github.com/bajpainaman/Avalytics/discussions
- **Twitter**: [@yourhandle](https://twitter.com/yourhandle)

---

## Acknowledgments

Built with:
- [web3.py](https://github.com/ethereum/web3.py) - Ethereum/Avalanche interaction
- [Ollama](https://ollama.ai) - Local AI inference
- [Perplexity](https://perplexity.ai) - Web-connected AI
- [Monday.com](https://monday.com) - CRM platform
- [Rich](https://github.com/Textualize/rich) - Terminal UI
- [Click](https://click.palletsprojects.com/) - CLI framework

---

**Made with ❤️ for the Avalanche ecosystem**
