#!/usr/bin/env python3
"""
Structured Wallet Analyzer using OpenAI-compatible API with Pydantic
Uses Ollama's OpenAI-compatible endpoint for structured outputs
"""
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import os


class WalletBehaviorProfile(BaseModel):
    """Structured wallet behavior analysis"""
    wallet_type: str = Field(description="Primary wallet type: whale, degen, bot, institutional, retail, arbitrageur")
    risk_level: str = Field(description="Risk level: low, medium, high, extreme")
    activity_pattern: str = Field(description="Activity pattern: sporadic, consistent, high_frequency, dormant")
    primary_use_case: str = Field(description="Main use: trading, liquidity_providing, nft_collecting, governance, bridging, other")
    sophistication_score: int = Field(ge=1, le=10, description="Sophistication level 1-10")
    key_insights: List[str] = Field(description="3-5 key behavioral insights")
    recommended_approach: str = Field(description="How to engage this wallet holder")


class CohortAnalysis(BaseModel):
    """Analysis of a wallet cohort"""
    cohort_name: str = Field(description="Descriptive name for this cohort")
    cohort_characteristics: List[str] = Field(description="Key characteristics of this cohort")
    typical_behavior: str = Field(description="Typical behavior pattern")
    engagement_strategy: str = Field(description="Best way to approach this cohort")
    value_proposition: str = Field(description="What matters to this cohort")


class TransactionPattern(BaseModel):
    """Pattern detected in transaction data"""
    pattern_type: str = Field(description="Type of pattern: accumulation, distribution, arbitrage, wash_trading, normal")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in pattern detection")
    explanation: str = Field(description="Explanation of the pattern")
    implications: List[str] = Field(description="What this pattern implies")


class StructuredAnalyzer:
    def __init__(self, db_path: str = "./data/avalytics.db"):
        self.db_path = db_path

        # Use OpenAI-compatible endpoint
        self.client = OpenAI(
            base_url=os.getenv("OLLAMA_URL", "http://10.246.250.44:11434") + "/v1",
            api_key="ollama"  # Ollama doesn't need real API key
        )
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def analyze_wallet_structured(self, wallet_address: str) -> WalletBehaviorProfile:
        """Get structured analysis of a wallet"""
        # Fetch wallet data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT total_txs, total_volume_wei, unique_contracts,
                   is_whale, is_bot, is_dex_user, avg_tx_value_wei,
                   first_seen, last_active
            FROM wallet_profiles
            WHERE wallet_address = ?
        ''', (wallet_address,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Wallet {wallet_address} not found")

        total_txs, total_vol, unique_contracts, is_whale, is_bot, is_dex_user, avg_tx, first_seen, last_active = row

        # Create analysis prompt
        prompt = f"""Analyze this Avalanche wallet and provide structured insights:

Wallet: {wallet_address}
- Total transactions: {total_txs}
- Total volume: {int(total_vol) / 10**18:.2f} AVAX
- Unique contracts interacted: {unique_contracts}
- Average transaction value: {int(avg_tx) / 10**18:.4f} AVAX
- Whale flag: {'Yes' if is_whale else 'No'}
- Bot flag: {'Yes' if is_bot else 'No'}
- DEX user flag: {'Yes' if is_dex_user else 'No'}
- First seen: {first_seen}
- Last active: {last_active}

Provide a comprehensive behavioral profile."""

        # Use structured output with Pydantic
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a blockchain analyst expert specializing in wallet behavior profiling."},
                {"role": "user", "content": prompt}
            ],
            response_format=WalletBehaviorProfile
        )

        return response.choices[0].message.parsed

    def analyze_cohort_structured(self, cohort_id: int) -> CohortAnalysis:
        """Get structured analysis of a wallet cohort"""
        # Fetch cohort statistics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as wallet_count,
                AVG(CAST(wp.total_volume_wei AS REAL)) as avg_volume,
                AVG(wp.total_txs) as avg_txs,
                AVG(wp.unique_contracts) as avg_contracts,
                SUM(wp.is_whale) as whale_count,
                SUM(wp.is_bot) as bot_count,
                SUM(wp.is_dex_user) as dex_user_count
            FROM wallet_profiles wp
            JOIN wallet_tags wt ON wp.wallet_address = wt.wallet_address
            WHERE wt.tag = ?
        ''', (f'cluster_{cohort_id}',))

        stats = cursor.fetchone()
        conn.close()

        wallet_count, avg_vol, avg_txs, avg_contracts, whale_count, bot_count, dex_count = stats

        prompt = f"""Analyze this wallet cohort from Avalanche blockchain:

Cohort #{cohort_id} Statistics:
- Total wallets: {wallet_count}
- Average volume: {avg_vol / 10**18:.2f} AVAX
- Average transactions: {avg_txs:.1f}
- Average unique contracts: {avg_contracts:.1f}
- Whales: {whale_count} ({whale_count/wallet_count*100:.1f}%)
- Bots: {bot_count} ({bot_count/wallet_count*100:.1f}%)
- DEX users: {dex_count} ({dex_count/wallet_count*100:.1f}%)

Provide a comprehensive cohort analysis."""

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a blockchain analyst expert specializing in user segmentation and cohort analysis."},
                {"role": "user", "content": prompt}
            ],
            response_format=CohortAnalysis
        )

        return response.choices[0].message.parsed

    def detect_transaction_pattern(self, wallet_address: str, window_size: int = 50) -> TransactionPattern:
        """Detect patterns in recent transactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT tx_hash, from_address, to_address, value, timestamp, gas_used
            FROM transactions
            WHERE from_address = ? OR to_address = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (wallet_address, wallet_address, window_size))

        txs = cursor.fetchall()
        conn.close()

        if not txs:
            raise ValueError(f"No transactions found for {wallet_address}")

        # Build transaction summary
        tx_summary = []
        for tx in txs[:10]:  # Show first 10 for context
            tx_hash, from_addr, to_addr, value, timestamp, gas = tx
            direction = "sent" if from_addr == wallet_address else "received"
            tx_summary.append(f"{timestamp}: {direction} {int(value)/10**18:.4f} AVAX")

        prompt = f"""Analyze transaction patterns for this wallet:

Wallet: {wallet_address}
Total transactions analyzed: {len(txs)}

Recent transactions:
{chr(10).join(tx_summary)}

Detect any patterns: accumulation, distribution, arbitrage, wash trading, or normal behavior."""

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a blockchain forensics expert specializing in transaction pattern detection."},
                {"role": "user", "content": prompt}
            ],
            response_format=TransactionPattern
        )

        return response.choices[0].message.parsed


if __name__ == "__main__":
    analyzer = StructuredAnalyzer()

    # Test with a random wallet
    import sqlite3
    conn = sqlite3.connect("./data/avalytics.db")
    cursor = conn.cursor()
    cursor.execute("SELECT wallet_address FROM wallet_profiles LIMIT 1")
    test_wallet = cursor.fetchone()[0]
    conn.close()

    print(f"Testing structured analysis on wallet: {test_wallet}\n")

    profile = analyzer.analyze_wallet_structured(test_wallet)
    print("Wallet Behavior Profile:")
    print(f"  Type: {profile.wallet_type}")
    print(f"  Risk: {profile.risk_level}")
    print(f"  Activity: {profile.activity_pattern}")
    print(f"  Use case: {profile.primary_use_case}")
    print(f"  Sophistication: {profile.sophistication_score}/10")
    print(f"  Insights: {profile.key_insights}")
    print(f"  Approach: {profile.recommended_approach}")
