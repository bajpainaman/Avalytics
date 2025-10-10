#!/usr/bin/env python3
"""
Avalanche Block Extractor
Pulls blocks + transactions from Avalanche C-Chain
"""
import json
import sqlite3
from pathlib import Path
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import config

class BlockExtractor:
    def __init__(self, rpc_url: str = config.RPC_URL, db_path: str = config.DB_PATH):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
        self.db_path = db_path

        Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to {rpc_url}")

        print(f"✅ Connected to Avalanche C-Chain")
        print(f"   Latest block: {self.w3.eth.block_number:,}")

    def get_block_with_txs(self, block_number: int):
        """Fetch block with full transaction details"""
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            txs = []

            for tx in block.transactions:
                receipt = self.w3.eth.get_transaction_receipt(tx['hash'])
                txs.append({
                    'hash': tx['hash'].hex(),
                    'block_number': block_number,
                    'from_address': tx['from'],
                    'to_address': tx['to'] if tx['to'] else None,
                    'value': int(tx['value']),
                    'gas_price': int(tx['gasPrice']),
                    'gas_used': int(receipt['gasUsed']),
                    'status': int(receipt['status']),
                    'timestamp': datetime.fromtimestamp(block['timestamp']),
                    'input_data': tx['input']
                })

            return {
                'block_number': block_number,
                'timestamp': datetime.fromtimestamp(block['timestamp']),
                'tx_count': len(txs),
                'transactions': txs
            }
        except Exception as e:
            print(f"❌ Error fetching block {block_number}: {e}")
            return None

    def save_to_db(self, blocks_data):
        """Save blocks and transactions to SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for block_data in blocks_data:
            if not block_data:
                continue

            for tx in block_data['transactions']:
                cursor.execute('''
                    INSERT OR REPLACE INTO transactions
                    (tx_hash, block_number, from_address, to_address, value, gas_price, gas_used, status, timestamp, input_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx['hash'], tx['block_number'], tx['from_address'], tx['to_address'],
                    str(tx['value']), str(tx['gas_price']), tx['gas_used'], tx['status'],
                    tx['timestamp'], tx['input_data']
                ))

        conn.commit()
        conn.close()
        print(f"✅ Saved to database")

    def extract_range(self, start_block: int, end_block: int):
        """Extract a range of blocks"""
        print(f"\n📦 Extracting blocks {start_block:,} to {end_block:,}")

        blocks_data = []
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.get_block_with_txs, block_num): block_num
                for block_num in range(start_block, end_block + 1)
            }

            for future in as_completed(futures):
                block_data = future.result()
                if block_data:
                    blocks_data.append(block_data)
                    if len(blocks_data) % 10 == 0:
                        print(f"   Extracted {len(blocks_data)} blocks...")

        self.save_to_db(blocks_data)
        return len(blocks_data)

    def extract_latest(self, num_blocks: int = 100):
        """Extract the latest N blocks"""
        latest = self.w3.eth.block_number
        start = max(0, latest - num_blocks)
        return self.extract_range(start, latest)

if __name__ == "__main__":
    import sys

    extractor = BlockExtractor()

    if len(sys.argv) > 1:
        num = int(sys.argv[1])
        extractor.extract_latest(num)
    else:
        extractor.extract_latest(100)
