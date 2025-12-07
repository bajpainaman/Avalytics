"""
Pydantic models for API request/response
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============ Enums ============
class WalletType(str, Enum):
    WHALE = "whale"
    BOT = "bot"
    DEX = "dex"
    RETAIL = "retail"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SortBy(str, Enum):
    VOLUME = "volume"
    TRANSACTIONS = "txs"
    CONTRACTS = "contracts"


# ============ Response Models ============
class WalletProfile(BaseModel):
    address: str
    total_txs: int
    total_volume_avax: float
    unique_contracts: int
    wallet_type: str
    is_whale: bool
    is_bot: bool
    is_dex_user: bool
    first_seen: Optional[str] = None
    last_active: Optional[str] = None


class WalletListResponse(BaseModel):
    wallets: List[WalletProfile]
    total: int
    page: int
    limit: int


class CohortStats(BaseModel):
    name: str
    wallet_count: int
    avg_volume_avax: float
    avg_txs: float
    whale_count: int


class CohortListResponse(BaseModel):
    cohorts: List[CohortStats]
    total: int


class PlatformStats(BaseModel):
    total_wallets: int
    total_transactions: int
    total_blocks: int
    total_volume_avax: float
    whale_count: int
    whale_percentage: float
    bot_count: int
    dex_user_count: int


class ChainStats(BaseModel):
    latest_block: int
    blocks_analyzed: int
    total_transactions: int
    total_volume_avax: float
    avg_block_time: float
    transactions_per_second: float
    avg_txs_per_block: float
    avg_gas_per_block: float


class BlockInfo(BaseModel):
    block_number: int
    hash: str
    timestamp: int
    transaction_count: int
    gas_used: int
    gas_limit: int


class TransactionInfo(BaseModel):
    hash: str
    block_number: int
    from_address: str
    to_address: Optional[str]
    value_avax: float
    gas_used: int
    status: str


class BlockRangeStats(BaseModel):
    from_block: int
    to_block: int
    blocks_queried: int
    total_transactions: int
    total_gas_used: int
    avg_txs_per_block: float
    avg_gas_per_block: float


# ============ AI Analysis Models ============
class WalletAnalysis(BaseModel):
    wallet_type: str
    risk_level: str
    activity_pattern: str
    primary_use_case: str
    sophistication_score: int
    key_insights: List[str]
    recommended_approach: str


class TransactionPattern(BaseModel):
    pattern_type: str
    confidence: float
    explanation: str
    implications: List[str]


# ============ Request Models ============
class IndexBlocksRequest(BaseModel):
    num_blocks: int = Field(default=100, ge=1, le=1000)


class WalletQueryParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)
    sort_by: SortBy = SortBy.VOLUME
    whale_only: bool = False
    min_volume_avax: Optional[float] = None


# ============ Health/Status ============
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    rpc_connected: bool
    timestamp: str


class APIKeyResponse(BaseModel):
    api_key: str
    created_at: str
    permissions: List[str]
