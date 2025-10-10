#!/usr/bin/env python3
"""
Grok AI Integration for Avalytics
Uses Grok API for enhanced wallet intelligence with web search
"""
import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
import json

load_dotenv()


class GrokClient:
    """Grok AI client with web search capabilities"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.base_url = "https://api.x.ai/v1"

        if not self.api_key:
            raise ValueError("Grok API key required. Set GROK_API_KEY env var")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, messages: List[Dict], model: str = "grok-beta", stream: bool = False) -> str:
        """Send chat completion request to Grok"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "messages": messages,
            "model": model,
            "stream": stream,
            "temperature": 0.7
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def research_wallet(self, wallet_address: str, wallet_stats: Dict) -> Dict:
        """Use Grok to research a wallet with web search"""

        prompt = f"""Research this Avalanche wallet address and provide intelligence:

Wallet: {wallet_address}
On-chain Stats:
- Total transactions: {wallet_stats.get('total_txs', 0)}
- Total volume: {wallet_stats.get('total_volume_wei', 0) / 10**18:.2f} AVAX
- Unique contracts: {wallet_stats.get('unique_contracts', 0)}
- Classification: {"WHALE" if wallet_stats.get('is_whale') else "Regular"}

Tasks:
1. Search for any public information about this wallet address
2. Check if it's associated with any known entities (exchanges, projects, funds)
3. Look for any social media mentions or blockchain explorer tags
4. Identify any notable transactions or patterns
5. Assess risk factors and legitimacy

Provide a structured analysis with sources."""

        messages = [
            {"role": "system", "content": "You are a blockchain intelligence analyst with access to web search. Research wallet addresses and provide detailed intelligence reports with sources."},
            {"role": "user", "content": prompt}
        ]

        try:
            analysis = self.chat(messages)

            return {
                "wallet_address": wallet_address,
                "grok_analysis": analysis,
                "research_completed": True
            }
        except Exception as e:
            return {
                "wallet_address": wallet_address,
                "grok_analysis": f"Error: {e}",
                "research_completed": False
            }

    def enrich_wallet_batch(self, wallets: List[Dict]) -> List[Dict]:
        """Enrich multiple wallets with Grok intelligence in parallel"""
        enriched_wallets = []

        print(f"[*] Enriching {len(wallets)} wallets with Grok AI...")

        for i, wallet in enumerate(wallets):
            try:
                research = self.research_wallet(
                    wallet.get("address", ""),
                    {
                        "total_txs": wallet.get("tx_count", 0),
                        "total_volume_wei": int(wallet.get("volume_avax", 0) * 10**18),
                        "unique_contracts": wallet.get("contracts", 0),
                        "is_whale": wallet.get("wallet_type") == "WHALE"
                    }
                )

                wallet["grok_intelligence"] = research["grok_analysis"]
                enriched_wallets.append(wallet)

                if (i + 1) % 5 == 0:
                    print(f"    Enriched {i + 1}/{len(wallets)} wallets...")

            except Exception as e:
                print(f"[-] Error enriching {wallet.get('address', 'unknown')}: {e}")
                wallet["grok_intelligence"] = ""
                enriched_wallets.append(wallet)

        print(f"[+] Enriched {len(enriched_wallets)} wallets with Grok")
        return enriched_wallets

    def search_similar_wallets(self, wallet_pattern: str) -> str:
        """Use Grok to find similar wallet patterns on the web"""

        messages = [
            {"role": "system", "content": "You are a blockchain analyst. Search the web for information about wallet patterns and similar behaviors."},
            {"role": "user", "content": f"Search for wallets or entities with similar behavior to: {wallet_pattern}. Include any known addresses, projects, or patterns."}
        ]

        return self.chat(messages)

    def identify_entity(self, wallet_address: str) -> Optional[Dict]:
        """Try to identify if wallet belongs to known entity"""

        messages = [
            {"role": "system", "content": "You are a blockchain intelligence analyst. Identify if a wallet address belongs to any known entity, exchange, project, or individual."},
            {"role": "user", "content": f"Search for information about Avalanche wallet {wallet_address}. Is it associated with any known entity? Provide name, type (exchange/project/fund/individual), and confidence level."}
        ]

        try:
            response = self.chat(messages)

            # Parse response for structured data
            return {
                "wallet": wallet_address,
                "identification": response,
                "has_identity": "unknown" not in response.lower()
            }
        except Exception as e:
            return None

    def analyze_threat_level(self, wallet_address: str, transaction_data: List[Dict]) -> Dict:
        """Use Grok to analyze wallet for suspicious activity"""

        tx_summary = "\n".join([
            f"- {tx.get('timestamp', 'N/A')}: {tx.get('type', 'transfer')} of {tx.get('value', 0)} AVAX to {tx.get('to', 'N/A')}"
            for tx in transaction_data[:10]
        ])

        messages = [
            {"role": "system", "content": "You are a blockchain security analyst. Analyze wallets for suspicious activity, scam indicators, and security risks."},
            {"role": "user", "content": f"""Analyze this wallet for threat indicators:

Wallet: {wallet_address}

Recent transactions:
{tx_summary}

Assess:
1. Is this wallet involved in any known scams or exploits?
2. Are there signs of wash trading or market manipulation?
3. Any patterns suggesting bot activity or automated trading?
4. Overall threat level (LOW/MEDIUM/HIGH/CRITICAL)
5. Recommended actions

Provide structured assessment."""}
        ]

        try:
            analysis = self.chat(messages)

            # Extract threat level
            threat_level = "LOW"
            if "HIGH" in analysis or "CRITICAL" in analysis:
                threat_level = "HIGH"
            elif "MEDIUM" in analysis:
                threat_level = "MEDIUM"

            return {
                "wallet": wallet_address,
                "threat_level": threat_level,
                "threat_analysis": analysis,
                "analyzed": True
            }
        except Exception as e:
            return {
                "wallet": wallet_address,
                "threat_level": "UNKNOWN",
                "threat_analysis": f"Error: {e}",
                "analyzed": False
            }

    def generate_outreach_strategy(self, wallet_profile: Dict) -> str:
        """Generate personalized outreach strategy using Grok"""

        messages = [
            {"role": "system", "content": "You are a crypto business development expert. Create personalized outreach strategies for high-value wallet holders."},
            {"role": "user", "content": f"""Create an outreach strategy for this wallet:

Profile:
- Type: {wallet_profile.get('wallet_type', 'UNKNOWN')}
- Volume: {wallet_profile.get('volume_avax', 0):.2f} AVAX
- Activity: {wallet_profile.get('tx_count', 0)} transactions
- Risk Level: {wallet_profile.get('risk_level', 'UNKNOWN')}

Generate:
1. Recommended approach (cold outreach, partnership, etc)
2. Key value propositions
3. Communication channels to try
4. Talking points
5. Red flags to watch for

Keep it concise and actionable."""}
        ]

        return self.chat(messages)


if __name__ == "__main__":
    # Test Grok integration
    import sys

    if len(sys.argv) < 2:
        print("Usage: python grok_client.py <wallet_address>")
        sys.exit(1)

    wallet = sys.argv[1]

    client = GrokClient()

    print(f"\n[*] Researching wallet {wallet} with Grok AI...\n")

    result = client.research_wallet(wallet, {
        "total_txs": 100,
        "total_volume_wei": 500 * 10**18,
        "unique_contracts": 15,
        "is_whale": True
    })

    print("=" * 80)
    print("GROK INTELLIGENCE REPORT")
    print("=" * 80)
    print(result["grok_analysis"])
    print("=" * 80)
