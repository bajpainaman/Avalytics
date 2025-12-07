#!/usr/bin/env python3
"""
X (Twitter) Integration for Avalytics
Generate and post data-driven content to X
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv()


class XClient:
    """X/Twitter client for posting analytics content"""
    
    def __init__(self, db_path: str = "./data/avalytics.db"):
        self.db_path = db_path
        
        # OpenAI for content generation
        api_key = os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai = OpenAI(api_key=api_key)
        else:
            self.openai = None
        
        # X API credentials
        self.x_api_key = os.getenv("X_API_KEY")
        self.x_api_secret = os.getenv("X_API_SECRET")
        self.x_access_token = os.getenv("X_ACCESS_TOKEN")
        self.x_access_secret = os.getenv("X_ACCESS_SECRET")
        self.x_bearer_token = os.getenv("X_BEARER_TOKEN")
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_platform_stats(self) -> Dict:
        """Get current platform statistics for content"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
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
        blocks = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_wallets": stats['total_wallets'] or 0,
            "total_transactions": int(stats['total_txs'] or 0),
            "total_blocks": blocks,
            "total_volume_avax": (stats['total_volume'] or 0) / 1e18,
            "whale_count": int(stats['whale_count'] or 0),
            "dex_users": int(stats['dex_user_count'] or 0)
        }
    
    def _get_recent_whale_activity(self) -> List[Dict]:
        """Get recent whale transactions"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                t.from_address,
                t.to_address,
                t.value,
                t.timestamp,
                wp.total_volume_wei
            FROM transactions t
            JOIN wallet_profiles wp ON t.from_address = wp.wallet_address
            WHERE wp.is_whale = 1
            ORDER BY t.timestamp DESC
            LIMIT 10
        ''')
        
        whales = []
        for row in cursor.fetchall():
            whales.append({
                "from": row['from_address'],
                "to": row['to_address'],
                "value_avax": int(row['value'] or 0) / 1e18,
                "timestamp": row['timestamp'],
                "wallet_volume": int(row['total_volume_wei'] or 0) / 1e18
            })
        
        conn.close()
        return whales
    
    def _get_top_wallets(self, limit: int = 5) -> List[Dict]:
        """Get top wallets by volume"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT wallet_address, total_txs, total_volume_wei, is_whale
            FROM wallet_profiles
            ORDER BY CAST(total_volume_wei AS REAL) DESC
            LIMIT ?
        ''', (limit,))
        
        wallets = []
        for row in cursor.fetchall():
            wallets.append({
                "address": row['wallet_address'][:10] + "..." + row['wallet_address'][-6:],
                "txs": row['total_txs'],
                "volume_avax": int(row['total_volume_wei'] or 0) / 1e18,
                "is_whale": bool(row['is_whale'])
            })
        
        conn.close()
        return wallets
    
    def generate_post(
        self,
        post_type: str,
        custom_prompt: Optional[str] = None,
        include_data: bool = True
    ) -> Dict[str, Any]:
        """
        Generate an X post using AI and real data
        
        post_type: 'stats', 'whale_alert', 'trends', 'custom'
        """
        if not self.openai:
            raise ValueError("OpenAI API key required for post generation")
        
        # Gather data based on post type
        stats = self._get_platform_stats()
        context_data = f"""
Platform Statistics:
- Total Wallets: {stats['total_wallets']:,}
- Total Transactions: {stats['total_transactions']:,}
- Total Volume: {stats['total_volume_avax']:,.2f} AVAX
- Whale Wallets: {stats['whale_count']}
- DEX Users: {stats['dex_users']}
"""
        
        if post_type == "whale_alert":
            whales = self._get_recent_whale_activity()
            if whales:
                context_data += f"\nRecent Whale Activity:\n"
                for w in whales[:3]:
                    context_data += f"- {w['value_avax']:.2f} AVAX moved\n"
        
        if post_type == "trends":
            from analytics.pattern_analyzer import PatternAnalyzer
            analyzer = PatternAnalyzer(self.db_path)
            trends = analyzer.get_trends(days=7)
            context_data += f"\nTrends ({trends['comparison']}):\n"
            for t in trends['trends']:
                context_data += f"- {t['metric']}: {t['change_percent']:+.1f}%\n"
        
        # Build prompt based on type
        prompts = {
            "stats": "Create an engaging tweet about Avalanche network statistics. Include key metrics. Make it informative yet exciting for crypto enthusiasts.",
            "whale_alert": "Create a whale alert tweet about large movements on Avalanche. Use whale emoji. Create FOMO but stay factual.",
            "trends": "Create a trends analysis tweet about what's happening on Avalanche this week. Highlight notable changes.",
            "custom": custom_prompt or "Create an engaging crypto tweet."
        }
        
        system_prompt = """You are a crypto social media expert. Create engaging X/Twitter posts about blockchain analytics.

Rules:
- Keep under 280 characters for single tweet, or create a thread (separate tweets with ---)
- Use relevant emojis sparingly
- Include real data when provided
- Add relevant hashtags ($AVAX, #Avalanche, etc.)
- Be informative but engaging
- No financial advice
- End with a hook or question to drive engagement"""

        user_prompt = f"""{prompts.get(post_type, prompts['custom'])}

Real Data to Use:
{context_data}

Generate the post now:"""

        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Check if it's a thread
        is_thread = "---" in content
        if is_thread:
            tweets = [t.strip() for t in content.split("---") if t.strip()]
        else:
            tweets = [content.strip()]
        
        return {
            "post_type": post_type,
            "content": content,
            "tweets": tweets,
            "is_thread": is_thread,
            "character_count": len(tweets[0]) if tweets else 0,
            "data_included": include_data,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_tweet_intent_url(self, content: str) -> str:
        """
        Generate a Twitter intent URL that opens Twitter with content pre-filled
        User clicks the link → Twitter opens → They post manually
        """
        import urllib.parse
        
        # Twitter intent URL - opens Twitter compose with text pre-filled
        base_url = "https://twitter.com/intent/tweet"
        encoded_text = urllib.parse.quote(content, safe='')
        
        return f"{base_url}?text={encoded_text}"
    
    def prepare_post(self, content: str) -> Dict[str, Any]:
        """
        Prepare a post with intent URL for manual posting
        """
        # Truncate if too long for single tweet
        if len(content) > 280:
            content = content[:277] + "..."
        
        return {
            "content": content,
            "character_count": len(content),
            "intent_url": self.get_tweet_intent_url(content),
            "ready_to_post": len(content) <= 280,
            "generated_at": datetime.now().isoformat()
        }
    
    def prepare_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """
        Prepare a thread - returns first tweet's intent URL
        User posts first tweet, then manually continues thread
        """
        prepared_tweets = []
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
            prepared_tweets.append({
                "index": i + 1,
                "content": tweet,
                "character_count": len(tweet)
            })
        
        return {
            "is_thread": True,
            "thread_length": len(tweets),
            "tweets": prepared_tweets,
            "first_tweet_url": self.get_tweet_intent_url(tweets[0]) if tweets else None,
            "instructions": "Click the link to post the first tweet, then reply to create your thread.",
            "generated_at": datetime.now().isoformat()
        }
    
    def get_post_templates(self) -> List[Dict]:
        """Get available post templates"""
        return [
            {
                "id": "stats",
                "name": "Weekly Stats",
                "description": "Share network statistics and metrics",
                "icon": "📊"
            },
            {
                "id": "whale_alert",
                "name": "Whale Alert",
                "description": "Highlight large wallet movements",
                "icon": "🐋"
            },
            {
                "id": "trends",
                "name": "Trends Analysis",
                "description": "Week-over-week trend comparison",
                "icon": "📈"
            },
            {
                "id": "custom",
                "name": "Custom Post",
                "description": "Write your own prompt for AI to expand",
                "icon": "✏️"
            }
        ]


if __name__ == "__main__":
    client = XClient()
    
    print("=== Generate Stats Post ===")
    result = client.generate_post("stats")
    print(result['content'])
    print(f"\nCharacters: {result['character_count']}")
