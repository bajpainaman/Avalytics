#!/usr/bin/env python3
"""
Quick demo of Avalytics capabilities
Run this to see the platform in action
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from indexer.extract_blocks import BlockExtractor
from analytics.wallet_profiler import WalletProfiler
from analytics.cohort_detector import CohortDetector
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def run_demo():
    """Run a quick demo of Avalytics"""

    console.print("\n[bold cyan]Avalytics Demo[/bold cyan]")
    console.print("=" * 50)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # Step 1: Index blocks
        task1 = progress.add_task("[cyan]Indexing latest 50 blocks...", total=None)
        try:
            extractor = BlockExtractor()
            blocks = extractor.extract_latest(50)
            progress.update(task1, completed=True)
            console.print(f"[green]Indexed {blocks} blocks[/green]")
        except Exception as e:
            console.print(f"[red]Error indexing: {e}[/red]")
            return

        # Step 2: Profile wallets
        task2 = progress.add_task("[cyan]Building wallet profiles...", total=None)
        try:
            profiler = WalletProfiler()
            profiler.build_profiles()
            progress.update(task2, completed=True)
            console.print("[green]Wallet profiles created[/green]")
        except Exception as e:
            console.print(f"[red]Error profiling: {e}[/red]")
            return

        # Step 3: Detect cohorts
        task3 = progress.add_task("[cyan]Detecting cohorts...", total=None)
        try:
            detector = CohortDetector()
            detector.detect_cohorts()
            progress.update(task3, completed=True)
            console.print("[green]Cohorts detected[/green]")
        except Exception as e:
            console.print(f"[red]Error detecting cohorts: {e}[/red]")
            return

    console.print("\n[bold green]Demo completed successfully![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Run [cyan]python cli/terminal.py[/cyan] for interactive mode")
    console.print("  2. Try natural language queries like:")
    console.print("     - 'show me the top 10 wallets by transaction count'")
    console.print("     - 'find all whales'")
    console.print("     - 'analyze wallet <address>'")

if __name__ == "__main__":
    run_demo()
