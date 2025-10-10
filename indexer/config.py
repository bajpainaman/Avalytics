"""Indexer configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# RPC Configuration
RPC_URL = os.getenv("RPC_URL", "https://api.avax.network/ext/bc/C/rpc")

# Database
DB_PATH = os.getenv("DB_PATH", "./data/avalytics.db")

# Indexing parameters
START_BLOCK = int(os.getenv("START_BLOCK", "0"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# Output
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
