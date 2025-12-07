#!/usr/bin/env python3
"""
Import wallets from third-party APIs
Much faster than indexing from scratch!
"""
import os
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/avalytics.db")


class CovalentImporter:
    """
    Import wallets using Covalent API
    Get free key at: https://www.covalenthq.com/platform/#/auth/register/
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.covalenthq.com/v1"
        self.chain_id = "43114"  # Avalanche C-Chain
        
    def get_top_wallets_by_balance(self, limit: int = 1000) -> list:
        """Get top wallets by AVAX balance"""
        # Note: Covalent doesn't have a direct "all wallets" endpoint
        # but you can get token holders, NFT owners, etc.
        print("⚠️ Covalent requires specific token/contract queries")
        return []
    
    def get_token_holders(self, token_address: str, page_size: int = 100) -> list:
        """Get holders of a specific token (e.g., WAVAX)"""
        url = f"{self.base_url}/{self.chain_id}/tokens/{token_address}/token_holders_v2/"
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"page-size": page_size}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("data", {}).get("items", [])
        except Exception as e:
            print(f"Error: {e}")
            return []


class MoralisImporter:
    """
    Import wallets using Moralis API
    Get free key at: https://admin.moralis.io/
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://deep-index.moralis.io/api/v2.2"
        
    def get_block_transactions(self, block_number: int) -> list:
        """Get all transactions from a block"""
        url = f"{self.base_url}/block/{block_number}"
        headers = {"X-API-Key": self.api_key}
        params = {"chain": "avalanche"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("transactions", [])
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_wallet_activity(self, address: str) -> dict:
        """Get wallet transaction history"""
        url = f"{self.base_url}/{address}"
        headers = {"X-API-Key": self.api_key}
        params = {"chain": "avalanche"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return {}


class DuneImporter:
    """
    Import wallets from Dune Analytics
    Best for bulk wallet data - can query ALL unique addresses
    Get API key at: https://dune.com/settings/api
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.dune.com/api/v1"
        
    def execute_query(self, query_id: int) -> dict:
        """Execute a Dune query and get results"""
        # Execute
        url = f"{self.base_url}/query/{query_id}/execute"
        headers = {"X-Dune-API-Key": self.api_key}
        
        response = requests.post(url, headers=headers)
        execution_id = response.json().get("execution_id")
        
        # Poll for results
        import time
        for _ in range(60):  # Wait up to 5 minutes
            status_url = f"{self.base_url}/execution/{execution_id}/status"
            status = requests.get(status_url, headers=headers).json()
            
            if status.get("state") == "QUERY_STATE_COMPLETED":
                results_url = f"{self.base_url}/execution/{execution_id}/results"
                return requests.get(results_url, headers=headers).json()
            
            time.sleep(5)
        
        return {}
    
    def get_all_unique_wallets_query(self) -> str:
        """
        SQL query to get all unique wallets on Avalanche
        Create this query on Dune and use execute_query with its ID
        """
        return """
        -- All unique Avalanche C-Chain addresses
        -- Run on Dune: https://dune.com/queries/new
        
        SELECT DISTINCT address, 
               COUNT(*) as tx_count,
               SUM(value) as total_volume,
               MIN(block_time) as first_seen,
               MAX(block_time) as last_seen
        FROM (
            SELECT "from" as address, value, block_time FROM avalanche_c.transactions
            UNION ALL
            SELECT "to" as address, value, block_time FROM avalanche_c.transactions WHERE "to" IS NOT NULL
        )
        GROUP BY address
        ORDER BY total_volume DESC
        """


def import_from_snowtrace():
    """
    Alternative: Export from Snowtrace (manual)
    
    1. Go to https://snowtrace.io/exportData
    2. Select "Transactions" 
    3. Choose block range
    4. Download CSV
    5. Import using this function
    """
    import csv
    
    csv_path = "./data/snowtrace_export.csv"
    
    if not Path(csv_path).exists():
        print(f"""
📋 Manual Snowtrace Export Instructions:

1. Go to https://snowtrace.io/exportData
2. Select type: "Transactions"
3. Set block range (e.g., last 1M blocks)
4. Download CSV
5. Save to: {csv_path}
6. Run this script again
        """)
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        wallets = {}
        
        for row in reader:
            from_addr = row.get('From', '').lower()
            to_addr = row.get('To', '').lower()
            value = int(row.get('Value', 0))
            timestamp = row.get('DateTime', '')
            
            for addr in [from_addr, to_addr]:
                if addr and addr.startswith('0x'):
                    if addr not in wallets:
                        wallets[addr] = {'count': 0, 'volume': 0}
                    wallets[addr]['count'] += 1
                    wallets[addr]['volume'] += value
        
        # Insert into DB
        for addr, data in wallets.items():
            cursor.execute('''
                INSERT OR REPLACE INTO wallet_profiles 
                (wallet_address, total_txs, total_volume_wei, last_updated)
                VALUES (?, ?, ?, datetime('now'))
            ''', (addr, data['count'], str(data['volume'])))
    
    conn.commit()
    conn.close()
    print(f"✓ Imported {len(wallets)} wallets from Snowtrace CSV")


# ============ Quick Start ============
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Third-Party Wallet Import Options                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. COVALENT API                                             ║
║     - Best for: Token holders, NFT owners                    ║
║     - Get key: https://www.covalenthq.com/platform/          ║
║     - Set: COVALENT_API_KEY in .env                          ║
║                                                              ║
║  2. MORALIS API                                              ║
║     - Best for: Transaction history, wallet activity         ║
║     - Get key: https://admin.moralis.io/                     ║
║     - Set: MORALIS_API_KEY in .env                           ║
║                                                              ║
║  3. DUNE ANALYTICS                                           ║
║     - Best for: BULK wallet data, SQL queries                ║
║     - Get key: https://dune.com/settings/api                 ║
║     - Set: DUNE_API_KEY in .env                              ║
║     - Create query with get_all_unique_wallets_query()       ║
║                                                              ║
║  4. SNOWTRACE EXPORT (Manual)                                ║
║     - Best for: Free, no API key needed                      ║
║     - Go to: https://snowtrace.io/exportData                 ║
║     - Download CSV, run import_from_snowtrace()              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Example usage
    covalent_key = os.getenv("COVALENT_API_KEY")
    if covalent_key:
        importer = CovalentImporter(covalent_key)
        # Get WAVAX holders as example
        wavax = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"
        holders = importer.get_token_holders(wavax)
        print(f"Got {len(holders)} WAVAX holders")
