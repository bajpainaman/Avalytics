#!/usr/bin/env python3
"""
Cohort Detector
Detects and tags wallet cohorts using ML clustering
"""
import sqlite3
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from indexer import config

class CohortDetector:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    def detect_cohorts(self, n_clusters: int = 5):
        """Detect wallet cohorts using K-means clustering"""
        print(f"\n[*] Detecting {n_clusters} cohorts...")

        conn = sqlite3.connect(self.db_path)

        # Load wallet profiles
        df = pd.read_sql_query('''
            SELECT
                wallet_address,
                total_txs,
                total_volume_wei,
                unique_contracts,
                is_whale,
                is_bot,
                is_dex_user
            FROM wallet_profiles
            WHERE total_txs > 0
        ''', conn)

        if len(df) < n_clusters:
            print(f"⚠️  Not enough wallets ({len(df)}) for {n_clusters} clusters")
            conn.close()
            return

        # Prepare features
        features = df[['total_txs', 'total_volume_wei', 'unique_contracts']].fillna(0)

        # Normalize
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(features_scaled)

        # Assign cohort tags
        cohort_names = ['high_volume', 'frequent_trader', 'contract_explorer', 'casual_user', 'whale']

        cursor = conn.cursor()

        for idx, row in df.iterrows():
            cohort_tag = cohort_names[row['cluster'] % len(cohort_names)]

            cursor.execute('''
                INSERT OR IGNORE INTO wallet_tags (wallet_address, tag, confidence)
                VALUES (?, ?, ?)
            ''', (row['wallet_address'], cohort_tag, 0.8))

        conn.commit()
        conn.close()

        print(f"[+] Tagged {len(df)} wallets into cohorts")
        print(f"\nCohort distribution:")
        print(df['cluster'].value_counts())

if __name__ == "__main__":
    detector = CohortDetector()
    detector.detect_cohorts()
