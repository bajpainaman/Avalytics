#!/usr/bin/env python3
"""
Avalytics Terminal
Interactive CLI for querying blockchain data with AI
"""
import sqlite3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from indexer import config
from ai.ollama_client import OllamaClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

class AvalyticsTerminal:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self.ai = OllamaClient()
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Load schema context
        schema_path = Path(__file__).parent.parent / "ai" / "schema_context.txt"
        with open(schema_path, 'r') as f:
            self.schema_context = f.read()

    def show_stats(self):
        """Show overall statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM transactions")
        tx_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM wallet_profiles")
        wallet_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM wallet_profiles WHERE is_whale = 1")
        whale_count = cursor.fetchone()[0]

        console.print(Panel.fit(
            f"[bold cyan]Avalytics Stats[/bold cyan]\n\n"
            f"Transactions: [yellow]{tx_count:,}[/yellow]\n"
            f"Wallets: [yellow]{wallet_count:,}[/yellow]\n"
            f"Whales: [yellow]{whale_count:,}[/yellow]",
            border_style="cyan"
        ))

    def show_whales(self, limit: int = 10):
        """Show top whale wallets"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT wallet_address, total_txs, total_volume_wei, unique_contracts
            FROM wallet_profiles
            WHERE is_whale = 1
            ORDER BY total_volume_wei DESC
            LIMIT {limit}
        ''')

        table = Table(title=f"Top {limit} Whale Wallets", box=box.ROUNDED)
        table.add_column("Wallet", style="cyan")
        table.add_column("Transactions", style="yellow")
        table.add_column("Volume (AVAX)", style="green")
        table.add_column("Contracts", style="magenta")

        for row in cursor.fetchall():
            table.add_row(
                row[0][:10] + "..." + row[0][-8:],
                str(row[1]),
                f"{row[2] / 10**18:.2f}",
                str(row[3])
            )

        console.print(table)

    def analyze_wallet(self, address: str):
        """Analyze a specific wallet with AI"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM wallet_profiles WHERE wallet_address = ?
        ''', (address,))

        row = cursor.fetchone()

        if not row:
            console.print(f"[red]Wallet {address} not found[/red]")
            return

        # Convert row to dict
        stats = dict(row)

        console.print(Panel.fit(
            f"[bold cyan]Wallet Analysis: {address[:10]}...{address[-8:]}[/bold cyan]\n\n"
            f"First seen: [yellow]{stats['first_seen']}[/yellow]\n"
            f"Last active: [yellow]{stats['last_active']}[/yellow]\n"
            f"Total txs: [yellow]{stats['total_txs']}[/yellow]\n"
            f"Volume: [green]{stats['total_volume_wei'] / 10**18:.2f} AVAX[/green]\n"
            f"Whale: [yellow]{'Yes' if stats['is_whale'] else 'No'}[/yellow]\n"
            f"Bot: [yellow]{'Yes' if stats['is_bot'] else 'No'}[/yellow]\n"
            f"DEX User: [yellow]{'Yes' if stats['is_dex_user'] else 'No'}[/yellow]",
            border_style="cyan"
        ))

        console.print("\n[bold]AI Analysis:[/bold]")
        with console.status("[bold green]Asking AI..."):
            analysis = self.ai.explain_wallet_behavior(stats)
        console.print(f"[italic]{analysis}[/italic]\n")

    def nl_query(self, query: str):
        """Execute natural language query"""
        console.print(f"\n[bold]Query:[/bold] {query}")

        with console.status("[bold green]Generating SQL..."):
            sql = self.ai.natural_language_to_sql(query, self.schema_context)

        console.print(f"[dim]SQL: {sql}[/dim]\n")

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()

            if not rows:
                console.print("[yellow]No results found[/yellow]")
                return

            # Display results
            table = Table(title="Query Results", box=box.ROUNDED)

            # Add columns
            for col in rows[0].keys():
                table.add_column(col, style="cyan")

            # Add rows (limit to 20)
            for row in rows[:20]:
                table.add_row(*[str(val) for val in row])

            console.print(table)
            console.print(f"\n[dim]Showing {min(len(rows), 20)} of {len(rows)} results[/dim]")

        except Exception as e:
            console.print(f"[red]Error executing query: {e}[/red]")

    def run(self):
        """Run interactive terminal"""
        console.print(Panel.fit(
            "[bold cyan]🚀 Avalytics Terminal[/bold cyan]\n"
            "Crypto Palantir for Avalanche\n\n"
            "Commands:\n"
            "  stats - Show overall statistics\n"
            "  whales - Show top whales\n"
            "  wallet <address> - Analyze wallet\n"
            "  query <natural language> - AI-powered query\n"
            "  quit - Exit",
            border_style="cyan",
            title="Welcome"
        ))

        self.show_stats()

        while True:
            try:
                console.print("\n[bold cyan]>[/bold cyan] ", end="")
                cmd = input().strip()

                if not cmd:
                    continue

                if cmd == "quit":
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif cmd == "stats":
                    self.show_stats()
                elif cmd == "whales":
                    self.show_whales()
                elif cmd.startswith("wallet "):
                    address = cmd.split(" ", 1)[1].strip()
                    self.analyze_wallet(address)
                elif cmd.startswith("query "):
                    query = cmd.split(" ", 1)[1].strip()
                    self.nl_query(query)
                else:
                    console.print("[red]Unknown command. Type 'quit' to exit.[/red]")

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    terminal = AvalyticsTerminal()
    terminal.run()
