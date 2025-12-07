#!/usr/bin/env python3
"""
Reliable Avalanche Wallet Indexer

Features:
- Checkpointing (resume from where you left off)
- Batch RPC calls (much faster)
- Rate limit handling with exponential backoff
- Multiple RPC provider fallback
- Progress tracking
- Wallet extraction from both from/to addresses
"""
import os
import sys
import json
import sqlite3
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

load_dotenv()

# ============ Configuration ============
class Config:
    # RPC endpoints (in order of preference)
    RPC_ENDPOINTS = [
        os.getenv("RPC_URL", "https://api.avax.network/ext/bc/C/rpc"),
        "https://avalanche-c-chain.publicnode.com",
        "https://rpc.ankr.com/avalanche",
        "https://avax.meowrpc.com",
    ]
    
    DB_PATH = os.getenv("DB_PATH", "./data/avalytics.db")
    CHECKPOINT_FILE = os.getenv("CHECKPOINT_FILE", "./data/indexer_checkpoint.json")
    
    # Indexing parameters
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))  # Blocks per batch
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "8"))  # Parallel workers
    WALLET_UPDATE_INTERVAL = int(os.getenv("WALLET_UPDATE_INTERVAL", "1000"))  # Update profiles every N blocks
    
    # Rate limiting
    MAX_RETRIES = 5
    BASE_DELAY = 1  # seconds
    MAX_DELAY = 60  # seconds
    
    # Whale threshold (in AVAX)
    WHALE_THRESHOLD = float(os.getenv("WHALE_THRESHOLD", "1000"))  # 1000 AVAX


class ReliableIndexer:
    """Production-grade Avalanche C-Chain indexer"""
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.checkpoint_file = Config.CHECKPOINT_FILE
        self.current_rpc_index = 0
        self.w3 = None
        self._connect_rpc()
        self._init_db()
        
    def _connect_rpc(self) -> bool:
        """Connect to RPC with fallback"""
        for i, rpc_url in enumerate(Config.RPC_ENDPOINTS):
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                if w3.is_connected():
                    self.w3 = w3
                    self.current_rpc_index = i
                    print(f"✓ Connected to RPC: {rpc_url}")
                    return True
            except Exception as e:
                print(f"✗ Failed to connect to {rpc_url}: {e}")
        
        raise Exception("Could not connect to any RPC endpoint")
    
    def _switch_rpc(self):
        """Switch to next RPC endpoint"""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(Config.RPC_ENDPOINTS)
        rpc_url = Config.RPC_ENDPOINTS[self.current_rpc_index]
        print(f"⟳ Switching to RPC: {rpc_url}")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
    def _init_db(self):
        """Initialize database with indexer tracking table"""
        Path(Config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main tables if they don't exist
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS transactions (
                tx_hash TEXT PRIMARY KEY,
                block_number INTEGER NOT NULL,
                from_address TEXT NOT NULL,
                to_address TEXT,
                value TEXT,
                gas_price TEXT,
                gas_used INTEGER,
                status INTEGER DEFAULT 1,
                timestamp DATETIME,
                input_data TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_tx_block ON transactions(block_number);
            CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address);
            CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address);
            CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp);
            
            CREATE TABLE IF NOT EXISTS wallet_profiles (
                wallet_address TEXT PRIMARY KEY,
                first_seen DATETIME,
                last_active DATETIME,
                total_txs INTEGER DEFAULT 0,
                total_volume_wei TEXT DEFAULT '0',
                unique_contracts INTEGER DEFAULT 0,
                is_whale INTEGER DEFAULT 0,
                is_bot INTEGER DEFAULT 0,
                is_dex_user INTEGER DEFAULT 0,
                is_nft_collector INTEGER DEFAULT 0,
                avg_tx_value_wei TEXT,
                behavior_score REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_wallet_last_active ON wallet_profiles(last_active);
            CREATE INDEX IF NOT EXISTS idx_wallet_whale ON wallet_profiles(is_whale);
            
            -- Indexer tracking table
            CREATE TABLE IF NOT EXISTS indexer_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized")
        
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        delay = Config.BASE_DELAY
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                
                # Rate limit or timeout - retry
                if '429' in error_str or 'timeout' in error_str or 'rate' in error_str:
                    print(f"  ⚠ Rate limited, waiting {delay}s... (attempt {attempt + 1})")
                    time.sleep(delay)
                    delay = min(delay * 2, Config.MAX_DELAY)
                    
                    # Try switching RPC after 2 failures
                    if attempt >= 2:
                        self._switch_rpc()
                        
                elif 'connection' in error_str:
                    self._switch_rpc()
                    time.sleep(1)
                else:
                    raise e
                    
        raise Exception(f"Max retries exceeded for {func.__name__}")
    
    # ============ Checkpoint Management ============
    def get_checkpoint(self) -> int:
        """Get last indexed block from checkpoint"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM indexer_state WHERE key = 'last_block'")
            result = cursor.fetchone()
            conn.close()
            if result:
                return int(result[0])
        except:
            pass
        
        # Also check JSON file as fallback
        try:
            if Path(self.checkpoint_file).exists():
                with open(self.checkpoint_file) as f:
                    data = json.load(f)
                    return data.get('last_block', 0)
        except:
            pass
            
        return 0
    
    def save_checkpoint(self, block_number: int):
        """Save checkpoint to both DB and file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO indexer_state (key, value, updated_at)
            VALUES ('last_block', ?, datetime('now'))
        ''', (str(block_number),))
        conn.commit()
        conn.close()
        
        # Also save to JSON file
        Path(self.checkpoint_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_file, 'w') as f:
            json.dump({
                'last_block': block_number,
                'updated_at': datetime.now().isoformat()
            }, f)
    
    # ============ Block Extraction ============
    def get_block_fast(self, block_number: int) -> Optional[Dict]:
        """
        Get block WITHOUT fetching receipts (much faster)
        We only need from/to addresses for wallet discovery
        """
        try:
            block = self._retry_with_backoff(
                self.w3.eth.get_block, 
                block_number, 
                full_transactions=True
            )
            
            timestamp = datetime.fromtimestamp(block['timestamp'])
            txs = []
            
            for tx in block.transactions:
                txs.append({
                    'hash': tx['hash'].hex(),
                    'block_number': block_number,
                    'from_address': tx['from'].lower(),
                    'to_address': tx['to'].lower() if tx['to'] else None,
                    'value': str(tx['value']),
                    'gas_price': str(tx['gasPrice']),
                    'gas_used': tx.get('gas', 21000),  # Estimate if not available
                    'timestamp': timestamp,
                    'input_data': tx['input'][:100] if len(tx['input']) > 100 else tx['input']  # Truncate to save space
                })
            
            return {
                'block_number': block_number,
                'timestamp': timestamp,
                'tx_count': len(txs),
                'transactions': txs
            }
        except Exception as e:
            print(f"  ✗ Block {block_number}: {e}")
            return None
    
    def extract_wallets_from_batch(self, blocks_data: List[Dict]) -> Dict[str, Dict]:
        """Extract unique wallets from a batch of blocks"""
        wallets = {}
        
        for block in blocks_data:
            if not block:
                continue
                
            for tx in block['transactions']:
                # Process sender
                from_addr = tx['from_address']
                if from_addr not in wallets:
                    wallets[from_addr] = {
                        'address': from_addr,
                        'first_seen': tx['timestamp'],
                        'last_seen': tx['timestamp'],
                        'tx_count': 0,
                        'volume_wei': 0
                    }
                
                wallets[from_addr]['tx_count'] += 1
                wallets[from_addr]['volume_wei'] += int(tx['value'])
                if tx['timestamp'] > wallets[from_addr]['last_seen']:
                    wallets[from_addr]['last_seen'] = tx['timestamp']
                    
                # Process receiver (if not contract creation)
                to_addr = tx['to_address']
                if to_addr:
                    if to_addr not in wallets:
                        wallets[to_addr] = {
                            'address': to_addr,
                            'first_seen': tx['timestamp'],
                            'last_seen': tx['timestamp'],
                            'tx_count': 0,
                            'volume_wei': 0
                        }
                    
                    wallets[to_addr]['tx_count'] += 1
                    wallets[to_addr]['volume_wei'] += int(tx['value'])
                    if tx['timestamp'] > wallets[to_addr]['last_seen']:
                        wallets[to_addr]['last_seen'] = tx['timestamp']
        
        return wallets
    
    def save_batch_to_db(self, blocks_data: List[Dict], wallets: Dict[str, Dict]):
        """Save transactions and update wallet profiles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert transactions
        for block in blocks_data:
            if not block:
                continue
            for tx in block['transactions']:
                cursor.execute('''
                    INSERT OR REPLACE INTO transactions
                    (tx_hash, block_number, from_address, to_address, value, gas_price, gas_used, timestamp, input_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx['hash'], tx['block_number'], tx['from_address'], tx['to_address'],
                    tx['value'], tx['gas_price'], tx['gas_used'], tx['timestamp'], tx['input_data']
                ))
        
        # Update wallet profiles (upsert)
        whale_threshold_wei = str(int(Config.WHALE_THRESHOLD * 1e18))
        
        for addr, data in wallets.items():
            volume_wei_str = str(data['volume_wei'])
            is_whale = 1 if data['volume_wei'] >= int(whale_threshold_wei) else 0
            
            cursor.execute('''
                INSERT INTO wallet_profiles (wallet_address, first_seen, last_active, total_txs, total_volume_wei, is_whale, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(wallet_address) DO UPDATE SET
                    first_seen = MIN(first_seen, excluded.first_seen),
                    last_active = MAX(last_active, excluded.last_active),
                    total_txs = total_txs + excluded.total_txs,
                    total_volume_wei = CAST(CAST(COALESCE(total_volume_wei, '0') AS REAL) + CAST(excluded.total_volume_wei AS REAL) AS TEXT),
                    is_whale = CASE WHEN CAST(COALESCE(total_volume_wei, '0') AS REAL) + CAST(excluded.total_volume_wei AS REAL) >= CAST(? AS REAL) THEN 1 ELSE is_whale END,
                    last_updated = datetime('now')
            ''', (addr, data['first_seen'], data['last_seen'], data['tx_count'], volume_wei_str, is_whale, whale_threshold_wei))
        
        conn.commit()
        conn.close()
    
    # ============ Main Indexing Loop ============
    def index_range(self, start_block: int, end_block: int, show_progress: bool = True):
        """Index a specific range of blocks"""
        total_blocks = end_block - start_block + 1
        processed = 0
        total_txs = 0
        total_wallets = 0
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"📊 Indexing blocks {start_block:,} to {end_block:,}")
        print(f"   Total: {total_blocks:,} blocks")
        print(f"{'='*60}\n")
        
        for batch_start in range(start_block, end_block + 1, Config.BATCH_SIZE):
            batch_end = min(batch_start + Config.BATCH_SIZE - 1, end_block)
            
            # Parallel block fetching
            blocks_data = []
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = {
                    executor.submit(self.get_block_fast, bn): bn
                    for bn in range(batch_start, batch_end + 1)
                }
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        blocks_data.append(result)
            
            # Extract wallets and save
            wallets = self.extract_wallets_from_batch(blocks_data)
            self.save_batch_to_db(blocks_data, wallets)
            self.save_checkpoint(batch_end)
            
            # Stats
            batch_txs = sum(b['tx_count'] for b in blocks_data if b)
            total_txs += batch_txs
            total_wallets += len(wallets)
            processed += len(blocks_data)
            
            # Progress
            if show_progress:
                elapsed = time.time() - start_time
                blocks_per_sec = processed / elapsed if elapsed > 0 else 0
                eta = (total_blocks - processed) / blocks_per_sec if blocks_per_sec > 0 else 0
                
                print(f"  Block {batch_end:,} | "
                      f"{processed:,}/{total_blocks:,} ({100*processed/total_blocks:.1f}%) | "
                      f"{batch_txs} txs, {len(wallets)} wallets | "
                      f"{blocks_per_sec:.1f} blk/s | "
                      f"ETA: {timedelta(seconds=int(eta))}")
        
        print(f"\n{'='*60}")
        print(f"✓ Complete! Indexed {processed:,} blocks, {total_txs:,} txs, {total_wallets:,} wallets")
        print(f"  Time: {timedelta(seconds=int(time.time() - start_time))}")
        print(f"{'='*60}\n")
        
        return processed, total_txs, total_wallets
    
    def index_latest(self, num_blocks: int = 1000):
        """Index the latest N blocks"""
        latest = self.w3.eth.block_number
        start = max(0, latest - num_blocks)
        return self.index_range(start, latest)
    
    def resume_indexing(self, target_block: Optional[int] = None):
        """Resume from last checkpoint to target (or latest) block"""
        last_block = self.get_checkpoint()
        target = target_block or self.w3.eth.block_number
        
        if last_block >= target:
            print(f"✓ Already indexed up to block {last_block:,}")
            return
        
        start = last_block + 1 if last_block > 0 else max(0, target - 10000)  # Start 10k blocks back if fresh
        return self.index_range(start, target)
    
    def continuous_sync(self, poll_interval: int = 12):
        """Continuously sync new blocks (run as daemon)"""
        print(f"🔄 Starting continuous sync (polling every {poll_interval}s)...")
        
        while True:
            try:
                last = self.get_checkpoint()
                latest = self.w3.eth.block_number
                
                if latest > last:
                    self.index_range(last + 1, latest, show_progress=False)
                    print(f"  ✓ Synced to block {latest:,}")
                else:
                    print(f"  · Up to date at block {latest:,}")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
                
            time.sleep(poll_interval)


def get_stats():
    """Get current indexing stats"""
    db_path = Config.DB_PATH
    
    if not Path(db_path).exists():
        print("Database not found. Run indexer first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    stats['transactions'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM wallet_profiles")
    stats['wallets'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM wallet_profiles WHERE is_whale = 1")
    stats['whales'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(block_number), MAX(block_number) FROM transactions")
    blocks = cursor.fetchone()
    stats['block_range'] = f"{blocks[0]:,} - {blocks[1]:,}" if blocks[0] else "N/A"
    
    cursor.execute("SELECT value FROM indexer_state WHERE key = 'last_block'")
    result = cursor.fetchone()
    stats['last_indexed'] = int(result[0]) if result else 0
    
    conn.close()
    
    print(f"\n📊 Avalytics Indexer Stats")
    print(f"{'='*40}")
    print(f"  Transactions: {stats['transactions']:,}")
    print(f"  Wallets:      {stats['wallets']:,}")
    print(f"  Whales:       {stats['whales']:,}")
    print(f"  Block Range:  {stats['block_range']}")
    print(f"  Last Indexed: {stats['last_indexed']:,}")
    print(f"{'='*40}\n")
    
    return stats


# ============ CLI ============
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Avalanche Wallet Indexer")
    parser.add_argument("command", choices=["latest", "range", "resume", "sync", "stats"], 
                       help="Command to run")
    parser.add_argument("--blocks", "-n", type=int, default=1000, 
                       help="Number of blocks for 'latest' command")
    parser.add_argument("--start", "-s", type=int, help="Start block for 'range' command")
    parser.add_argument("--end", "-e", type=int, help="End block for 'range' command")
    parser.add_argument("--interval", "-i", type=int, default=12, 
                       help="Poll interval for 'sync' command")
    
    args = parser.parse_args()
    
    if args.command == "stats":
        get_stats()
    else:
        indexer = ReliableIndexer()
        
        if args.command == "latest":
            indexer.index_latest(args.blocks)
        elif args.command == "range":
            if not args.start or not args.end:
                print("Error: --start and --end required for range command")
                sys.exit(1)
            indexer.index_range(args.start, args.end)
        elif args.command == "resume":
            indexer.resume_indexing()
        elif args.command == "sync":
            indexer.continuous_sync(args.interval)
