#!/usr/bin/env python3
"""
Pattern Analyzer for Avalytics
Detects behavioral patterns, generates heatmaps, and identifies trends
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict
import json


class PatternAnalyzer:
    """Analyzes wallet behavior patterns from transaction data"""
    
    def __init__(self, db_path: str = "./data/avalytics.db"):
        self.db_path = db_path
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def analyze_patterns(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze behavior patterns across all wallets
        Returns: accumulators, distributors, arbitrageurs, etc.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        patterns = {
            "accumulators": [],
            "distributors": [],
            "high_frequency": [],
            "dormant_reactivated": [],
            "new_whales": []
        }
        
        # Find accumulators (more received than sent)
        cursor.execute('''
            SELECT 
                t.to_address as address,
                COUNT(*) as receive_count,
                SUM(CAST(t.value AS REAL)) as total_received
            FROM transactions t
            WHERE t.timestamp > ? AND t.to_address IS NOT NULL
            GROUP BY t.to_address
            HAVING receive_count > 3
            ORDER BY total_received DESC
            LIMIT 50
        ''', (cutoff_date,))
        
        receivers = {row['address']: {'count': row['receive_count'], 'amount': row['total_received']} 
                    for row in cursor.fetchall()}
        
        # Find what they sent
        cursor.execute('''
            SELECT 
                t.from_address as address,
                COUNT(*) as send_count,
                SUM(CAST(t.value AS REAL)) as total_sent
            FROM transactions t
            WHERE t.timestamp > ? 
            GROUP BY t.from_address
            HAVING send_count > 0
        ''', (cutoff_date,))
        
        senders = {row['address']: {'count': row['send_count'], 'amount': row['total_sent']} 
                  for row in cursor.fetchall()}
        
        # Classify patterns
        for address, recv in receivers.items():
            sent = senders.get(address, {'count': 0, 'amount': 0})
            net = recv['amount'] - sent['amount']
            
            if net > 0 and recv['amount'] > sent['amount'] * 1.5:
                patterns["accumulators"].append({
                    "address": address,
                    "net_flow_wei": net,
                    "net_flow_avax": net / 1e18,
                    "receive_count": recv['count'],
                    "send_count": sent['count'],
                    "pattern": "accumulating"
                })
        
        # Find distributors (more sent than received)
        for address, sent in senders.items():
            recv = receivers.get(address, {'count': 0, 'amount': 0})
            net = sent['amount'] - recv['amount']
            
            if net > 0 and sent['amount'] > recv['amount'] * 1.5:
                patterns["distributors"].append({
                    "address": address,
                    "net_flow_wei": net,
                    "net_flow_avax": net / 1e18,
                    "send_count": sent['count'],
                    "receive_count": recv['count'],
                    "pattern": "distributing"
                })
        
        # High frequency traders (many txs in short period)
        cursor.execute('''
            SELECT 
                from_address as address,
                COUNT(*) as tx_count,
                SUM(CAST(value AS REAL)) as volume
            FROM transactions
            WHERE timestamp > ?
            GROUP BY from_address
            HAVING tx_count >= 10
            ORDER BY tx_count DESC
            LIMIT 20
        ''', (cutoff_date,))
        
        for row in cursor.fetchall():
            patterns["high_frequency"].append({
                "address": row['address'],
                "tx_count": row['tx_count'],
                "volume_avax": (row['volume'] or 0) / 1e18,
                "pattern": "high_frequency"
            })
        
        # New whales (recently crossed threshold)
        cursor.execute('''
            SELECT wallet_address, total_volume_wei, total_txs, first_seen
            FROM wallet_profiles
            WHERE is_whale = 1 
            AND first_seen > ?
            ORDER BY CAST(total_volume_wei AS REAL) DESC
            LIMIT 10
        ''', (cutoff_date,))
        
        for row in cursor.fetchall():
            patterns["new_whales"].append({
                "address": row['wallet_address'],
                "volume_avax": int(row['total_volume_wei'] or 0) / 1e18,
                "tx_count": row['total_txs'],
                "first_seen": row['first_seen'],
                "pattern": "new_whale"
            })
        
        conn.close()
        
        # Sort and limit
        patterns["accumulators"] = sorted(
            patterns["accumulators"], 
            key=lambda x: x['net_flow_avax'], 
            reverse=True
        )[:20]
        
        patterns["distributors"] = sorted(
            patterns["distributors"], 
            key=lambda x: x['net_flow_avax'], 
            reverse=True
        )[:20]
        
        return {
            "period_days": days,
            "analyzed_at": datetime.now().isoformat(),
            "patterns": patterns,
            "summary": {
                "accumulators_count": len(patterns["accumulators"]),
                "distributors_count": len(patterns["distributors"]),
                "high_frequency_count": len(patterns["high_frequency"]),
                "new_whales_count": len(patterns["new_whales"])
            }
        }
    
    def get_activity_heatmap(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate activity heatmap data (hour x day_of_week)
        Shows when users are most active
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get all transactions with timestamps
        cursor.execute('''
            SELECT timestamp
            FROM transactions
            WHERE timestamp > ?
        ''', (cutoff_date,))
        
        # Initialize heatmap grid (7 days x 24 hours)
        heatmap = [[0 for _ in range(24)] for _ in range(7)]
        total_txs = 0
        
        for row in cursor.fetchall():
            try:
                ts = row['timestamp']
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00').split('+')[0])
                else:
                    dt = datetime.fromtimestamp(ts)
                
                day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
                hour = dt.hour
                
                heatmap[day_of_week][hour] += 1
                total_txs += 1
            except:
                continue
        
        conn.close()
        
        # Find peak times
        max_activity = 0
        peak_day = 0
        peak_hour = 0
        
        for day in range(7):
            for hour in range(24):
                if heatmap[day][hour] > max_activity:
                    max_activity = heatmap[day][hour]
                    peak_day = day
                    peak_hour = hour
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Calculate daily totals
        daily_totals = [sum(heatmap[day]) for day in range(7)]
        busiest_day = day_names[daily_totals.index(max(daily_totals))]
        
        # Calculate hourly totals (across all days)
        hourly_totals = [sum(heatmap[day][hour] for day in range(7)) for hour in range(24)]
        busiest_hour = hourly_totals.index(max(hourly_totals))
        
        return {
            "period_days": days,
            "total_transactions": total_txs,
            "heatmap": {
                "data": heatmap,
                "rows": day_names,
                "columns": [f"{h:02d}:00" for h in range(24)]
            },
            "insights": {
                "peak_day": day_names[peak_day],
                "peak_hour": f"{peak_hour:02d}:00",
                "peak_activity": max_activity,
                "busiest_day": busiest_day,
                "busiest_hour": f"{busiest_hour:02d}:00",
                "best_posting_times": self._get_best_posting_times(heatmap, day_names)
            }
        }
    
    def _get_best_posting_times(self, heatmap: List[List[int]], day_names: List[str]) -> List[Dict]:
        """Find top 5 best times to post based on activity"""
        times = []
        for day in range(7):
            for hour in range(24):
                times.append({
                    "day": day_names[day],
                    "hour": f"{hour:02d}:00",
                    "activity": heatmap[day][hour]
                })
        
        # Sort by activity and return top 5
        times.sort(key=lambda x: x['activity'], reverse=True)
        return times[:5]
    
    def get_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Detect trending behaviors and changes
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        current_cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        previous_cutoff = (datetime.now() - timedelta(days=days*2)).isoformat()
        
        trends = []
        
        # Transaction volume trend
        cursor.execute('''
            SELECT COUNT(*) as count, SUM(CAST(value AS REAL)) as volume
            FROM transactions WHERE timestamp > ?
        ''', (current_cutoff,))
        current = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) as count, SUM(CAST(value AS REAL)) as volume
            FROM transactions WHERE timestamp > ? AND timestamp <= ?
        ''', (previous_cutoff, current_cutoff))
        previous = cursor.fetchone()
        
        if previous['count'] and previous['count'] > 0:
            tx_change = ((current['count'] - previous['count']) / previous['count']) * 100
            vol_change = (((current['volume'] or 0) - (previous['volume'] or 0)) / max(previous['volume'] or 1, 1)) * 100
            
            trends.append({
                "metric": "Transaction Count",
                "current": current['count'],
                "previous": previous['count'],
                "change_percent": round(tx_change, 1),
                "direction": "up" if tx_change > 0 else "down"
            })
            
            trends.append({
                "metric": "Volume (AVAX)",
                "current": round((current['volume'] or 0) / 1e18, 2),
                "previous": round((previous['volume'] or 0) / 1e18, 2),
                "change_percent": round(vol_change, 1),
                "direction": "up" if vol_change > 0 else "down"
            })
        
        # New wallet trend
        cursor.execute('''
            SELECT COUNT(*) as count FROM wallet_profiles WHERE first_seen > ?
        ''', (current_cutoff,))
        new_current = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM wallet_profiles 
            WHERE first_seen > ? AND first_seen <= ?
        ''', (previous_cutoff, current_cutoff))
        new_previous = cursor.fetchone()['count']
        
        if new_previous > 0:
            new_wallet_change = ((new_current - new_previous) / new_previous) * 100
            trends.append({
                "metric": "New Wallets",
                "current": new_current,
                "previous": new_previous,
                "change_percent": round(new_wallet_change, 1),
                "direction": "up" if new_wallet_change > 0 else "down"
            })
        
        # Whale activity
        cursor.execute('''
            SELECT COUNT(DISTINCT from_address) as active_whales
            FROM transactions t
            JOIN wallet_profiles wp ON t.from_address = wp.wallet_address
            WHERE t.timestamp > ? AND wp.is_whale = 1
        ''', (current_cutoff,))
        active_whales = cursor.fetchone()['active_whales']
        
        # Average transaction value trend
        cursor.execute('''
            SELECT AVG(CAST(value AS REAL)) as avg_val FROM transactions WHERE timestamp > ?
        ''', (current_cutoff,))
        current_avg = cursor.fetchone()['avg_val'] or 0
        
        cursor.execute('''
            SELECT AVG(CAST(value AS REAL)) as avg_val 
            FROM transactions WHERE timestamp > ? AND timestamp <= ?
        ''', (previous_cutoff, current_cutoff))
        previous_avg = cursor.fetchone()['avg_val'] or 0
        
        if previous_avg > 0:
            avg_change = ((current_avg - previous_avg) / previous_avg) * 100
            trends.append({
                "metric": "Avg Transaction Size (AVAX)",
                "current": round(current_avg / 1e18, 4),
                "previous": round(previous_avg / 1e18, 4),
                "change_percent": round(avg_change, 1),
                "direction": "up" if avg_change > 0 else "down"
            })
        
        conn.close()
        
        # Generate insights
        insights = []
        for trend in trends:
            if abs(trend['change_percent']) > 20:
                emoji = "📈" if trend['direction'] == 'up' else "📉"
                insights.append(
                    f"{emoji} {trend['metric']} {trend['direction']} {abs(trend['change_percent']):.0f}% this period"
                )
        
        return {
            "period_days": days,
            "comparison": f"Last {days} days vs previous {days} days",
            "trends": trends,
            "insights": insights,
            "summary": {
                "active_whales": active_whales,
                "total_trends_up": len([t for t in trends if t['direction'] == 'up']),
                "total_trends_down": len([t for t in trends if t['direction'] == 'down'])
            }
        }


if __name__ == "__main__":
    analyzer = PatternAnalyzer()
    
    print("=== Patterns ===")
    patterns = analyzer.analyze_patterns(days=30)
    print(f"Accumulators: {patterns['summary']['accumulators_count']}")
    print(f"Distributors: {patterns['summary']['distributors_count']}")
    
    print("\n=== Heatmap ===")
    heatmap = analyzer.get_activity_heatmap(days=30)
    print(f"Peak time: {heatmap['insights']['peak_day']} at {heatmap['insights']['peak_hour']}")
    
    print("\n=== Trends ===")
    trends = analyzer.get_trends(days=7)
    for insight in trends['insights']:
        print(f"  {insight}")
