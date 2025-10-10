#!/usr/bin/env python3
"""
Wallet Profiler
Builds wallet profiles from transaction data
"""
import sqlite3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from indexer import config
from datetime import datetime

class WalletProfiler:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    def build_profiles(self):
        """Build wallet profiles from transactions"""
        print("\n🧠 Building wallet profiles...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all unique wallets
        cursor.execute('''
            SELECT DISTINCT from_address FROM transactions
            UNION
            SELECT DISTINCT to_address FROM transactions WHERE to_address IS NOT NULL
        ''')

        wallets = [row[0] for row in cursor.fetchall()]
        print(f"   Found {len(wallets)} unique wallets")

        for i, wallet in enumerate(wallets):
            self._profile_wallet(cursor, wallet)

            if (i + 1) % 100 == 0:
                print(f"   Profiled {i + 1}/{len(wallets)} wallets...")
                conn.commit()

        conn.commit()
        conn.close()
        print(f"✅ Profiled {len(wallets)} wallets")

    def _profile_wallet(self, cursor, wallet_address: str):
        """Profile a single wallet"""
        # Get transaction stats
        cursor.execute('''
            SELECT
                COUNT(*) as tx_count,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_active,
                SUM(CASE WHEN from_address = ? THEN value ELSE 0 END) as total_sent,
                AVG(CASE WHEN from_address = ? THEN value ELSE 0 END) as avg_tx_value,
                COUNT(DISTINCT CASE WHEN from_address = ? THEN to_address END) as unique_contracts
            FROM transactions
            WHERE from_address = ? OR to_address = ?
        ''', (wallet_address, wallet_address, wallet_address, wallet_address, wallet_address))

        stats = cursor.fetchone()

        tx_count, first_seen, last_active, total_sent, avg_tx_value, unique_contracts = stats

        # Whale detection (>100 AVAX equivalent in wei)
        is_whale = 1 if total_sent and int(total_sent) > 100 * 10**18 else 0

        # Bot detection (high frequency, low variance)
        cursor.execute('''
            SELECT COUNT(*) as tx_per_day
            FROM transactions
            WHERE from_address = ?
            AND timestamp > datetime('now', '-1 day')
        ''', (wallet_address,))

        tx_per_day = cursor.fetchone()[0]
        is_bot = 1 if tx_per_day > 50 else 0

        # DEX user detection (interacts with known DEX contracts)
        # Simplified: checks if interacts with contracts frequently
        is_dex_user = 1 if unique_contracts and unique_contracts > 10 else 0

        # Insert or update profile
        cursor.execute('''
            INSERT OR REPLACE INTO wallet_profiles
            (wallet_address, first_seen, last_active, total_txs, total_volume_wei,
             unique_contracts, is_whale, is_bot, is_dex_user, avg_tx_value_wei, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallet_address, first_seen, last_active, tx_count, str(total_sent) if total_sent else '0',
            unique_contracts, is_whale, is_bot, is_dex_user, str(avg_tx_value) if avg_tx_value else '0',
            datetime.now()
        ))

if __name__ == "__main__":
    profiler = WalletProfiler()
    profiler.build_profiles()
