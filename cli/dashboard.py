#!/usr/bin/env python3
"""
Avalytics Analytics Dashboard
Interactive terminal with structured AI insights
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.prompt import Prompt
from rich import box
from ai.structured_analyzer import StructuredAnalyzer
import json


class Dashboard:
    def __init__(self, db_path: str = "./data/avalytics.db"):
        self.db_path = db_path
        self.console = Console()
        self.analyzer = StructuredAnalyzer(db_path)

    def show_overview(self):
        """Show platform overview"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get overall stats
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
        total_wallets, total_txs, total_vol, whales, bots, dex_users = stats

        cursor.execute('SELECT COUNT(DISTINCT block_number) FROM transactions')
        total_blocks = cursor.fetchone()[0]

        conn.close()

        # Create overview table
        table = Table(title="Avalytics Platform Overview", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Wallets Tracked", f"{total_wallets:,}")
        table.add_row("Total Transactions", f"{int(total_txs):,}")
        table.add_row("Total Blocks Indexed", f"{total_blocks:,}")
        table.add_row("Total Volume", f"{total_vol/10**18:,.2f} AVAX")
        table.add_row("Whale Wallets", f"{int(whales):,} ({whales/total_wallets*100:.1f}%)")
        table.add_row("Bot Wallets", f"{int(bots):,} ({bots/total_wallets*100:.1f}%)")
        table.add_row("DEX Users", f"{int(dex_users):,} ({dex_users/total_wallets*100:.1f}%)")

        self.console.print(table)

    def show_top_wallets(self, limit: int = 10):
        """Show top wallets by volume"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT wallet_address, total_txs, total_volume_wei, unique_contracts,
                   is_whale, is_bot, is_dex_user
            FROM wallet_profiles
            ORDER BY CAST(total_volume_wei AS REAL) DESC
            LIMIT ?
        ''', (limit,))

        wallets = cursor.fetchall()
        conn.close()

        table = Table(title=f"Top {limit} Wallets by Volume", box=box.ROUNDED)
        table.add_column("Wallet", style="cyan")
        table.add_column("Txs", justify="right")
        table.add_column("Volume (AVAX)", justify="right", style="green")
        table.add_column("Contracts", justify="right")
        table.add_column("Flags", style="yellow")

        for wallet, txs, vol, contracts, whale, bot, dex in wallets:
            flags = []
            if whale: flags.append("")
            if bot: flags.append("")
            if dex: flags.append("")

            table.add_row(
                wallet[:10] + "..." + wallet[-8:],
                str(txs),
                f"{int(vol)/10**18:,.2f}",
                str(contracts) if contracts else "0",
                " ".join(flags)
            )

        self.console.print(table)

    def analyze_wallet_deep(self, wallet_address: str):
        """Deep analysis of a wallet with structured AI"""
        self.console.print(f"\n[cyan]Analyzing wallet: {wallet_address}[/cyan]\n")

        try:
            # Get structured profile
            with self.console.status("[bold green]Running AI analysis..."):
                profile = self.analyzer.analyze_wallet_structured(wallet_address)

            # Display results
            panel_content = f"""
[bold cyan]Wallet Type:[/bold cyan] {profile.wallet_type}
[bold yellow]Risk Level:[/bold yellow] {profile.risk_level}
[bold green]Activity Pattern:[/bold green] {profile.activity_pattern}
[bold blue]Primary Use Case:[/bold blue] {profile.primary_use_case}
[bold magenta]Sophistication Score:[/bold magenta] {profile.sophistication_score}/10

[bold]Key Insights:[/bold]
{chr(10).join(f'  • {insight}' for insight in profile.key_insights)}

[bold]Recommended Approach:[/bold]
  {profile.recommended_approach}
"""
            self.console.print(Panel(panel_content, title="AI-Powered Wallet Analysis", border_style="green"))

            # Transaction pattern analysis
            if Prompt.ask("\nAnalyze transaction patterns?", choices=["y", "n"], default="n") == "y":
                with self.console.status("[bold green]Analyzing transaction patterns..."):
                    pattern = self.analyzer.detect_transaction_pattern(wallet_address)

                pattern_content = f"""
[bold cyan]Pattern Type:[/bold cyan] {pattern.pattern_type}
[bold yellow]Confidence:[/bold yellow] {pattern.confidence:.2%}

[bold]Explanation:[/bold]
  {pattern.explanation}

[bold]Implications:[/bold]
{chr(10).join(f'  • {impl}' for impl in pattern.implications)}
"""
                self.console.print(Panel(pattern_content, title="Transaction Pattern Analysis", border_style="yellow"))

        except Exception as e:
            self.console.print(f"[red]Error analyzing wallet: {e}[/red]")

    def analyze_cohort_deep(self, cohort_id: int):
        """Deep analysis of a cohort with structured AI"""
        self.console.print(f"\n[cyan]Analyzing cohort {cohort_id}...[/cyan]\n")

        try:
            with self.console.status("[bold green]Running cohort analysis..."):
                analysis = self.analyzer.analyze_cohort_structured(cohort_id)

            content = f"""
[bold cyan]Cohort Name:[/bold cyan] {analysis.cohort_name}

[bold]Characteristics:[/bold]
{chr(10).join(f'  • {char}' for char in analysis.cohort_characteristics)}

[bold green]Typical Behavior:[/bold green]
  {analysis.typical_behavior}

[bold yellow]Engagement Strategy:[/bold yellow]
  {analysis.engagement_strategy}

[bold blue]Value Proposition:[/bold blue]
  {analysis.value_proposition}
"""
            self.console.print(Panel(content, title=f"Cohort {cohort_id} Analysis", border_style="blue"))

        except Exception as e:
            self.console.print(f"[red]Error analyzing cohort: {e}[/red]")

    def show_cohorts(self):
        """Show all cohorts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                wt.tag,
                COUNT(*) as wallet_count,
                AVG(CAST(wp.total_volume_wei AS REAL)) as avg_volume,
                AVG(wp.total_txs) as avg_txs
            FROM wallet_tags wt
            JOIN wallet_profiles wp ON wt.wallet_address = wp.wallet_address
            WHERE wt.tag LIKE 'cluster_%'
            GROUP BY wt.tag
            ORDER BY wallet_count DESC
        ''')

        cohorts = cursor.fetchall()
        conn.close()

        table = Table(title="Wallet Cohorts", box=box.ROUNDED)
        table.add_column("Cohort", style="cyan")
        table.add_column("Wallets", justify="right")
        table.add_column("Avg Volume (AVAX)", justify="right", style="green")
        table.add_column("Avg Txs", justify="right")

        for tag, count, avg_vol, avg_txs in cohorts:
            cohort_id = tag.replace('cluster_', '')
            table.add_row(
                f"Cohort {cohort_id}",
                f"{count:,}",
                f"{avg_vol/10**18:,.2f}",
                f"{avg_txs:.1f}"
            )

        self.console.print(table)

    def interactive_mode(self):
        """Interactive dashboard mode"""
        self.console.clear()
        self.console.print(Panel.fit(
            "[bold cyan]Avalytics Analytics Dashboard[/bold cyan]\n"
            "Crypto Intelligence Platform for Avalanche",
            border_style="blue"
        ))

        while True:
            self.console.print("\n[bold]Commands:[/bold]")
            self.console.print("  1. overview     - Platform overview")
            self.console.print("  2. top          - Top wallets by volume")
            self.console.print("  3. wallet       - Deep wallet analysis")
            self.console.print("  4. cohorts      - View all cohorts")
            self.console.print("  5. cohort       - Deep cohort analysis")
            self.console.print("  6. quit         - Exit\n")

            cmd = Prompt.ask("Select command", choices=["1", "2", "3", "4", "5", "6"])

            if cmd == "1":
                self.show_overview()
            elif cmd == "2":
                limit = int(Prompt.ask("How many wallets?", default="10"))
                self.show_top_wallets(limit)
            elif cmd == "3":
                wallet = Prompt.ask("Enter wallet address")
                self.analyze_wallet_deep(wallet)
            elif cmd == "4":
                self.show_cohorts()
            elif cmd == "5":
                cohort = int(Prompt.ask("Enter cohort ID"))
                self.analyze_cohort_deep(cohort)
            elif cmd == "6":
                self.console.print("[yellow]Goodbye![/yellow]")
                break


if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.interactive_mode()
