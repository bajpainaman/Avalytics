#!/usr/bin/env python3
"""
Avalytics CLI - Professional blockchain intelligence platform
Foundry-style interface with extensive customization
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import click
import sqlite3
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
from typing import Optional
from ai.structured_analyzer import StructuredAnalyzer

console = Console()

class AvalyticsConfig:
    """Global configuration management"""
    def __init__(self):
        self.config_file = Path.home() / '.avalytics' / 'config.json'
        self.config_file.parent.mkdir(exist_ok=True)
        self.load()

    def load(self):
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.data = json.load(f)
        else:
            self.data = {
                'db_path': './data/avalytics.db',
                'rpc_url': 'https://api.avax.network/ext/bc/C/rpc',
                'ollama_url': 'http://10.246.250.44:11434',
                'output_format': 'table',
                'color_scheme': 'default',
                'verbose': False
            }
            self.save()

    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

config = AvalyticsConfig()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--db', type=str, help='Override database path')
def cli(verbose, db):
    """Avalytics - Blockchain Intelligence Platform for Avalanche

    A professional tool for on-chain analytics, wallet profiling, and intelligence gathering.
    """
    if verbose:
        config.set('verbose', True)
    if db:
        config.set('db_path', db)


@cli.command()
@click.option('--limit', '-n', default=10, help='Number of results to display')
@click.option('--sort', '-s', type=click.Choice(['volume', 'txs', 'contracts']), default='volume')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table')
def wallets(limit, sort, format):
    """List top wallets by various metrics"""
    db_path = config.get('db_path')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sort_cols = {
        'volume': 'CAST(total_volume_wei AS REAL)',
        'txs': 'total_txs',
        'contracts': 'unique_contracts'
    }

    cursor.execute(f'''
        SELECT wallet_address, total_txs, total_volume_wei, unique_contracts,
               is_whale, is_bot, is_dex_user
        FROM wallet_profiles
        ORDER BY {sort_cols[sort]} DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()
    conn.close()

    if format == 'json':
        data = []
        for row in results:
            data.append({
                'address': row[0],
                'transactions': row[1],
                'volume_wei': row[2],
                'contracts': row[3],
                'flags': {
                    'whale': bool(row[4]),
                    'bot': bool(row[5]),
                    'dex_user': bool(row[6])
                }
            })
        console.print_json(data=data)
    elif format == 'csv':
        console.print("address,transactions,volume_wei,contracts,whale,bot,dex_user")
        for row in results:
            console.print(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]}")
    else:
        table = Table(title=f"Top {limit} Wallets (sorted by {sort})", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("Address", style="cyan", no_wrap=True)
        table.add_column("Txs", justify="right")
        table.add_column("Volume (AVAX)", justify="right", style="green")
        table.add_column("Contracts", justify="right")
        table.add_column("Type", style="yellow")

        for row in results:
            addr, txs, vol, contracts, whale, bot, dex = row
            types = []
            if whale: types.append("WHALE")
            if bot: types.append("BOT")
            if dex: types.append("DEX")

            table.add_row(
                addr[:10] + "..." + addr[-8:],
                str(txs),
                f"{int(vol)/10**18:,.2f}",
                str(contracts or 0),
                " | ".join(types) or "RETAIL"
            )

        console.print(table)


@cli.command()
@click.argument('address')
@click.option('--ai', is_flag=True, help='Enable AI-powered deep analysis')
@click.option('--patterns', is_flag=True, help='Analyze transaction patterns')
def inspect(address, ai, patterns):
    """Deep inspection of a specific wallet"""
    db_path = config.get('db_path')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT total_txs, total_volume_wei, unique_contracts,
               is_whale, is_bot, is_dex_user, avg_tx_value_wei,
               first_seen, last_active
        FROM wallet_profiles
        WHERE wallet_address = ?
    ''', (address,))

    row = cursor.fetchone()

    if not row:
        console.print(f"[red]Error:[/red] Wallet {address} not found in database")
        return

    txs, vol, contracts, whale, bot, dex, avg_tx, first, last = row

    console.print(f"\n[bold]Wallet:[/bold] {address}\n")
    console.print(f"  First Seen:     {first}")
    console.print(f"  Last Active:    {last}")
    console.print(f"  Transactions:   {txs:,}")
    console.print(f"  Volume:         {int(vol)/10**18:,.4f} AVAX")
    console.print(f"  Avg Tx Value:   {int(avg_tx)/10**18:,.6f} AVAX")
    console.print(f"  Contracts:      {contracts or 0}")

    flags = []
    if whale: flags.append("WHALE")
    if bot: flags.append("BOT")
    if dex: flags.append("DEX_USER")
    console.print(f"  Classification: {' | '.join(flags) if flags else 'RETAIL'}\n")

    if ai:
        console.print("[dim]Running AI analysis...[/dim]")
        analyzer = StructuredAnalyzer(db_path)
        try:
            profile = analyzer.analyze_wallet_structured(address)
            console.print(f"\n[bold]AI Analysis:[/bold]")
            console.print(f"  Type:           {profile.wallet_type}")
            console.print(f"  Risk Level:     {profile.risk_level}")
            console.print(f"  Activity:       {profile.activity_pattern}")
            console.print(f"  Primary Use:    {profile.primary_use_case}")
            console.print(f"  Sophistication: {profile.sophistication_score}/10")
            console.print(f"\n[bold]Key Insights:[/bold]")
            for insight in profile.key_insights:
                console.print(f"  - {insight}")
            console.print(f"\n[bold]Recommended Approach:[/bold]\n  {profile.recommended_approach}\n")
        except Exception as e:
            console.print(f"[red]AI analysis failed:[/red] {e}")

    if patterns:
        console.print("[dim]Analyzing transaction patterns...[/dim]")
        analyzer = StructuredAnalyzer(db_path)
        try:
            pattern = analyzer.detect_transaction_pattern(address)
            console.print(f"\n[bold]Transaction Pattern:[/bold]")
            console.print(f"  Type:       {pattern.pattern_type}")
            console.print(f"  Confidence: {pattern.confidence:.1%}")
            console.print(f"  Reasoning:  {pattern.explanation}\n")
        except Exception as e:
            console.print(f"[red]Pattern analysis failed:[/red] {e}")

    conn.close()


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
def cohorts(format):
    """List all wallet cohorts"""
    db_path = config.get('db_path')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            wt.tag,
            COUNT(*) as wallet_count,
            AVG(CAST(wp.total_volume_wei AS REAL)) as avg_volume,
            AVG(wp.total_txs) as avg_txs,
            SUM(wp.is_whale) as whales
        FROM wallet_tags wt
        JOIN wallet_profiles wp ON wt.wallet_address = wp.wallet_address
        WHERE wt.tag LIKE 'cluster_%'
        GROUP BY wt.tag
        ORDER BY wallet_count DESC
    ''')

    results = cursor.fetchall()
    conn.close()

    if format == 'json':
        data = []
        for row in results:
            cohort_id = row[0].replace('cluster_', '')
            data.append({
                'cohort_id': cohort_id,
                'wallets': row[1],
                'avg_volume_avax': row[2] / 10**18,
                'avg_txs': row[3],
                'whales': row[4]
            })
        console.print_json(data=data)
    else:
        table = Table(title="Wallet Cohorts", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("Cohort", style="cyan")
        table.add_column("Wallets", justify="right")
        table.add_column("Avg Volume (AVAX)", justify="right", style="green")
        table.add_column("Avg Txs", justify="right")
        table.add_column("Whales", justify="right", style="yellow")

        for row in results:
            cohort_id = row[0].replace('cluster_', '')
            table.add_row(
                f"Cohort {cohort_id}",
                f"{row[1]:,}",
                f"{row[2]/10**18:,.2f}",
                f"{row[3]:.1f}",
                str(row[4])
            )

        console.print(table)


@cli.command()
def stats():
    """Display platform statistics"""
    db_path = config.get('db_path')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(DISTINCT wallet_address) as wallets,
            SUM(total_txs) as txs,
            SUM(CAST(total_volume_wei AS REAL)) as volume,
            SUM(is_whale) as whales,
            SUM(is_bot) as bots,
            SUM(is_dex_user) as dex_users
        FROM wallet_profiles
    ''')

    wallets, txs, vol, whales, bots, dex = cursor.fetchone()

    cursor.execute('SELECT COUNT(DISTINCT block_number) FROM transactions')
    blocks = cursor.fetchone()[0]

    conn.close()

    table = Table(title="Avalytics Platform Statistics", box=box.MINIMAL_DOUBLE_HEAD, show_header=False)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right", style="bold")

    table.add_row("Wallets Tracked", f"{wallets:,}")
    table.add_row("Total Transactions", f"{int(txs):,}")
    table.add_row("Blocks Indexed", f"{blocks:,}")
    table.add_row("Total Volume", f"{vol/10**18:,.2f} AVAX")
    table.add_row("Whale Wallets", f"{int(whales):,} ({whales/wallets*100:.1f}%)")
    table.add_row("Bot Wallets", f"{int(bots):,}")
    table.add_row("DEX Users", f"{int(dex):,}")

    console.print(table)


@cli.group()
def config_cmd():
    """Configuration management"""
    pass


@config_cmd.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value"""
    config.set(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")


@config_cmd.command('get')
@click.argument('key', required=False)
def config_get(key):
    """Get configuration value(s)"""
    if key:
        console.print(f"{key}: {config.get(key)}")
    else:
        table = Table(title="Avalytics Configuration", box=box.MINIMAL)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for k, v in config.data.items():
            table.add_row(k, str(v))

        console.print(table)


@cli.group()
def crm():
    """CRM functions for wallet management"""
    pass


@crm.command('add')
@click.argument('address')
@click.option('--name', help='Contact name')
@click.option('--tags', help='Comma-separated tags')
@click.option('--notes', help='Notes about this wallet')
def crm_add(address, name, tags, notes):
    """Add wallet to CRM"""
    db_path = config.get('db_path')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crm_contacts (
            wallet_address TEXT PRIMARY KEY,
            contact_name TEXT,
            tags TEXT,
            notes TEXT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_contact DATETIME
        )
    ''')

    cursor.execute('''
        INSERT OR REPLACE INTO crm_contacts (wallet_address, contact_name, tags, notes)
        VALUES (?, ?, ?, ?)
    ''', (address, name, tags, notes))

    conn.commit()
    conn.close()

    console.print(f"[green]Added {address} to CRM[/green]")


@crm.command('list')
@click.option('--tag', help='Filter by tag')
def crm_list(tag):
    """List CRM contacts"""
    db_path = config.get('db_path')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if tag:
        cursor.execute('''
            SELECT wallet_address, contact_name, tags, added_at
            FROM crm_contacts
            WHERE tags LIKE ?
        ''', (f'%{tag}%',))
    else:
        cursor.execute('''
            SELECT wallet_address, contact_name, tags, added_at
            FROM crm_contacts
        ''')

    results = cursor.fetchall()
    conn.close()

    if not results:
        console.print("[yellow]No contacts found[/yellow]")
        return

    table = Table(title="CRM Contacts", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("Address", style="cyan")
    table.add_column("Name")
    table.add_column("Tags", style="yellow")
    table.add_column("Added")

    for row in results:
        table.add_row(
            row[0][:10] + "..." + row[0][-8:],
            row[1] or "-",
            row[2] or "-",
            row[3][:10] if row[3] else "-"
        )

    console.print(table)


if __name__ == '__main__':
    cli()
