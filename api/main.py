#!/usr/bin/env python3
"""
Avalytics API Server
REST API for blockchain intelligence platform
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Query, Security, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
from web3 import Web3

# Handle different web3 versions for POA middleware
try:
    from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware as poa_middleware
    except ImportError:
        poa_middleware = None

from api.models import (
    WalletProfile, WalletListResponse, CohortStats, CohortListResponse,
    PlatformStats, ChainStats, BlockInfo, TransactionInfo, BlockRangeStats,
    WalletAnalysis, TransactionPattern, IndexBlocksRequest, HealthResponse
)

# ============ Configuration ============
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data_demo/avalytics.db")
RPC_URL = os.getenv("RPC_URL", "https://api.avax.network/ext/bc/C/rpc")
API_KEYS = set(os.getenv("API_KEYS", "demo-key-123").split(","))
VERSION = "1.0.0"


# ============ Lifespan ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 Avalytics API Server starting...")
    print(f"   Database: {DB_PATH}")
    print(f"   RPC: {RPC_URL}")
    yield
    # Shutdown
    print("👋 Avalytics API Server shutting down...")


# ============ FastAPI App ============
app = FastAPI(
    title="Avalytics API",
    description="""
## Blockchain Intelligence Platform for Avalanche

Avalytics is the **Palantir for Crypto** - providing deep analytics, wallet profiling, 
and ML-powered cohort detection for the Avalanche ecosystem.

### Features:
- 🔍 **Wallet Analytics** - Profile any wallet with transaction history
- 📊 **Cohort Detection** - ML clustering of wallets by behavior
- ⛓️ **Chain Stats** - Real-time TPS, gas, and performance metrics
- 🤖 **AI Analysis** - Deep wallet analysis with LLM insights
- 📈 **Marketing Intelligence** - Identify high-value targets for campaigns

### Authentication:
All endpoints require an API key passed via `X-API-Key` header.
    """,
    version=VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Dependencies ============
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints"""
    if not api_key or api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Pass via X-API-Key header."
        )
    return api_key


def get_db():
    """Get database connection"""
    if not Path(DB_PATH).exists():
        raise HTTPException(status_code=500, detail="Database not initialized. Run indexer first.")
    # check_same_thread=False allows SQLite to work across threads
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_web3():
    """Get Web3 connection with POA middleware"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
    if poa_middleware:
        w3.middleware_onion.inject(poa_middleware, layer=0)
    if not w3.is_connected():
        raise HTTPException(status_code=503, detail="Cannot connect to Avalanche RPC")
    return w3


# ============ Health Endpoints ============
@app.get("/", tags=["Health"])
async def root():
    """API root - returns basic info"""
    return {
        "name": "Avalytics API",
        "version": VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if Path(DB_PATH).exists() else "not found"
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 5}))
        rpc_connected = w3.is_connected()
    except:
        rpc_connected = False
    
    return HealthResponse(
        status="healthy" if db_status == "connected" and rpc_connected else "degraded",
        version=VERSION,
        database=db_status,
        rpc_connected=rpc_connected,
        timestamp=datetime.now().isoformat()
    )


# ============ Platform Stats ============
@app.get("/api/v1/stats", tags=["Analytics"])
async def get_platform_stats(
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get overall platform statistics"""
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT
            COUNT(DISTINCT wallet_address) as total_wallets,
            SUM(total_txs) as total_txs,
            SUM(CAST(total_volume_wei AS REAL)) as total_volume,
            SUM(is_whale) as whale_count,
            SUM(is_bot) as bot_count,
            SUM(is_dex_user) as dex_user_count
        FROM wallet_profiles
    ''')
    
    stats = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(DISTINCT block_number) FROM transactions')
    total_blocks = cursor.fetchone()[0] or 0
    
    total_wallets = stats['total_wallets'] or 0
    whale_count = stats['whale_count'] or 0
    
    # Return format matching dashboard expectations
    return {
        "total_wallets": total_wallets,
        "total_transactions": int(stats['total_txs'] or 0),
        "total_blocks": total_blocks,
        "blocks_indexed": total_blocks,  # Dashboard expects this name
        "total_volume_avax": (stats['total_volume'] or 0) / 10**18,
        "whale_count": whale_count,
        "whale_percentage": (whale_count / total_wallets * 100) if total_wallets > 0 else 0,
        "bot_count": int(stats['bot_count'] or 0),
        "dex_user_count": int(stats['dex_user_count'] or 0)
    }


# ============ Wallet Endpoints ============
@app.get("/api/v1/wallets", tags=["Wallets"])
async def list_wallets(
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number"),
    sort_by: str = Query("volume", enum=["volume", "txs", "contracts"]),
    whale_only: bool = Query(False, description="Filter to whale wallets only"),
    whale: bool = Query(False, description="Filter to whale wallets"),
    bot: bool = Query(False, description="Filter to bot wallets"),
    dex_user: bool = Query(False, description="Filter to DEX users"),
    min_volume: Optional[float] = Query(None, description="Minimum volume in AVAX"),
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """List wallets with filtering and pagination"""
    cursor = db.cursor()
    
    # Build query
    where_clauses = ["1=1"]
    params = []
    
    if whale_only or whale:
        where_clauses.append("is_whale = 1")
    
    if bot:
        where_clauses.append("is_bot = 1")
    
    if dex_user:
        where_clauses.append("is_dex_user = 1")
    
    if min_volume is not None:
        where_clauses.append("CAST(total_volume_wei AS REAL) >= ?")
        params.append(min_volume * 10**18)
    
    where_sql = " AND ".join(where_clauses)
    
    sort_cols = {
        "volume": "CAST(total_volume_wei AS REAL)",
        "txs": "total_txs",
        "contracts": "unique_contracts"
    }
    
    offset = (page - 1) * limit
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM wallet_profiles WHERE {where_sql}", params)
    total = cursor.fetchone()[0]
    
    # Get wallets
    cursor.execute(f'''
        SELECT wallet_address, total_txs, total_volume_wei, unique_contracts,
               is_whale, is_bot, is_dex_user, first_seen, last_active
        FROM wallet_profiles
        WHERE {where_sql}
        ORDER BY {sort_cols[sort_by]} DESC
        LIMIT ? OFFSET ?
    ''', params + [limit, offset])
    
    wallets = []
    for row in cursor.fetchall():
        # Return field names matching dashboard expectations
        # Use float() to handle scientific notation in large numbers
        wallets.append({
            "wallet_address": row['wallet_address'],
            "total_txs": row['total_txs'],
            "volume_avax": float(row['total_volume_wei'] or 0) / 10**18,
            "unique_contracts": row['unique_contracts'] or 0,
            "is_whale": bool(row['is_whale']),
            "is_bot": bool(row['is_bot']),
            "is_dex_user": bool(row['is_dex_user']),
            "first_seen": row['first_seen'],
            "last_seen": row['last_active']
        })
    
    return {
        "wallets": wallets,
        "total": total,
        "page": page,
        "limit": limit
    }


@app.get("/api/v1/wallets/{address}", tags=["Wallets"])
async def get_wallet(
    address: str,
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get detailed profile for a specific wallet"""
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT wallet_address, total_txs, total_volume_wei, unique_contracts,
               is_whale, is_bot, is_dex_user, first_seen, last_active
        FROM wallet_profiles
        WHERE wallet_address = ?
    ''', (address,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Wallet {address} not found")
    
    # Return format matching dashboard expectations
    return {
        "wallet": {
            "wallet_address": row['wallet_address'],
            "total_txs": row['total_txs'],
            "volume_avax": float(row['total_volume_wei'] or 0) / 10**18,
            "unique_contracts": row['unique_contracts'] or 0,
            "is_whale": bool(row['is_whale']),
            "is_bot": bool(row['is_bot']),
            "is_dex_user": bool(row['is_dex_user']),
            "first_seen": row['first_seen'],
            "last_seen": row['last_active']
        }
    }


@app.get("/api/v1/wallets/{address}/transactions", tags=["Wallets"])
async def get_wallet_transactions(
    address: str,
    limit: int = Query(50, ge=1, le=500),
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get transactions for a wallet"""
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT tx_hash, block_number, from_address, to_address, value, 
               gas_used, status, timestamp
        FROM transactions
        WHERE from_address = ? OR to_address = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (address, address, limit))
    
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            "hash": row['tx_hash'],
            "block_number": row['block_number'],
            "from": row['from_address'],
            "to": row['to_address'],
            "value_avax": int(row['value'] or 0) / 10**18,
            "gas_used": row['gas_used'],
            "status": "success" if row['status'] == 1 else "failed",
            "timestamp": row['timestamp'],
            "direction": "sent" if row['from_address'].lower() == address.lower() else "received"
        })
    
    return {"address": address, "transactions": transactions, "count": len(transactions)}


# ============ Cohort Endpoints ============
@app.get("/api/v1/cohorts", tags=["Cohorts"])
async def list_cohorts(
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """List all ML-detected wallet cohorts"""
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT
            wt.tag,
            COUNT(*) as wallet_count,
            AVG(CAST(wp.total_volume_wei AS REAL)) as avg_volume,
            AVG(wp.total_txs) as avg_txs,
            SUM(wp.is_whale) as whale_count
        FROM wallet_tags wt
        JOIN wallet_profiles wp ON wt.wallet_address = wp.wallet_address
        GROUP BY wt.tag
        ORDER BY wallet_count DESC
    ''')
    
    cohorts = []
    for row in cursor.fetchall():
        # Return format matching dashboard expectations
        cohorts.append({
            "cohort_name": row['tag'],  # Dashboard expects cohort_name
            "wallet_count": row['wallet_count'],
            "avg_volume_avax": (row['avg_volume'] or 0) / 10**18,
            "avg_txs": row['avg_txs'] or 0,
            "whale_count": int(row['whale_count'] or 0)
        })
    
    return {"cohorts": cohorts, "total_cohorts": len(cohorts)}


@app.get("/api/v1/cohorts/{cohort_name}/wallets", tags=["Cohorts"])
async def get_cohort_wallets(
    cohort_name: str,
    limit: int = Query(50, ge=1, le=500),
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get wallets in a specific cohort"""
    cursor = db.cursor()
    
    # Try exact match first, then try lowercase with underscores
    tag = cohort_name
    
    cursor.execute('''
        SELECT wp.wallet_address, wp.total_txs, wp.total_volume_wei, 
               wp.is_whale, wp.is_bot, wp.is_dex_user
        FROM wallet_profiles wp
        JOIN wallet_tags wt ON wp.wallet_address = wt.wallet_address
        WHERE wt.tag = ? OR wt.tag = ?
        ORDER BY CAST(wp.total_volume_wei AS REAL) DESC
        LIMIT ?
    ''', (tag, tag.lower().replace(' ', '_'), limit))
    
    wallets = []
    for row in cursor.fetchall():
        wallets.append({
            "wallet_address": row['wallet_address'],
            "total_txs": row['total_txs'],
            "volume_avax": float(row['total_volume_wei'] or 0) / 10**18,
            "is_whale": bool(row['is_whale']),
            "is_bot": bool(row['is_bot']),
            "is_dex_user": bool(row['is_dex_user'])
        })
    
    return {"cohort": cohort_name, "wallets": wallets, "count": len(wallets)}


# ============ Chain Stats Endpoints ============
@app.get("/api/v1/chain/stats", tags=["Chain"])
async def get_chain_stats(
    api_key: str = Depends(verify_api_key)
):
    """Get real-time chain status - quick endpoint for dashboard"""
    try:
        w3 = get_web3()
        latest_block = w3.eth.block_number
        gas_price = w3.eth.gas_price
        
        # Return format matching dashboard expectations
        return {
            "chain_id": 43114,  # Avalanche C-Chain
            "latest_block": latest_block,
            "gas_price_gwei": gas_price / 10**9,
            "synced": True,
            "rpc_url": RPC_URL
        }
    except Exception as e:
        return {
            "chain_id": 43114,
            "latest_block": 0,
            "gas_price_gwei": 0,
            "synced": False,
            "rpc_url": RPC_URL,
            "error": str(e)
        }


@app.get("/api/v1/chain/performance", tags=["Chain"])
async def get_chain_performance(
    blocks: int = Query(100, ge=10, le=1000, description="Number of blocks to analyze"),
    api_key: str = Depends(verify_api_key)
):
    """Get detailed chain performance statistics"""
    w3 = get_web3()
    
    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - blocks)
    
    total_txs = 0
    total_gas = 0
    total_volume = 0
    block_times = []
    prev_timestamp = None
    
    for block_num in range(start_block, latest_block + 1):
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)
            total_txs += len(block['transactions'])
            total_gas += block['gasUsed']
            
            for tx in block['transactions']:
                total_volume += int(tx['value'])
            
            if prev_timestamp:
                block_times.append(block['timestamp'] - prev_timestamp)
            prev_timestamp = block['timestamp']
        except:
            continue
    
    if not block_times:
        raise HTTPException(status_code=500, detail="Could not fetch block data")
    
    blocks_analyzed = len(block_times) + 1
    avg_block_time = sum(block_times) / len(block_times)
    total_time = avg_block_time * blocks_analyzed
    tps = total_txs / total_time if total_time > 0 else 0
    
    return {
        "latest_block": latest_block,
        "blocks_analyzed": blocks_analyzed,
        "total_transactions": total_txs,
        "total_volume_avax": total_volume / 10**18,
        "avg_block_time": avg_block_time,
        "transactions_per_second": tps,
        "avg_txs_per_block": total_txs / blocks_analyzed,
        "avg_gas_per_block": total_gas / blocks_analyzed
    }


@app.get("/api/v1/chain/block/{block_number}", response_model=BlockInfo, tags=["Chain"])
async def get_block(
    block_number: int,
    api_key: str = Depends(verify_api_key)
):
    """Get information about a specific block"""
    w3 = get_web3()
    
    try:
        block = w3.eth.get_block(block_number)
        return BlockInfo(
            block_number=block['number'],
            hash=block['hash'].hex(),
            timestamp=block['timestamp'],
            transaction_count=len(block['transactions']),
            gas_used=block['gasUsed'],
            gas_limit=block['gasLimit']
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Block not found: {e}")


@app.get("/api/v1/chain/transaction/{tx_hash}", response_model=TransactionInfo, tags=["Chain"])
async def get_transaction(
    tx_hash: str,
    api_key: str = Depends(verify_api_key)
):
    """Get information about a specific transaction"""
    w3 = get_web3()
    
    try:
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        return TransactionInfo(
            hash=tx['hash'].hex(),
            block_number=tx['blockNumber'],
            from_address=tx['from'],
            to_address=tx['to'],
            value_avax=int(tx['value']) / 10**18,
            gas_used=receipt['gasUsed'],
            status="success" if receipt['status'] == 1 else "failed"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Transaction not found: {e}")


# ============ AI Analysis Endpoints ============
@app.get("/api/v1/wallets/{address}/analyze", response_model=WalletAnalysis, tags=["AI Analysis"])
async def analyze_wallet(
    address: str,
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get AI-powered analysis of a wallet (requires Ollama)"""
    try:
        from ai.structured_analyzer import StructuredAnalyzer
        analyzer = StructuredAnalyzer(DB_PATH)
        profile = analyzer.analyze_wallet_structured(address)
        
        return WalletAnalysis(
            wallet_type=profile.wallet_type,
            risk_level=profile.risk_level,
            activity_pattern=profile.activity_pattern,
            primary_use_case=profile.primary_use_case,
            sophistication_score=profile.sophistication_score,
            key_insights=profile.key_insights,
            recommended_approach=profile.recommended_approach
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")


# ============ Indexer Endpoints ============
@app.post("/api/v1/indexer/run", tags=["Indexer"])
async def run_indexer(
    request: IndexBlocksRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Trigger block indexing (runs in background)"""
    def index_blocks(num_blocks: int):
        try:
            from indexer.extract_blocks import BlockExtractor
            extractor = BlockExtractor()
            extractor.extract_latest(num_blocks)
        except Exception as e:
            print(f"Indexer error: {e}")
    
    background_tasks.add_task(index_blocks, request.num_blocks)
    
    return {
        "status": "started",
        "message": f"Indexing {request.num_blocks} blocks in background",
        "check_status": "/api/v1/stats"
    }


@app.post("/api/v1/indexer/profile", tags=["Indexer"])
async def run_profiler(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Trigger wallet profiling (runs in background)"""
    def profile_wallets():
        try:
            from analytics.wallet_profiler import WalletProfiler
            profiler = WalletProfiler()
            profiler.build_profiles()
        except Exception as e:
            print(f"Profiler error: {e}")
    
    background_tasks.add_task(profile_wallets)
    
    return {"status": "started", "message": "Profiling wallets in background"}


@app.post("/api/v1/indexer/cohorts", tags=["Indexer"])
async def run_cohort_detection(
    n_clusters: int = Query(5, ge=2, le=20),
    background_tasks: BackgroundTasks = None,
    api_key: str = Depends(verify_api_key)
):
    """Trigger ML cohort detection (runs in background)"""
    def detect_cohorts(n: int):
        try:
            from analytics.cohort_detector import CohortDetector
            detector = CohortDetector()
            detector.detect_cohorts(n)
        except Exception as e:
            print(f"Cohort detection error: {e}")
    
    background_tasks.add_task(detect_cohorts, n_clusters)
    
    return {"status": "started", "message": f"Detecting {n_clusters} cohorts in background"}


# ============ Marketing Endpoints ============
@app.get("/api/v1/marketing/targets", tags=["Marketing"])
async def get_marketing_targets(
    min_volume: float = Query(10.0, description="Minimum volume in AVAX"),
    max_results: int = Query(100, ge=1, le=1000),
    exclude_bots: bool = Query(True, description="Exclude bot wallets"),
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get high-value wallet targets for marketing campaigns"""
    cursor = db.cursor()
    
    where_clauses = [f"CAST(total_volume_wei AS REAL) >= {min_volume * 10**18}"]
    if exclude_bots:
        where_clauses.append("is_bot = 0")
    
    where_sql = " AND ".join(where_clauses)
    
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
    ''', (max_results,))
    
    targets = []
    for row in cursor.fetchall():
        targets.append({
            "address": row['wallet_address'],
            "total_txs": row['total_txs'],
            "volume_avax": float(row['total_volume_wei'] or 0) / 10**18,
            "is_whale": bool(row['is_whale']),
            "is_dex_user": bool(row['is_dex_user']),
            "last_active": row['last_active'],
            "cohort": row['cohort'].replace('_', ' ').title() if row['cohort'] else "Unknown",
            "priority": "high" if row['is_whale'] else ("medium" if row['is_dex_user'] else "standard")
        })
    
    return {
        "targets": targets,
        "count": len(targets),
        "criteria": {
            "min_volume_avax": min_volume,
            "exclude_bots": exclude_bots
        }
    }


# ============ Export Endpoints ============
@app.get("/api/v1/export/wallets", tags=["Export"])
async def export_wallets(
    format: str = Query("json", enum=["json", "csv"]),
    limit: int = Query(1000, ge=1, le=10000),
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """Export wallet data for external use"""
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT wallet_address, total_txs, total_volume_wei, unique_contracts,
               is_whale, is_bot, is_dex_user, first_seen, last_active
        FROM wallet_profiles
        ORDER BY CAST(total_volume_wei AS REAL) DESC
        LIMIT ?
    ''', (limit,))
    
    wallets = []
    for row in cursor.fetchall():
        wallets.append({
            "address": row['wallet_address'],
            "total_txs": row['total_txs'],
            "volume_avax": float(row['total_volume_wei'] or 0) / 10**18,
            "unique_contracts": row['unique_contracts'] or 0,
            "is_whale": bool(row['is_whale']),
            "is_bot": bool(row['is_bot']),
            "is_dex_user": bool(row['is_dex_user']),
            "first_seen": row['first_seen'],
            "last_active": row['last_active']
        })
    
    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        if wallets:
            writer = csv.DictWriter(output, fieldnames=wallets[0].keys())
            writer.writeheader()
            writer.writerows(wallets)
        return JSONResponse(
            content={"csv": output.getvalue()},
            headers={"Content-Disposition": "attachment; filename=wallets.csv"}
        )
    
    return {"wallets": wallets, "count": len(wallets), "format": format}


# ============ AI-Powered Endpoints ============

class ICPRequest(BaseModel):
    """Request model for ICP generation"""
    protocol_name: str
    protocol_description: str  # Dashboard sends this field name
    target_audience: Optional[str] = None  # Dashboard sends this field name
    # Legacy field names for backwards compatibility
    protocol_type: Optional[str] = None
    description: Optional[str] = None
    target_market: Optional[str] = None
    competitors: Optional[List[str]] = None


class NaturalSearchRequest(BaseModel):
    """Request for natural language search"""
    query: str
    max_results: int = 100


@app.post("/api/v1/icp/generate", tags=["AI Intelligence"])
async def generate_icp(
    request: ICPRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    🎯 Generate Ideal Customer Profile from your protocol description
    
    This AI-powered endpoint takes your protocol details and generates:
    - Specific targeting criteria (volume, wallet types, behaviors)
    - Rationale for why these users are ideal
    - Outreach strategy recommendations
    - Matching wallets from our database
    
    **Protocol Types:**
    - `defi_lending` - Lending/borrowing protocols
    - `dex` - Decentralized exchanges
    - `nft_marketplace` - NFT platforms
    - `gamefi` - Gaming/P2E protocols
    - `infrastructure` - Dev tools, oracles, etc.
    - `bridge` - Cross-chain bridges
    - `yield_aggregator` - Yield optimization
    """
    try:
        from ai.openai_service import OpenAIService
        
        service = OpenAIService(DB_PATH)
        
        # Handle both dashboard and legacy field names
        protocol_type = request.protocol_type or "defi"  # Default type
        description = request.protocol_description or request.description or ""
        target_market = request.target_audience or request.target_market
        
        # Generate ICP
        icp = service.generate_icp(
            protocol_name=request.protocol_name,
            protocol_type=protocol_type,
            description=description,
            target_market=target_market,
            competitors=request.competitors
        )
        
        # Find matching wallets
        targets = service.generate_campaign_targets(icp, max_targets=50)
        
        # Return format matching dashboard expectations
        return {
            "protocol": request.protocol_name,
            "icp": {
                "name": icp.name,
                "description": icp.description,
                "criteria": {
                    "min_transaction_count": icp.criteria.min_transactions,
                    "min_volume_usd": icp.criteria.min_volume_avax * 25,  # Rough AVAX to USD
                    "wallet_age_days": icp.criteria.active_within_days or 30,
                    "required_behaviors": icp.criteria.behaviors,
                    "excluded_behaviors": ["bot"] if icp.criteria.exclude_bots else []
                },
                "outreach_strategy": icp.outreach_strategy
            },
            "matching_wallets": len(targets),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ICP generation failed: {str(e)}")


class ICPCampaignRequest(BaseModel):
    """Request for ICP-based campaign post"""
    protocol_name: str
    icp_name: str
    icp_description: str
    outreach_strategy: str
    matching_wallets: int
    required_behaviors: List[str] = []
    post_type: str = "launch"  # launch, engagement, announcement


@app.post("/api/v1/icp/campaign-post", tags=["AI Intelligence"])
async def generate_icp_campaign_post(
    request: ICPCampaignRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    📣 Generate X/Twitter marketing campaign post from ICP
    
    Creates targeted social media content based on your generated ICP.
    Returns ready-to-post content with Twitter intent URL.
    """
    try:
        from openai import OpenAI
        
        api_key_openai = os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_API_KEY")
        if not api_key_openai:
            raise HTTPException(status_code=400, detail="OpenAI API key required")
        
        client = OpenAI(api_key=api_key_openai)
        
        system_prompt = """You are an expert crypto marketing copywriter. Create compelling X/Twitter posts for blockchain protocols.

Rules:
- Keep under 280 characters for single tweet
- Use relevant emojis (2-3 max)
- Include $AVAX or relevant tickers
- Add 2-3 hashtags
- Be exciting but not spammy
- Focus on value proposition
- Create FOMO or urgency when appropriate
- NO financial advice"""

        user_prompt = f"""Create a {request.post_type} marketing post for X/Twitter.

Protocol: {request.protocol_name}
Target Audience: {request.icp_name}
About: {request.icp_description}
Strategy: {request.outreach_strategy}
Audience Size: {request.matching_wallets} matching wallets identified
Key Behaviors: {', '.join(request.required_behaviors) if request.required_behaviors else 'active traders'}

Generate ONE compelling tweet that would appeal to this target audience. Make it engaging and action-oriented."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=300
        )
        
        content = response.choices[0].message.content.strip()
        
        # Truncate if needed
        if len(content) > 280:
            content = content[:277] + "..."
        
        # Generate Twitter intent URL
        import urllib.parse
        encoded_text = urllib.parse.quote(content, safe='')
        intent_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        
        return {
            "content": content,
            "character_count": len(content),
            "intent_url": intent_url,
            "ready_to_post": len(content) <= 280,
            "post_type": request.post_type,
            "protocol": request.protocol_name,
            "target_audience": request.icp_name,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign post generation failed: {str(e)}")


@app.post("/api/v1/search/natural", tags=["AI Intelligence"])
async def natural_language_search(
    request: NaturalSearchRequest,
    api_key: str = Depends(verify_api_key),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    🔍 Search wallets using natural language
    
    Examples:
    - "Find whales with more than 500 AVAX"
    - "Active traders in the last week"
    - "DEX users excluding bots"
    - "Wallets with 50+ transactions and high volume"
    - "New wallets from this month with significant activity"
    """
    try:
        from ai.openai_service import OpenAIService
        
        service = OpenAIService(DB_PATH)
        
        # Convert natural language to SQL
        search_query = service.natural_language_search(request.query)
        
        cursor = db.cursor()
        
        # Execute the generated query
        try:
            cursor.execute(f'''
                SELECT wallet_address, total_txs, total_volume_wei, 
                       is_whale, is_bot, is_dex_user, last_active, first_seen
                FROM wallet_profiles
                WHERE {search_query.sql_where_clause}
                ORDER BY CAST(total_volume_wei AS REAL) DESC
                LIMIT ?
            ''', (request.max_results,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "wallet_address": row['wallet_address'],
                    "total_txs": row['total_txs'],
                    "volume_avax": float(row['total_volume_wei'] or 0) / 1e18,
                    "is_whale": bool(row['is_whale']),
                    "is_bot": bool(row['is_bot']),
                    "is_dex_user": bool(row['is_dex_user']),
                    "first_seen": row['first_seen'],
                    "last_seen": row['last_active']
                })
            
            # Return format matching dashboard expectations
            return {
                "query": request.query,
                "interpretation": {
                    "intent": "wallet_search",
                    "filters": [search_query.explanation]
                },
                "results": results,
                "total_matches": len(results)
            }
            
        except sqlite3.Error as e:
            return {
                "query": request.query,
                "interpretation": {
                    "intent": "wallet_search",
                    "filters": [search_query.explanation]
                },
                "error": f"Query execution failed: {str(e)}",
                "results": [],
                "total_matches": 0
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/v1/wallets/{address}/insights", tags=["AI Intelligence"])
async def get_wallet_insights(
    address: str,
    api_key: str = Depends(verify_api_key)
):
    """
    🧠 Get AI-generated insights about a wallet for outreach
    
    Returns:
    - Wallet persona classification
    - Risk assessment
    - Engagement recommendations
    - Key behavioral observations
    """
    try:
        from ai.openai_service import OpenAIService
        
        service = OpenAIService(DB_PATH)
        insight = service.analyze_wallet_for_outreach(address)
        
        return {
            "address": address,
            "insights": {
                "summary": insight.summary,
                "persona": insight.wallet_persona,
                "risk_level": insight.risk_assessment,
                "engagement_strategy": insight.engagement_recommendation,
                "observations": insight.key_observations
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@app.get("/api/v1/protocols/suggestions", tags=["AI Intelligence"])
async def get_protocol_suggestions(
    protocol_type: str = Query(..., description="Protocol type: defi_lending, dex, nft_marketplace, yield, bridge"),
    api_key: str = Depends(verify_api_key)
):
    """
    📋 Get competitor protocols to target users from
    
    Returns known protocols on Avalanche that you might want to target users from.
    """
    try:
        from ai.openai_service import OpenAIService
        
        service = OpenAIService(DB_PATH)
        suggestions = service.suggest_target_protocols(protocol_type)
        
        return {
            "protocol_type": protocol_type,
            "competitors": suggestions,
            "usage": "Use these protocol names/addresses to find their users in our database"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@app.post("/api/v1/campaigns/create", tags=["Marketing Campaigns"])
async def create_campaign_targets(
    protocol_name: str = Query(..., description="Your protocol name"),
    protocol_type: str = Query(..., description="Protocol type"),
    description: str = Query(..., description="What your protocol does"),
    max_targets: int = Query(100, ge=10, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """
    🚀 One-click campaign target generation
    
    Combines ICP generation + wallet matching into a single call.
    Perfect for quickly building a marketing list.
    """
    try:
        from ai.openai_service import OpenAIService
        
        service = OpenAIService(DB_PATH)
        
        # Generate ICP
        icp = service.generate_icp(
            protocol_name=protocol_name,
            protocol_type=protocol_type,
            description=description
        )
        
        # Get targets
        targets = service.generate_campaign_targets(icp, max_targets=max_targets)
        
        # Prepare export-ready data
        export_data = []
        for t in targets:
            export_data.append({
                "address": t['address'],
                "volume_avax": round(t['volume_avax'], 2),
                "transactions": t['total_txs'],
                "segment": t['cohort'],
                "priority": "🔥 High" if t['match_score'] > 0.7 else ("⚡ Medium" if t['match_score'] > 0.4 else "📊 Standard"),
                "match_score": t['match_score']
            })
        
        return {
            "campaign": {
                "name": f"{protocol_name} - {icp.name}",
                "icp_summary": icp.description,
                "targeting_criteria": icp.criteria.model_dump(),
                "recommended_approach": icp.outreach_strategy
            },
            "targets": export_data,
            "stats": {
                "total_targets": len(targets),
                "high_priority": len([t for t in targets if t['match_score'] > 0.7]),
                "total_volume_avax": round(sum(t['volume_avax'] for t in targets), 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")


# ============ Pattern Analysis Endpoints ============

@app.post("/api/v1/patterns/analyze", tags=["Pattern Analysis"])
async def analyze_patterns(
    days: int = Query(7, ge=1, le=90, description="Days to analyze"),
    api_key: str = Depends(verify_api_key)
):
    """
    🔍 Analyze behavioral patterns across wallets
    
    Detects:
    - **Accumulators** - Wallets receiving more than sending
    - **Distributors** - Wallets sending more than receiving  
    - **High Frequency** - Wallets with many transactions
    - **New Whales** - Recently emerged high-value wallets
    """
    try:
        from analytics.pattern_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer(DB_PATH)
        result = analyzer.analyze_patterns(days=days)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")


@app.get("/api/v1/patterns/heatmap", tags=["Pattern Analysis"])
async def get_activity_heatmap(
    days: int = Query(30, ge=7, le=90, description="Days to analyze"),
    api_key: str = Depends(verify_api_key)
):
    """
    🗓️ Get activity heatmap (when users are most active)
    
    Returns a 7x24 grid showing activity levels by day and hour.
    Perfect for timing your posts and campaigns!
    """
    try:
        from analytics.pattern_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer(DB_PATH)
        result = analyzer.get_activity_heatmap(days=days)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")


@app.get("/api/v1/patterns/trends", tags=["Pattern Analysis"])
async def get_trends(
    days: int = Query(7, ge=1, le=30, description="Period to compare"),
    api_key: str = Depends(verify_api_key)
):
    """
    📈 Get trending behaviors and metrics
    
    Compares current period vs previous period to identify:
    - Volume changes
    - Transaction count changes
    - New wallet trends
    - Average transaction size changes
    """
    try:
        from analytics.pattern_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer(DB_PATH)
        result = analyzer.get_trends(days=days)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


# ============ Social Media Endpoints ============

class GeneratePostRequest(BaseModel):
    post_type: str  # stats, whale_alert, trends, custom
    custom_prompt: Optional[str] = None


class PostToXRequest(BaseModel):
    content: str
    is_thread: bool = False
    tweets: Optional[List[str]] = None


@app.get("/api/v1/social/templates", tags=["Social Media"])
async def get_post_templates(
    api_key: str = Depends(verify_api_key)
):
    """
    📋 Get available post templates
    """
    try:
        from integrations.x_client import XClient
        
        client = XClient(DB_PATH)
        return {"templates": client.get_post_templates()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/social/generate-post", tags=["Social Media"])
async def generate_social_post(
    request: GeneratePostRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    🤖 Generate an AI-powered X/Twitter post using real analytics data
    
    **Post Types:**
    - `stats` - Weekly network statistics
    - `whale_alert` - Large wallet movement alerts
    - `trends` - Trend analysis and insights
    - `custom` - Your own prompt (provide custom_prompt)
    
    The AI uses real data from Avalytics to create engaging, data-driven content.
    """
    try:
        from integrations.x_client import XClient
        
        client = XClient(DB_PATH)
        result = client.generate_post(
            post_type=request.post_type,
            custom_prompt=request.custom_prompt
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Post generation failed: {str(e)}")


@app.post("/api/v1/social/prepare-post", tags=["Social Media"])
async def prepare_post(
    request: PostToXRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    🔗 Prepare post and get Twitter intent URL
    
    Returns a clickable URL that opens Twitter with your content pre-filled.
    No API keys needed - user posts manually via the link!
    """
    try:
        from integrations.x_client import XClient
        
        client = XClient(DB_PATH)
        
        if request.is_thread and request.tweets:
            result = client.prepare_thread(request.tweets)
        else:
            result = client.prepare_post(request.content)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preparation failed: {str(e)}")


@app.post("/api/v1/social/generate-ready", tags=["Social Media"])
async def generate_ready_to_post(
    post_type: str = Query(..., description="Post type: stats, whale_alert, trends"),
    api_key: str = Depends(verify_api_key)
):
    """
    🚀 One-click: Generate AI post with Twitter intent URL
    
    Generates content and returns a ready-to-use Twitter link.
    Click the link → Twitter opens → Post!
    """
    try:
        from integrations.x_client import XClient
        
        client = XClient(DB_PATH)
        
        # Generate content
        generated = client.generate_post(post_type=post_type)
        
        # Prepare with intent URL
        if generated['is_thread']:
            prepared = client.prepare_thread(generated['tweets'])
        else:
            prepared = client.prepare_post(generated['tweets'][0])
        
        return {
            "post_type": post_type,
            "generated": generated,
            "ready": prepared
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


# ============ Run Server ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
