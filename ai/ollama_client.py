#!/usr/bin/env python3
"""
Ollama Client
Connects to local Ollama instance for AI queries
"""
import requests
import json
import os

class OllamaClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://10.246.250.44:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def query(self, prompt: str, system_prompt: str = None) -> str:
        """Send a query to Ollama"""
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except Exception as e:
            return f"Error querying Ollama: {e}"

    def natural_language_to_sql(self, nl_query: str, schema_context: str) -> str:
        """Convert natural language query to SQL"""
        system_prompt = f"""You are a SQL expert. Convert natural language queries to SQL.
Database schema:
{schema_context}

Rules:
- Return ONLY the SQL query, no explanation
- Use proper SQLite syntax
- Table names: transactions, wallet_profiles, wallet_tags, event_logs
"""

        prompt = f"Convert this to SQL: {nl_query}"

        sql = self.query(prompt, system_prompt)

        # Extract SQL from response (remove markdown if present)
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()

        return sql

    def explain_wallet_behavior(self, wallet_stats: dict) -> str:
        """Get AI explanation of wallet behavior"""
        prompt = f"""Analyze this wallet's behavior:
- Total transactions: {wallet_stats.get('total_txs', 0)}
- Total volume: {wallet_stats.get('total_volume_wei', 0) / 10**18:.2f} AVAX
- Unique contracts: {wallet_stats.get('unique_contracts', 0)}
- Is whale: {wallet_stats.get('is_whale', 0)}
- Is bot: {wallet_stats.get('is_bot', 0)}
- Is DEX user: {wallet_stats.get('is_dex_user', 0)}

Provide a concise 2-3 sentence analysis of this wallet's behavior pattern."""

        return self.query(prompt)

if __name__ == "__main__":
    # Test Ollama connection
    client = OllamaClient()
    print("Testing Ollama connection...")

    response = client.query("Say 'Hello from Avalytics' in one sentence.")
    print(f"Response: {response}")
