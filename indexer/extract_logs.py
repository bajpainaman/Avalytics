#!/usr/bin/env python3
"""
Event Logs Extractor
Pulls event logs from Avalanche C-Chain
"""
import sqlite3
from web3 import Web3
from datetime import datetime
import config

class LogsExtractor:
    def __init__(self, rpc_url: str = config.RPC_URL, db_path: str = config.DB_PATH):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
        self.db_path = db_path

        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to {rpc_url}")

    def extract_logs(self, from_block: int, to_block: int):
        """Extract logs for block range"""
        print(f"\n📝 Extracting logs from block {from_block:,} to {to_block:,}")

        try:
            logs = self.w3.eth.get_logs({
                'fromBlock': from_block,
                'toBlock': to_block
            })

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for log in logs:
                block = self.w3.eth.get_block(log['blockNumber'])

                cursor.execute('''
                    INSERT INTO event_logs
                    (tx_hash, block_number, log_index, address, topic0, topic1, topic2, topic3, data, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log['transactionHash'].hex(),
                    log['blockNumber'],
                    log['logIndex'],
                    log['address'],
                    log['topics'][0].hex() if len(log['topics']) > 0 else None,
                    log['topics'][1].hex() if len(log['topics']) > 1 else None,
                    log['topics'][2].hex() if len(log['topics']) > 2 else None,
                    log['topics'][3].hex() if len(log['topics']) > 3 else None,
                    log['data'],
                    datetime.fromtimestamp(block['timestamp'])
                ))

            conn.commit()
            conn.close()

            print(f"✅ Extracted {len(logs)} logs")
            return len(logs)

        except Exception as e:
            print(f"❌ Error extracting logs: {e}")
            return 0

if __name__ == "__main__":
    import sys

    extractor = LogsExtractor()

    if len(sys.argv) == 3:
        start = int(sys.argv[1])
        end = int(sys.argv[2])
        extractor.extract_logs(start, end)
    else:
        w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        latest = w3.eth.block_number
        extractor.extract_logs(latest - 100, latest)
