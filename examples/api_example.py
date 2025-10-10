#!/usr/bin/env python3
"""
Example of using Avalytics programmatically
This shows how to integrate Avalytics into your own applications
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
from indexer import config
from ai.ollama_client import OllamaClient

def get_top_wallets(limit=10):
    """Get top wallets by transaction count"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f'''
        SELECT wallet_address, total_txs, total_volume_wei, is_whale
        FROM wallet_profiles
        ORDER BY total_txs DESC
        LIMIT {limit}
    ''')

    results = cursor.fetchall()
    conn.close()

    return results

def get_wallet_profile(address):
    """Get detailed profile for a wallet"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM wallet_profiles
        WHERE wallet_address = ?
    ''', (address,))

    profile = cursor.fetchone()
    conn.close()

    return dict(profile) if profile else None

def ai_analyze_wallet(address):
    """Get AI analysis of a wallet"""
    profile = get_wallet_profile(address)

    if not profile:
        return "Wallet not found"

    ai = OllamaClient()
    analysis = ai.explain_wallet_behavior(profile)

    return analysis

def natural_language_query(query):
    """Execute a natural language query"""
    ai = OllamaClient()

    # Load schema
    schema_path = Path(__file__).parent.parent / "ai" / "schema_context.txt"
    with open(schema_path, 'r') as f:
        schema = f.read()

    # Convert to SQL
    sql = ai.natural_language_to_sql(query, schema)

    # Execute
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()

    return results

# Example usage
if __name__ == "__main__":
    print("Avalytics API Examples")
    print("=" * 50)

    # Example 1: Get top wallets
    print("\nTop 5 wallets by transaction count:")
    wallets = get_top_wallets(5)
    for wallet in wallets:
        print(f"  {wallet[0][:10]}... : {wallet[1]} txs, Whale: {bool(wallet[3])}")

    # Example 2: Profile a specific wallet
    if wallets:
        address = wallets[0][0]
        print(f"\nProfile for {address[:10]}...:")
        profile = get_wallet_profile(address)
        if profile:
            print(f"  Total txs: {profile['total_txs']}")
            print(f"  Volume: {profile['total_volume_wei'] / 10**18:.2f} AVAX")
            print(f"  Whale: {bool(profile['is_whale'])}")

    # Example 3: Natural language query
    print("\nNatural language query: 'show wallets with more than 10 transactions'")
    try:
        results = natural_language_query("show wallets with more than 10 transactions")
        print(f"  Found {len(results)} results")
    except Exception as e:
        print(f"  Query failed: {e}")
