#!/usr/bin/env python3
"""
Database initialization
"""
import sqlite3
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from indexer import config

def init_database(db_path: str = config.DB_PATH):
    """Initialize SQLite database with schema"""
    Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print(f"📊 Initializing database at {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = Path(__file__).parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema = f.read()

    cursor.executescript(schema)
    conn.commit()
    conn.close()

    print("✅ Database initialized")

if __name__ == "__main__":
    init_database()
