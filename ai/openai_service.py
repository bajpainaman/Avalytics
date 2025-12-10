#!/usr/bin/env python3
"""
OpenAI-Powered Intelligence Service for Avalytics
Handles ICP generation, natural language search, and smart wallet targeting
"""
import os
import json
import sqlite3
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# ============ Pydantic Models for Structured Outputs ============

class ICPCriteria(BaseModel):
    """Criteria for ideal customer profile"""
    min_volume_avax: float = Field(description="Minimum transaction volume in AVAX")
    max_volume_avax: Optional[float] = Field(default=None, description="Maximum volume (None for unlimited)")
    wallet_types: List[str] = Field(description="Target wallet types: whale, retail, bot, dex_user, nft_collector, defi_user")
    behaviors: List[str] = Field(description="Target behaviors: high_frequency, large_transactions, contract_deployer, liquidity_provider, yield_farmer, nft_trader, bridge_user")
    min_transactions: int = Field(default=1, description="Minimum number of transactions")
    active_within_days: Optional[int] = Field(default=None, description="Must be active within N days")
    exclude_bots: bool = Field(default=True, description="Exclude bot wallets")


class ICPProfile(BaseModel):
    """Generated Ideal Customer Profile"""
    name: str = Field(description="Short name for this ICP segment")
    description: str = Field(description="Description of this customer segment")
    criteria: ICPCriteria = Field(description="Filtering criteria for finding these customers")
    rationale: str = Field(description="Why this ICP makes sense for the protocol")
    outreach_strategy: str = Field(description="Recommended approach to reach these users")
    estimated_segment_size: str = Field(description="Estimated size: small (<100), medium (100-1000), large (1000+)")


class SearchQuery(BaseModel):
    """Structured search query from natural language"""
    sql_where_clause: str = Field(description="SQL WHERE clause for wallet_profiles table")
    explanation: str = Field(description="Explanation of what the search will find")


class WalletInsight(BaseModel):
    """AI-generated insight about a wallet"""
    summary: str = Field(description="One-line summary of this wallet")
    wallet_persona: str = Field(description="Persona type: whale, trader, collector, builder, etc.")
    risk_assessment: str = Field(description="Risk level: low, medium, high")
    engagement_recommendation: str = Field(description="How to approach this wallet holder")
    key_observations: List[str] = Field(description="Key observations about behavior")


# ============ OpenAI Service ============

class OpenAIService:
    """OpenAI-powered intelligence service"""
    
    def __init__(self, db_path: str = "./data/avalytics.db"):
        self.db_path = db_path
        api_key = os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_APIKEY in .env")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def generate_icp(
        self,
        protocol_name: str,
        protocol_type: str,
        description: str,
        target_market: Optional[str] = None,
        competitors: Optional[List[str]] = None
    ) -> ICPProfile:
        """Generate an Ideal Customer Profile based on protocol description"""
        
        # Get platform stats for context
        stats = self._get_platform_stats()
        
        prompt = f"""You are a crypto marketing strategist. Generate an Ideal Customer Profile (ICP) for a blockchain protocol.

PROTOCOL DETAILS:
- Name: {protocol_name}
- Type: {protocol_type}
- Description: {description}
- Target Market: {target_market or 'Not specified'}
- Competitors: {', '.join(competitors) if competitors else 'Not specified'}

AVAILABLE DATA (from our Avalanche analytics platform):
- Total wallets tracked: {stats['total_wallets']:,}
- Total volume: {stats['total_volume_avax']:,.2f} AVAX
- Whale wallets (>100 AVAX): {stats['whale_count']}
- Bot wallets: {stats['bot_count']}
- DEX users: {stats['dex_user_count']}

PROTOCOL TYPES AND TYPICAL ICPs:
- defi_lending: Target whales, institutional traders, yield farmers
- dex: Target active traders, arbitrageurs, liquidity providers
- nft_marketplace: Target NFT collectors, artists, high-volume traders
- gamefi: Target gamers, NFT holders, active daily users
- infrastructure: Target developers, contract deployers, high-frequency users
- bridge: Target cross-chain users, large transfers, DeFi power users
- yield_aggregator: Target yield farmers, whales, DeFi degens

Generate a detailed ICP with specific, actionable criteria for finding ideal users on Avalanche."""

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a crypto growth expert specializing in on-chain user acquisition. Generate specific, data-driven ICPs."},
                {"role": "user", "content": prompt}
            ],
            response_format=ICPProfile
        )
        
        return response.choices[0].message.parsed
    
    def natural_language_search(self, query: str) -> SearchQuery:
        """Convert natural language query to structured search"""
        
        # Get schema context
        schema_info = """
        TABLE: wallet_profiles
        COLUMNS:
        - wallet_address (TEXT, PRIMARY KEY)
        - total_txs (INTEGER) - total transaction count
        - total_volume_wei (TEXT) - volume in wei (divide by 10^18 for AVAX)
        - unique_contracts (INTEGER) - number of unique contracts interacted with
        - is_whale (INTEGER 0/1) - whale flag (>100 AVAX volume)
        - is_bot (INTEGER 0/1) - bot detection flag
        - is_dex_user (INTEGER 0/1) - DEX user flag
        - first_seen (DATETIME)
        - last_active (DATETIME)
        - avg_tx_value_wei (TEXT)
        
        TABLE: wallet_tags
        COLUMNS:
        - wallet_address (TEXT)
        - tag (TEXT) - cohort tags like 'high_volume', 'whale', 'frequent_trader', etc.
        - confidence (REAL)
        
        TABLE: transactions
        COLUMNS:
        - tx_hash, block_number, from_address, to_address, value, gas_used, status, timestamp
        """
        
        prompt = f"""Convert this natural language search into a SQL WHERE clause for the wallet_profiles table.

USER QUERY: "{query}"

DATABASE SCHEMA:
{schema_info}

EXAMPLES:
- "whales with more than 500 AVAX" → CAST(total_volume_wei AS REAL) > 500 * 1e18 AND is_whale = 1
- "active traders in last week" → last_active > datetime('now', '-7 days') AND total_txs > 10
- "DEX users excluding bots" → is_dex_user = 1 AND is_bot = 0
- "wallets with 50+ transactions" → total_txs >= 50

Generate a valid SQLite WHERE clause. Use CAST(total_volume_wei AS REAL) for volume comparisons.
Convert AVAX amounts to wei by multiplying by 1e18."""

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate valid SQLite WHERE clauses from natural language. Be precise and handle edge cases."},
                {"role": "user", "content": prompt}
            ],
            response_format=SearchQuery
        )
        
        return response.choices[0].message.parsed
    
    def analyze_wallet_for_outreach(self, wallet_address: str) -> WalletInsight:
        """Generate AI insights about a wallet for sales/marketing outreach"""
        
        # Fetch wallet data
        wallet_data = self._get_wallet_data(wallet_address)
        
        if not wallet_data:
            raise ValueError(f"Wallet {wallet_address} not found")
        
        prompt = f"""Analyze this Avalanche wallet for marketing/sales outreach purposes.

WALLET DATA:
- Address: {wallet_address}
- Total Transactions: {wallet_data['total_txs']}
- Total Volume: {wallet_data['volume_avax']:.2f} AVAX
- Unique Contracts: {wallet_data['unique_contracts']}
- Is Whale: {wallet_data['is_whale']}
- Is Bot: {wallet_data['is_bot']}
- Is DEX User: {wallet_data['is_dex_user']}
- First Seen: {wallet_data['first_seen']}
- Last Active: {wallet_data['last_active']}
- Cohort: {wallet_data.get('cohort', 'Unknown')}

Provide actionable insights for reaching out to this wallet holder."""

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a crypto BD/sales expert. Analyze wallets and provide actionable outreach strategies."},
                {"role": "user", "content": prompt}
            ],
            response_format=WalletInsight
        )
        
        return response.choices[0].message.parsed
    
    def suggest_target_protocols(self, protocol_type: str) -> List[Dict]:
        """Suggest competitor protocols to target users from"""
        
        protocol_map = {
            "defi_lending": [
                {"name": "AAVE", "address_hint": "aave", "chain": "avalanche"},
                {"name": "Benqi", "address_hint": "benqi", "chain": "avalanche"},
                {"name": "Trader Joe Lend", "address_hint": "traderjoe", "chain": "avalanche"},
            ],
            "dex": [
                {"name": "Trader Joe", "address_hint": "traderjoe", "chain": "avalanche"},
                {"name": "Pangolin", "address_hint": "pangolin", "chain": "avalanche"},
                {"name": "GMX", "address_hint": "gmx", "chain": "avalanche"},
            ],
            "nft_marketplace": [
                {"name": "Joepegs", "address_hint": "joepegs", "chain": "avalanche"},
                {"name": "Kalao", "address_hint": "kalao", "chain": "avalanche"},
            ],
            "yield": [
                {"name": "Yield Yak", "address_hint": "yieldyak", "chain": "avalanche"},
                {"name": "Vector Finance", "address_hint": "vector", "chain": "avalanche"},
            ],
            "bridge": [
                {"name": "Stargate", "address_hint": "stargate", "chain": "avalanche"},
                {"name": "LayerZero", "address_hint": "layerzero", "chain": "avalanche"},
            ]
        }
        
        return protocol_map.get(protocol_type, [])
    
    def generate_campaign_targets(
        self,
        icp: ICPProfile,
        max_targets: int = 100
    ) -> List[Dict]:
        """Find wallets matching an ICP"""
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query from ICP criteria
        where_clauses = []
        
        criteria = icp.criteria
        
        # Volume filter
        if criteria.min_volume_avax > 0:
            where_clauses.append(f"CAST(total_volume_wei AS REAL) >= {criteria.min_volume_avax * 1e18}")
        
        if criteria.max_volume_avax:
            where_clauses.append(f"CAST(total_volume_wei AS REAL) <= {criteria.max_volume_avax * 1e18}")
        
        # Transaction count
        if criteria.min_transactions > 1:
            where_clauses.append(f"total_txs >= {criteria.min_transactions}")
        
        # Exclude bots
        if criteria.exclude_bots:
            where_clauses.append("is_bot = 0")
        
        # Wallet type filters
        type_conditions = []
        if "whale" in criteria.wallet_types:
            type_conditions.append("is_whale = 1")
        if "dex_user" in criteria.wallet_types or "defi_user" in criteria.wallet_types:
            type_conditions.append("is_dex_user = 1")
        
        if type_conditions:
            where_clauses.append(f"({' OR '.join(type_conditions)})")
        
        # Activity filter
        if criteria.active_within_days:
            where_clauses.append(f"last_active > datetime('now', '-{criteria.active_within_days} days')")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f'''
            SELECT 
                wp.wallet_address,
                wp.total_txs,
                wp.total_volume_wei,
                wp.is_whale,
                wp.is_dex_user,
                wp.last_active,
                wt.tag as cohort
            FROM wallet_profiles wp
            LEFT JOIN wallet_tags wt ON wp.wallet_address = wt.wallet_address
            WHERE {where_sql}
            ORDER BY CAST(wp.total_volume_wei AS REAL) DESC
            LIMIT ?
        ''', (max_targets,))
        
        targets = []
        for row in cursor.fetchall():
            volume_avax = float(row['total_volume_wei'] or 0) / 1e18
            targets.append({
                "address": row['wallet_address'],
                "total_txs": row['total_txs'],
                "volume_avax": volume_avax,
                "is_whale": bool(row['is_whale']),
                "is_dex_user": bool(row['is_dex_user']),
                "last_active": row['last_active'],
                "cohort": row['cohort'].replace('_', ' ').title() if row['cohort'] else "Unknown",
                "match_score": self._calculate_match_score(row, criteria)
            })
        
        conn.close()
        
        # Sort by match score
        targets.sort(key=lambda x: x['match_score'], reverse=True)
        
        return targets
    
    def _calculate_match_score(self, wallet_row, criteria: ICPCriteria) -> float:
        """Calculate how well a wallet matches the ICP (0-1)"""
        score = 0.0
        factors = 0
        
        volume = float(wallet_row['total_volume_wei'] or 0) / 1e18
        
        # Volume score
        if criteria.min_volume_avax > 0:
            if volume >= criteria.min_volume_avax:
                score += min(1.0, volume / (criteria.min_volume_avax * 10))
            factors += 1
        
        # Whale match
        if "whale" in criteria.wallet_types:
            if wallet_row['is_whale']:
                score += 1.0
            factors += 1
        
        # DEX user match
        if "dex_user" in criteria.wallet_types or "defi_user" in criteria.wallet_types:
            if wallet_row['is_dex_user']:
                score += 1.0
            factors += 1
        
        # Transaction activity
        if criteria.min_transactions > 1:
            if wallet_row['total_txs'] >= criteria.min_transactions:
                score += min(1.0, wallet_row['total_txs'] / (criteria.min_transactions * 5))
            factors += 1
        
        return round(score / max(factors, 1), 2)
    
    def _get_platform_stats(self) -> Dict:
        """Get platform statistics for context"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT
                    COUNT(DISTINCT wallet_address) as total_wallets,
                    SUM(CAST(total_volume_wei AS REAL)) as total_volume,
                    SUM(is_whale) as whale_count,
                    SUM(is_bot) as bot_count,
                    SUM(is_dex_user) as dex_user_count
                FROM wallet_profiles
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            return {
                "total_wallets": row[0] or 0,
                "total_volume_avax": (row[1] or 0) / 1e18,
                "whale_count": row[2] or 0,
                "bot_count": row[3] or 0,
                "dex_user_count": row[4] or 0
            }
        except:
            return {
                "total_wallets": 0,
                "total_volume_avax": 0,
                "whale_count": 0,
                "bot_count": 0,
                "dex_user_count": 0
            }
    
    def _get_wallet_data(self, address: str) -> Optional[Dict]:
        """Fetch wallet data from database"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    wp.*,
                    wt.tag as cohort
                FROM wallet_profiles wp
                LEFT JOIN wallet_tags wt ON wp.wallet_address = wt.wallet_address
                WHERE wp.wallet_address = ?
            ''', (address,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                "address": row['wallet_address'],
                "total_txs": row['total_txs'],
                "volume_avax": float(row['total_volume_wei'] or 0) / 1e18,
                "unique_contracts": row['unique_contracts'] or 0,
                "is_whale": bool(row['is_whale']),
                "is_bot": bool(row['is_bot']),
                "is_dex_user": bool(row['is_dex_user']),
                "first_seen": row['first_seen'],
                "last_active": row['last_active'],
                "cohort": row['cohort']
            }
        except Exception as e:
            print(f"Error fetching wallet: {e}")
            return None


# ============ Test ============
if __name__ == "__main__":
    service = OpenAIService()
    
    print("Testing ICP Generation...")
    icp = service.generate_icp(
        protocol_name="TestLend",
        protocol_type="defi_lending",
        description="Institutional-grade lending protocol",
        target_market="whales and institutions"
    )
    print(f"Generated ICP: {icp.name}")
    print(f"Criteria: {icp.criteria}")
