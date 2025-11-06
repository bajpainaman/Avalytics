"""Indexer configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# RPC Configuration
# Try local node first, fallback to public API
LOCAL_NODE_URL = "http://localhost:9650/ext/bc/C/rpc"
PUBLIC_RPC_URL = "https://api.avax.network/ext/bc/C/rpc"

# Check if local node is available
import requests
try:
    response = requests.get("http://localhost:9650/ext/health", timeout=2)
    if response.status_code == 200:
        RPC_URL = os.getenv("RPC_URL", LOCAL_NODE_URL)
    else:
        RPC_URL = os.getenv("RPC_URL", PUBLIC_RPC_URL)
except:
    RPC_URL = os.getenv("RPC_URL", PUBLIC_RPC_URL)

# Database
DB_PATH = os.getenv("DB_PATH", "./data/avalytics.db")

# Indexing parameters
START_BLOCK = int(os.getenv("START_BLOCK", "0"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# Output
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
