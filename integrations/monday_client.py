#!/usr/bin/env python3
"""
Monday.com Integration for Avalytics
Sync wallet intelligence to Monday.com boards
"""
import requests
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import time


class MondayClient:
    """Monday.com API client for CRM integration"""

    def __init__(self, api_token: str = None):
        from dotenv import load_dotenv
        load_dotenv()

        self.api_url = "https://api.monday.com/v2"
        self.api_token = api_token or os.getenv("MONDAY_API_TOKEN")

        if not self.api_token:
            raise ValueError("Monday.com API token required. Set MONDAY_API_TOKEN env var or pass api_token")

        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2024-10"
        }

        # App credentials
        self.client_id = os.getenv("MONDAY_CLIENT_ID", "d9090d7691631c8e47c6ce610e213eb6")
        self.client_secret = os.getenv("MONDAY_CLIENT_SECRET", "f30f7d56d3c1458ab47c2661ee97ece4")
        self.signing_secret = os.getenv("MONDAY_SIGNING_SECRET", "ad286d85e9c3e563688a144221070e07")
        self.app_id = os.getenv("MONDAY_APP_ID", "10608176")

    def query(self, query: str, variables: Dict = None) -> Dict:
        """Execute GraphQL query against Monday.com API"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise Exception(f"Monday.com API error: {result['errors']}")

        return result.get("data", {})

    def create_board(self, board_name: str, board_kind: str = "public") -> str:
        """Create a new Monday.com board for wallet tracking"""
        query = """
        mutation ($boardName: String!, $boardKind: BoardKind!) {
            create_board (board_name: $boardName, board_kind: $boardKind) {
                id
                name
            }
        }
        """

        variables = {
            "boardName": board_name,
            "boardKind": board_kind
        }

        result = self.query(query, variables)
        board_id = result["create_board"]["id"]

        print(f"[+] Created Monday.com board: {board_name} (ID: {board_id})")

        # Add custom columns for wallet data
        self._setup_wallet_columns(board_id)

        return board_id

    def _setup_wallet_columns(self, board_id: str):
        """Setup custom columns for wallet tracking"""
        # First create basic columns
        basic_columns = [
            {"title": "Wallet Address", "column_type": "text"},
            {"title": "Total Volume (AVAX)", "column_type": "numbers"},
            {"title": "Transaction Count", "column_type": "numbers"},
            {"title": "Last Active", "column_type": "date"},
            {"title": "Tags", "column_type": "tags"},
            {"title": "AI Analysis", "column_type": "long_text"}
        ]

        for col in basic_columns:
            query = """
            mutation ($boardId: ID!, $title: String!, $columnType: ColumnType!) {
                create_column (board_id: $boardId, title: $title, column_type: $columnType) {
                    id
                    title
                }
            }
            """

            variables = {
                "boardId": board_id,
                "title": col["title"],
                "columnType": col["column_type"]
            }

            try:
                self.query(query, variables)
            except Exception as e:
                print(f"[-] Warning: Could not create column {col['title']}: {e}")

        # Create status columns with custom labels
        status_columns = [
            {
                "title": "Wallet Type",
                "labels": {"0": "WHALE", "1": "BOT", "2": "DEX", "3": "RETAIL"}
            },
            {
                "title": "Risk Level",
                "labels": {"0": "HIGH", "1": "MEDIUM", "2": "LOW"}
            },
            {
                "title": "Contact Status",
                "labels": {"0": "NEW", "1": "CONTACTED", "2": "QUALIFIED", "3": "CLOSED"}
            }
        ]

        for col in status_columns:
            query = """
            mutation ($boardId: ID!, $title: String!, $labels: JSON!) {
                create_column (
                    board_id: $boardId,
                    title: $title,
                    column_type: status,
                    defaults: $labels
                ) {
                    id
                    title
                }
            }
            """

            variables = {
                "boardId": board_id,
                "title": col["title"],
                "labels": json.dumps(col["labels"])
            }

            try:
                self.query(query, variables)
            except Exception as e:
                print(f"[-] Warning: Could not create status column {col['title']}: {e}")

    def get_board_columns(self, board_id: str) -> Dict[str, str]:
        """Get column IDs for a board"""
        query = """
        query ($boardId: [ID!]) {
            boards (ids: $boardId) {
                columns {
                    id
                    title
                    type
                }
            }
        }
        """

        result = self.query(query, {"boardId": [board_id]})
        columns = result["boards"][0]["columns"]

        # Map title to ID
        column_map = {col["title"]: col["id"] for col in columns}
        return column_map

    def add_wallet_item(self, board_id: str, wallet_data: Dict, column_map: Dict[str, str] = None) -> str:
        """Add a wallet as an item to Monday.com board"""

        if not column_map:
            column_map = self.get_board_columns(board_id)

        query = """
        mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
            create_item (
                board_id: $boardId,
                item_name: $itemName,
                column_values: $columnValues
            ) {
                id
            }
        }
        """

        # Prepare column values using actual column IDs
        wallet_address = wallet_data.get("address", "Unknown")
        column_values = {}

        # Text column - Wallet Address
        column_values["text_mkwkzjba"] = wallet_address

        # Number columns
        column_values["numeric_mkwkeqrg"] = str(wallet_data.get("volume_avax", 0))
        column_values["numeric_mkwkz2rn"] = str(wallet_data.get("tx_count", 0))

        # Status columns - use index (0, 1, 2) instead of label
        wallet_type = wallet_data.get("wallet_type", "RETAIL")
        type_map = {"WHALE": 0, "BOT": 1, "DEX": 2, "RETAIL": 2}
        column_values["color_mkwk6bwx"] = {"index": type_map.get(wallet_type, 2)}

        risk_level = wallet_data.get("risk_level", "LOW")
        risk_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        column_values["color_mkwkewf2"] = {"index": risk_map.get(risk_level, 2)}

        # Date column
        date_str = wallet_data.get("last_active", "")
        if date_str:
            column_values["date_mkwkmt8e"] = {"date": date_str[:10]}

        # Contact status
        contact_status = wallet_data.get("contact_status", "NEW")
        status_map = {"NEW": 0, "CONTACTED": 1, "QUALIFIED": 2, "CLOSED": 3}
        column_values["color_mkwkcg49"] = {"index": status_map.get(contact_status, 0)}

        # AI Analysis long text
        ai_analysis = wallet_data.get("ai_analysis", "")
        if ai_analysis:
            column_values["long_text_mkwk2g0e"] = {"text": ai_analysis}

        variables = {
            "boardId": board_id,
            "itemName": wallet_address,
            "columnValues": json.dumps(column_values)
        }

        result = self.query(query, variables)
        item_id = result["create_item"]["id"]

        return item_id

    def bulk_sync_wallets(self, board_id: str, wallets: List[Dict]) -> List[str]:
        """Bulk sync multiple wallets to Monday.com"""
        item_ids = []

        print(f"[*] Syncing {len(wallets)} wallets to Monday.com board {board_id}...")

        # Get column map once to avoid repeated API calls
        column_map = self.get_board_columns(board_id)
        print(f"[*] Found {len(column_map)} columns on board")

        for i, wallet in enumerate(wallets):
            try:
                item_id = self.add_wallet_item(board_id, wallet, column_map)
                item_ids.append(item_id)

                # Rate limiting: sleep 0.5s between requests to avoid 429 errors
                time.sleep(0.5)

                if (i + 1) % 10 == 0:
                    print(f"    Synced {i + 1}/{len(wallets)} wallets...")
            except Exception as e:
                if "429" in str(e):
                    print(f"[-] Rate limited, waiting 5 seconds...")
                    time.sleep(5)
                    # Retry once
                    try:
                        item_id = self.add_wallet_item(board_id, wallet)
                        item_ids.append(item_id)
                    except:
                        print(f"[-] Failed to sync wallet {wallet.get('address', 'unknown')}")
                else:
                    print(f"[-] Error syncing wallet {wallet.get('address', 'unknown')}: {e}")

        print(f"[+] Successfully synced {len(item_ids)} wallets")
        return item_ids

    def update_wallet_item(self, item_id: str, column_values: Dict):
        """Update an existing wallet item"""
        query = """
        mutation ($itemId: ID!, $columnValues: JSON!) {
            change_multiple_column_values (
                item_id: $itemId,
                column_values: $columnValues
            ) {
                id
            }
        }
        """

        variables = {
            "itemId": item_id,
            "columnValues": json.dumps(column_values)
        }

        self.query(query, variables)

    def get_boards(self) -> List[Dict]:
        """Get all Monday.com boards"""
        query = """
        {
            boards {
                id
                name
                state
                board_kind
            }
        }
        """

        result = self.query(query)
        return result.get("boards", [])

    def search_wallet_item(self, board_id: str, wallet_address: str) -> Optional[str]:
        """Search for a wallet item by address"""
        query = """
        query ($boardId: [ID!]!) {
            boards (ids: $boardId) {
                items_page {
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                        }
                    }
                }
            }
        }
        """

        variables = {"boardId": [board_id]}
        result = self.query(query, variables)

        if not result.get("boards"):
            return None

        items = result["boards"][0]["items_page"]["items"]

        for item in items:
            # Check if wallet address matches
            for col in item.get("column_values", []):
                if col.get("text") and wallet_address in col.get("text", ""):
                    return item["id"]

        return None

    def create_webhook(self, board_id: str, event: str, target_url: str) -> str:
        """Create a webhook for board events"""
        query = """
        mutation ($boardId: ID!, $url: String!, $event: WebhookEventType!) {
            create_webhook (board_id: $boardId, url: $url, event: $event) {
                id
            }
        }
        """

        variables = {
            "boardId": board_id,
            "url": target_url,
            "event": event
        }

        result = self.query(query, variables)
        return result["create_webhook"]["id"]


def sync_from_avalytics_db(board_id: str, db_path: str = "./data/avalytics.db", limit: int = 100):
    """Sync top wallets from Avalytics database to Monday.com"""
    import sqlite3

    client = MondayClient()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            wallet_address,
            total_txs,
            total_volume_wei,
            is_whale,
            is_bot,
            is_dex_user,
            last_active
        FROM wallet_profiles
        ORDER BY CAST(total_volume_wei AS REAL) DESC
        LIMIT ?
    ''', (limit,))

    wallets = []
    for row in cursor.fetchall():
        wallet_type = "WHALE" if row[3] else ("BOT" if row[4] else ("DEX" if row[5] else "RETAIL"))

        wallets.append({
            "address": row[0],
            "tx_count": row[1],
            "volume_avax": int(row[2]) / 10**18,
            "wallet_type": wallet_type,
            "risk_level": "HIGH" if row[3] else "LOW",
            "last_active": row[6],
            "contact_status": "NEW"
        })

    conn.close()

    # Sync to Monday.com
    item_ids = client.bulk_sync_wallets(board_id, wallets)

    return item_ids


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python monday_client.py create <board_name>")
        print("  python monday_client.py sync <board_id> [limit]")
        print("  python monday_client.py list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        board_name = sys.argv[2] if len(sys.argv) > 2 else "Avalytics Wallet Intelligence"
        client = MondayClient()
        board_id = client.create_board(board_name)
        print(f"\nBoard created! ID: {board_id}")
        print(f"Run: python monday_client.py sync {board_id}")

    elif command == "sync":
        if len(sys.argv) < 3:
            print("Error: board_id required")
            sys.exit(1)

        board_id = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100

        sync_from_avalytics_db(board_id, limit=limit)

    elif command == "list":
        client = MondayClient()
        boards = client.get_boards()

        print("\nMonday.com Boards:")
        for board in boards:
            print(f"  {board['id']}: {board['name']} ({board['board_kind']})")

    else:
        print(f"Unknown command: {command}")
