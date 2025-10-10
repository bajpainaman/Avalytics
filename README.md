# Avalytics 🚀

**Crypto Palantir for Avalanche** - Open-source blockchain intelligence platform with AI-powered analytics

Built for whale tracking, wallet profiling, and behavioral analysis on Avalanche C-Chain.

## 🎯 Features

- **Blockchain Indexer** - Pull blocks, transactions, and event logs from Avalanche
- **Wallet Profiling** - Automatic wallet classification (whales, bots, DEX users, NFT collectors)
- **ML-Powered Cohorts** - K-means clustering for wallet segmentation
- **AI Query Interface** - Natural language → SQL with Ollama (8x H100s ready!)
- **Terminal UI** - Rich CLI for exploring data
- **Real-time Analytics** - Behavior scoring and pattern detection

## 🏗️ Architecture

```
Avalanche RPC → Indexer → SQLite → Analytics Engine → Ollama AI → Terminal
```

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/bajpainaman/Avalytics.git
cd Avalytics

# Run everything (one command)
./run.sh

# Or manual steps:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python3 db/init.py

# Index latest 100 blocks
python3 indexer/extract_blocks.py 100

# Build wallet profiles
python3 analytics/wallet_profiler.py

# Detect cohorts
python3 analytics/cohort_detector.py

# Launch terminal
python3 cli/terminal.py
```

## 🤖 AI Features

Configure Ollama in `.env`:
```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

Terminal commands:
- `stats` - Show overall statistics
- `whales` - Show top whale wallets
- `wallet <address>` - AI-powered wallet analysis
- `query <natural language>` - Ask questions in plain English
  - Example: "Show me wallets that traded over 10 ETH"
  - Example: "Find all DEX users active in the last week"

## 📊 Database Schema

- `transactions` - All on-chain transactions
- `wallet_profiles` - Profiled wallets with behavior flags
- `wallet_tags` - ML-generated cohort tags
- `event_logs` - Contract event logs
- `contracts` - Contract metadata

## 🎨 Example Queries

```python
# Terminal natural language queries
> query show me the top 10 wallets by transaction count
> query find all whales active in the last 24 hours
> query which wallets interact with the most unique contracts
```

## 🛠️ Tech Stack

- **Indexer**: web3.py
- **Database**: SQLite (upgrade to Postgres/ClickHouse for scale)
- **Analytics**: pandas + scikit-learn
- **AI**: Ollama (local LLM with 8x H100s)
- **UI**: Rich (Python terminal UI)

## 📈 Roadmap

- [ ] Real-time streaming (websockets)
- [ ] Graph database integration (Neo4j)
- [ ] Web dashboard (Next.js)
- [ ] Multi-subnet support
- [ ] Defi protocol-specific analytics
- [ ] Wallet contact discovery (ENS, Lens)

## 🤝 Contributing

Built for the Avalanche ecosystem. Contributions welcome!

## 📄 License

MIT License

---

**Built with 🔥 for the crypto intelligence community**
