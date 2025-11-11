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
@click.option('--block', '-b', type=int, help='Query specific block number')
@click.option('--tx', '-t', type=str, help='Query transaction by hash')
@click.option('--from-block', type=int, help='Start block number')
@click.option('--to-block', type=int, help='End block number')
@click.option('--address', '-a', type=str, help='Filter by address')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
def query(block, tx, from_block, to_block, address, format):
    """Query blockchain data from Avalanche C-Chain"""
    from web3 import Web3
    
    rpc_url = config.get('rpc_url', 'http://localhost:9650/ext/bc/C/rpc')
    
    console.print(f"[dim]Connecting to {rpc_url}...[/dim]")
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            console.print(f"[red]Error:[/red] Failed to connect to RPC endpoint")
            return
        
        latest_block = w3.eth.block_number
        console.print(f"[green]Connected[/green] - Latest block: {latest_block:,}\n")
        
        if block:
            # Query single block
            console.print(f"[bold]Fetching block {block}...[/bold]")
            try:
                block_data = w3.eth.get_block(block, full_transactions=True)
                
                if format == 'json':
                    result = {
                        'block_number': block_data['number'],
                        'hash': block_data['hash'].hex(),
                        'timestamp': block_data['timestamp'],
                        'transaction_count': len(block_data['transactions']),
                        'gas_used': block_data['gasUsed'],
                        'gas_limit': block_data['gasLimit']
                    }
                    console.print_json(data=result)
                else:
                    table = Table(title=f"Block {block}", box=box.MINIMAL)
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="green")
                    
                    table.add_row("Block Number", str(block_data['number']))
                    table.add_row("Hash", block_data['hash'].hex()[:20] + "...")
                    table.add_row("Timestamp", str(block_data['timestamp']))
                    table.add_row("Transactions", str(len(block_data['transactions'])))
                    table.add_row("Gas Used", f"{block_data['gasUsed']:,}")
                    table.add_row("Gas Limit", f"{block_data['gasLimit']:,}")
                    
                    console.print(table)
                    
                    # Show transactions if address filter
                    if address and block_data['transactions']:
                        console.print(f"\n[bold]Transactions involving {address}:[/bold]")
                        matches = [tx for tx in block_data['transactions'] 
                                 if tx['from'].lower() == address.lower() or 
                                    (tx['to'] and tx['to'].lower() == address.lower())]
                        console.print(f"  Found {len(matches)} matching transactions")
                        
            except Exception as e:
                console.print(f"[red]Error fetching block:[/red] {e}")
        elif tx:
            # Query transaction
            console.print(f"[bold]Fetching transaction {tx}...[/bold]")
            try:
                tx_data = w3.eth.get_transaction(tx)
                receipt = w3.eth.get_transaction_receipt(tx)
                
                if format == 'json':
                    result = {
                        'hash': tx_data['hash'].hex(),
                        'block_number': tx_data['blockNumber'],
                        'from': tx_data['from'],
                        'to': tx_data['to'],
                        'value': str(tx_data['value']),
                        'gas_price': str(tx_data['gasPrice']),
                        'gas_used': receipt['gasUsed'],
                        'status': 'success' if receipt['status'] == 1 else 'failed'
                    }
                    console.print_json(data=result)
                else:
                    table = Table(title=f"Transaction {tx[:20]}...", box=box.MINIMAL)
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="green")
                    
                    table.add_row("Hash", tx_data['hash'].hex())
                    table.add_row("Block", str(tx_data['blockNumber']))
                    table.add_row("From", tx_data['from'])
                    table.add_row("To", tx_data['to'] or "Contract Creation")
                    table.add_row("Value", f"{tx_data['value'] / 10**18:.6f} AVAX")
                    table.add_row("Gas Used", f"{receipt['gasUsed']:,}")
                    table.add_row("Status", "✅ Success" if receipt['status'] == 1 else "❌ Failed")
                    
                    console.print(table)
            except Exception as e:
                console.print(f"[red]Error fetching transaction:[/red] {e}")
        elif from_block and to_block:
            # Query block range
            console.print(f"[bold]Querying blocks {from_block:,} to {to_block:,}...[/bold]")
            
            if to_block - from_block > 1000:
                console.print("[yellow]Warning: Large range, this may take a while...[/yellow]")
            
            try:
                blocks_data = []
                total_txs = 0
                total_gas = 0
                
                # Sample blocks for large ranges
                step = max(1, (to_block - from_block) // 100) if (to_block - from_block) > 100 else 1
                max_blocks = min(100, to_block - from_block + 1)
                
                matching_txs = []
                
                with Progress() as progress:
                    task = progress.add_task("[cyan]Fetching blocks...", total=max_blocks)
                    
                    for block_num in range(from_block, min(to_block + 1, from_block + max_blocks)):
                        try:
                            # Fetch full transactions if address filter is set
                            full_txs = address is not None
                            block_data = w3.eth.get_block(block_num, full_transactions=full_txs)
                            
                            block_tx_count = len(block_data['transactions'])
                            
                            # Filter by address if specified
                            if address and full_txs:
                                for tx in block_data['transactions']:
                                    if (tx['from'].lower() == address.lower() or 
                                        (tx['to'] and tx['to'].lower() == address.lower())):
                                        matching_txs.append({
                                            'hash': tx['hash'].hex(),
                                            'block': block_num,
                                            'from': tx['from'],
                                            'to': tx['to'],
                                            'value': int(tx['value'])
                                        })
                            
                            blocks_data.append({
                                'number': block_data['number'],
                                'tx_count': block_tx_count,
                                'gas_used': block_data['gasUsed'],
                                'timestamp': block_data['timestamp']
                            })
                            total_txs += block_tx_count
                            total_gas += block_data['gasUsed']
                            progress.update(task, advance=1)
                        except Exception as e:
                            console.print(f"[red]Error fetching block {block_num}:[/red] {e}")
                            break
                
                if format == 'json':
                    result = {
                        'from_block': from_block,
                        'to_block': to_block,
                        'blocks_queried': len(blocks_data),
                        'total_transactions': total_txs,
                        'total_gas_used': total_gas,
                        'blocks': blocks_data
                    }
                    console.print_json(data=result)
                else:
                    table = Table(title=f"Block Range {from_block:,} - {to_block:,}", box=box.MINIMAL)
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="green", justify="right")
                    
                    table.add_row("Blocks Queried", f"{len(blocks_data):,}")
                    table.add_row("Total Transactions", f"{total_txs:,}")
                    table.add_row("Total Gas Used", f"{total_gas:,}")
                    if len(blocks_data) > 0:
                        avg_txs = total_txs / len(blocks_data)
                        avg_gas = total_gas / len(blocks_data)
                        table.add_row("Avg Txs per Block", f"{avg_txs:.1f}")
                        table.add_row("Avg Gas per Block", f"{avg_gas:,.0f}")
                    
                    console.print(table)
                    
                    # Show matching transactions if address filter was used
                    if address and matching_txs:
                        console.print(f"\n[bold]Found {len(matching_txs)} transactions for {address}:[/bold]")
                        tx_table = Table(box=box.MINIMAL)
                        tx_table.add_column("Hash", style="cyan", no_wrap=False)
                        tx_table.add_column("Block", justify="right")
                        tx_table.add_column("From", style="yellow")
                        tx_table.add_column("To", style="yellow")
                        tx_table.add_column("Value (AVAX)", justify="right", style="green")
                        
                        for tx in matching_txs[:20]:  # Limit to 20 for display
                            tx_table.add_row(
                                tx['hash'][:16] + "...",
                                str(tx['block']),
                                tx['from'][:10] + "...",
                                (tx['to'][:10] + "..." if tx['to'] else "Contract"),
                                f"{tx['value'] / 10**18:.6f}"
                            )
                        
                        if len(matching_txs) > 20:
                            console.print(f"[dim]... and {len(matching_txs) - 20} more[/dim]")
                        
                        console.print(tx_table)
                    
            except Exception as e:
                console.print(f"[red]Error querying block range:[/red] {e}")
        else:
            console.print("[yellow]Query functionality coming soon...[/yellow]")
            console.print("  Use --block to query a specific block")
            console.print("  Use --from-block and --to-block for ranges")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@cli.command()
@click.option('--blocks', '-n', default=100, help='Number of recent blocks to analyze')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
def chain_stats(blocks, format):
    """Show chain performance statistics (TPS, gas, volume)"""
    from web3 import Web3
    
    rpc_url = config.get('rpc_url', 'http://localhost:9650/ext/bc/C/rpc')
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            console.print(f"[red]Error:[/red] Failed to connect to RPC endpoint")
            return
        
        latest_block = w3.eth.block_number
        start_block = max(0, latest_block - blocks)
        
        console.print(f"[dim]Analyzing blocks {start_block:,} to {latest_block:,}...[/dim]\n")
        
        total_txs = 0
        total_gas = 0
        total_volume = 0
        block_times = []
        prev_timestamp = None
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching blocks...", total=blocks)
            
            for block_num in range(start_block, latest_block + 1):
                try:
                    block = w3.eth.get_block(block_num, full_transactions=True)
                    total_txs += len(block['transactions'])
                    total_gas += block['gasUsed']
                    
                    # Calculate volume from transactions
                    for tx in block['transactions']:
                        total_volume += int(tx['value'])
                    
                    # Calculate block time
                    if prev_timestamp:
                        block_time = block['timestamp'] - prev_timestamp
                        block_times.append(block_time)
                    prev_timestamp = block['timestamp']
                    
                    progress.update(task, advance=1)
                except Exception as e:
                    break
        
        if len(block_times) == 0:
            console.print("[red]Error:[/red] Could not fetch enough blocks")
            return
        
        # Calculate metrics
        blocks_analyzed = latest_block - start_block + 1
        avg_block_time = sum(block_times) / len(block_times) if block_times else 0
        tps = total_txs / (avg_block_time * blocks_analyzed) if avg_block_time > 0 else 0
        avg_gas_per_block = total_gas / blocks_analyzed
        avg_txs_per_block = total_txs / blocks_analyzed
        
        if format == 'json':
            result = {
                'blocks_analyzed': blocks_analyzed,
                'total_transactions': total_txs,
                'total_gas_used': total_gas,
                'total_volume_avax': total_volume / 10**18,
                'avg_block_time_seconds': avg_block_time,
                'transactions_per_second': tps,
                'avg_gas_per_block': avg_gas_per_block,
                'avg_txs_per_block': avg_txs_per_block
            }
            console.print_json(data=result)
        else:
            table = Table(title="Chain Performance Statistics", box=box.MINIMAL_DOUBLE_HEAD)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")
            
            table.add_row("Blocks Analyzed", f"{blocks_analyzed:,}")
            table.add_row("Total Transactions", f"{total_txs:,}")
            table.add_row("Total Volume", f"{total_volume / 10**18:,.2f} AVAX")
            table.add_row("Total Gas Used", f"{total_gas:,}")
            table.add_row("", "")
            table.add_row("Avg Block Time", f"{avg_block_time:.2f} seconds")
            table.add_row("Transactions/Second", f"{tps:.2f}")
            table.add_row("Avg Txs per Block", f"{avg_txs_per_block:.1f}")
            table.add_row("Avg Gas per Block", f"{avg_gas_per_block:,.0f}")
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


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


@cli.group()
def monday():
    """Monday.com integration for CRM"""
    pass


@monday.command('create')
@click.option('--name', default='Avalytics Wallet Intelligence', help='Board name')
def monday_create(name):
    """Create a new Monday.com board for wallet tracking"""
    sys.path.append(str(Path(__file__).parent.parent))
    from integrations.monday_client import MondayClient

    try:
        client = MondayClient()
        board_id = client.create_board(name)
        console.print(f"[green][+] Created Monday.com board: {name}[/green]")
        console.print(f"[cyan]Board ID: {board_id}[/cyan]")
        console.print(f"\nNext: Run [bold]avalytics.py monday sync {board_id}[/bold] to sync wallets")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@monday.command('sync')
@click.argument('board_id')
@click.option('--limit', '-n', default=100, help='Number of wallets to sync')
@click.option('--min-volume', type=float, help='Minimum volume in AVAX')
@click.option('--whale-only', is_flag=True, help='Sync only whale wallets')
@click.option('--with-ai', is_flag=True, help='Include AI analysis for each wallet')
@click.option('--with-research', is_flag=True, help='Include web research (Grok/Perplexity)')
def monday_sync(board_id, limit, min_volume, whale_only, with_ai, with_research):
    """Sync wallets from Avalytics to Monday.com board"""
    sys.path.append(str(Path(__file__).parent.parent))
    from integrations.monday_client import MondayClient
    import sqlite3

    db_path = config.get('db_path')
    client = MondayClient()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build query based on filters
    where_clauses = []
    params = []

    if min_volume:
        where_clauses.append("CAST(total_volume_wei AS REAL) >= ?")
        params.append(min_volume * 10**18)

    if whale_only:
        where_clauses.append("is_whale = 1")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    cursor.execute(f'''
        SELECT
            wallet_address,
            total_txs,
            total_volume_wei,
            is_whale,
            is_bot,
            is_dex_user,
            last_active
        FROM wallet_profiles
        WHERE {where_sql}
        ORDER BY CAST(total_volume_wei AS REAL) DESC
        LIMIT ?
    ''', params + [limit])

    wallets = []

    # Optionally get AI analyzer
    analyzer = None
    if with_ai:
        from ai.structured_analyzer import StructuredAnalyzer
        analyzer = StructuredAnalyzer(db_path)
        console.print("[dim]AI analysis enabled - this will be slower...[/dim]")

    for row in cursor.fetchall():
        wallet_type = "WHALE" if row[3] else ("BOT" if row[4] else ("DEX" if row[5] else "RETAIL"))

        wallet_data = {
            "address": row[0],
            "tx_count": row[1],
            "volume_avax": int(row[2]) / 10**18,
            "wallet_type": wallet_type,
            "risk_level": "HIGH" if row[3] else "LOW",
            "last_active": row[6],
            "contact_status": "NEW"
        }

        # Add AI analysis if requested
        if with_ai and analyzer:
            try:
                profile = analyzer.analyze_wallet_structured(row[0])
                wallet_data["ai_analysis"] = f"""Type: {profile.wallet_type}
Risk: {profile.risk_level}
Activity: {profile.activity_pattern}
Use Case: {profile.primary_use_case}
Sophistication: {profile.sophistication_score}/10

Key Insights:
{chr(10).join(f'- {i}' for i in profile.key_insights[:3])}

Approach: {profile.recommended_approach}"""
            except Exception as e:
                console.print(f"[dim][-] AI analysis failed for {row[0][:10]}...: {e}[/dim]")
                wallet_data["ai_analysis"] = ""

        # Add web research if requested
        if with_research:
            try:
                from integrations.perplexity_client import PerplexityClient
                research_client = PerplexityClient()

                console.print(f"[dim]Researching {row[0][:10]}... with web search...[/dim]")
                entity_info = research_client.research_wallet_entity(row[0])
                scam_info = research_client.check_scam_indicators(row[0])

                research_text = f"""
ENTITY RESEARCH:
{entity_info['entity_info']}

RISK CHECK:
{scam_info['scam_check']}
Risk Level: {scam_info['risk_level']}
"""
                if wallet_data.get("ai_analysis"):
                    wallet_data["ai_analysis"] += f"\n\nWEB RESEARCH:{research_text}"
                else:
                    wallet_data["ai_analysis"] = research_text

            except Exception as e:
                console.print(f"[dim][-] Web research failed for {row[0][:10]}...: {e}[/dim]")

        wallets.append(wallet_data)

    conn.close()

    if not wallets:
        console.print("[yellow]No wallets found matching criteria[/yellow]")
        return

    console.print(f"[*] Syncing {len(wallets)} wallets to Monday.com...")

    try:
        item_ids = client.bulk_sync_wallets(board_id, wallets)
        console.print(f"[green][+] Successfully synced {len(item_ids)} wallets to Monday.com[/green]")
    except Exception as e:
        console.print(f"[red]Error syncing: {e}[/red]")


@monday.command('list')
def monday_list():
    """List all Monday.com boards"""
    sys.path.append(str(Path(__file__).parent.parent))
    from integrations.monday_client import MondayClient

    try:
        client = MondayClient()
        boards = client.get_boards()

        table = Table(title="Monday.com Boards", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Type", style="yellow")
        table.add_column("State", style="green")

        for board in boards:
            table.add_row(
                board['id'],
                board['name'],
                board['board_kind'],
                board['state']
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


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
