#!/usr/bin/env python3
"""
Perplexity AI Integration for Avalytics
Real-time web search for wallet intelligence
"""
import os
import requests
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


class PerplexityClient:
    """Perplexity AI client with real-time web search"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"

        if not self.api_key:
            raise ValueError("Perplexity API key required. Set PERPLEXITY_API_KEY env var")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search(self, query: str, model: str = "llama-3.1-sonar-large-128k-online") -> Dict:
        """Search with Perplexity's web-connected models"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a blockchain intelligence analyst. Search the web for accurate, up-to-date information about cryptocurrency wallets and entities."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        }

        response = requests.post(url, headers=self.headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return {
            "answer": result["choices"][0]["message"]["content"],
            "citations": result.get("citations", [])
        }

    def research_wallet_entity(self, wallet_address: str) -> Dict:
        """Search for wallet entity information"""

        query = f"""Search for information about this Avalanche C-Chain wallet address: {wallet_address}

Find:
1. Is this wallet associated with any known exchange (Binance, Coinbase, etc)?
2. Does it belong to any DeFi protocol or project?
3. Any blockchain explorer tags or labels?
4. Notable transactions or activity patterns?
5. Public mentions on Twitter, forums, or news?

Provide sources for all claims."""

        try:
            result = self.search(query)
            return {
                "wallet": wallet_address,
                "entity_info": result["answer"],
                "sources": result["citations"],
                "identified": True
            }
        except Exception as e:
            return {
                "wallet": wallet_address,
                "entity_info": f"Error: {e}",
                "sources": [],
                "identified": False
            }

    def find_similar_wallets(self, behavior_pattern: str) -> Dict:
        """Find similar wallet patterns"""

        query = f"""Search for Avalanche wallets with similar behavior:

Pattern: {behavior_pattern}

Find examples of:
1. Wallets with similar transaction patterns
2. Known entities with this behavior
3. Any documented cases or analysis
4. Risk indicators associated with this pattern

Include sources."""

        return self.search(query)

    def check_scam_indicators(self, wallet_address: str) -> Dict:
        """Check if wallet is flagged as scam"""

        query = f"""Search for scam/fraud reports about Avalanche wallet {wallet_address}

Check:
1. Scam databases and blacklists
2. Community reports on Reddit, Twitter
3. Blockchain explorer warnings
4. Similar addresses involved in scams
5. Any known exploits or hacks

Be specific about sources."""

        try:
            result = self.search(query)

            # Determine if scam based on response
            is_flagged = any(word in result["answer"].lower() for word in ["scam", "fraud", "hack", "exploit", "warning"])

            return {
                "wallet": wallet_address,
                "scam_check": result["answer"],
                "sources": result["citations"],
                "is_flagged": is_flagged,
                "risk_level": "HIGH" if is_flagged else "LOW"
            }
        except Exception as e:
            return {
                "wallet": wallet_address,
                "scam_check": f"Error: {e}",
                "sources": [],
                "is_flagged": False,
                "risk_level": "UNKNOWN"
            }

    def research_batch(self, wallets: List[str], max_wallets: int = 10) -> List[Dict]:
        """Research multiple wallets (rate limited)"""

        results = []
        print(f"[*] Researching {min(len(wallets), max_wallets)} wallets with Perplexity...")

        for i, wallet in enumerate(wallets[:max_wallets]):
            try:
                entity_info = self.research_wallet_entity(wallet)
                scam_info = self.check_scam_indicators(wallet)

                results.append({
                    "wallet": wallet,
                    "entity_research": entity_info,
                    "scam_research": scam_info,
                    "researched": True
                })

                print(f"    Researched {i + 1}/{min(len(wallets), max_wallets)} wallets...")

            except Exception as e:
                print(f"[-] Error researching {wallet}: {e}")
                results.append({
                    "wallet": wallet,
                    "researched": False,
                    "error": str(e)
                })

        print(f"[+] Completed research on {len(results)} wallets")
        return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python perplexity_client.py <wallet_address>")
        sys.exit(1)

    wallet = sys.argv[1]

    client = PerplexityClient()

    print(f"\n[*] Researching wallet {wallet} with Perplexity AI...\n")

    # Entity research
    entity = client.research_wallet_entity(wallet)
    print("=" * 80)
    print("ENTITY RESEARCH")
    print("=" * 80)
    print(entity["entity_info"])
    if entity["sources"]:
        print("\nSources:")
        for src in entity["sources"]:
            print(f"  - {src}")

    # Scam check
    scam = client.check_scam_indicators(wallet)
    print("\n" + "=" * 80)
    print("SCAM/RISK CHECK")
    print("=" * 80)
    print(scam["scam_check"])
    print(f"\nRisk Level: {scam['risk_level']}")
