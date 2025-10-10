#!/usr/bin/env python3
"""
Demo of structured AI-powered analytics
Shows Pydantic-based wallet and cohort analysis
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from ai.structured_analyzer import StructuredAnalyzer

console = Console()

def main():
    console.print(Panel.fit(
        "[bold cyan]Avalytics Structured Analytics Demo[/bold cyan]\n"
        "AI-powered wallet intelligence with Pydantic models",
        border_style="blue"
    ))

    analyzer = StructuredAnalyzer()

    # Get a few sample wallets
    conn = sqlite3.connect("./data/avalytics.db")
    cursor = conn.cursor()

    # Get a whale
    cursor.execute('''
        SELECT wallet_address
        FROM wallet_profiles
        WHERE is_whale = 1
        ORDER BY CAST(total_volume_wei AS REAL) DESC
        LIMIT 1
    ''')
    whale = cursor.fetchone()

    # Get a regular wallet
    cursor.execute('''
        SELECT wallet_address
        FROM wallet_profiles
        WHERE is_whale = 0 AND total_txs > 5
        ORDER BY total_txs DESC
        LIMIT 1
    ''')
    regular = cursor.fetchone()

    # Get cohort count
    cursor.execute('SELECT COUNT(DISTINCT tag) FROM wallet_tags WHERE tag LIKE "cluster_%"')
    cohort_count = cursor.fetchone()[0]

    conn.close()

    # Analyze whale
    if whale:
        console.print("\n[bold yellow]═══ Whale Wallet Analysis ═══[/bold yellow]\n")
        whale_addr = whale[0]
        console.print(f"Wallet: [cyan]{whale_addr}[/cyan]\n")

        try:
            with console.status("[bold green]Analyzing whale wallet..."):
                profile = analyzer.analyze_wallet_structured(whale_addr)

            console.print(f"[bold]Type:[/bold] {profile.wallet_type}")
            console.print(f"[bold]Risk:[/bold] {profile.risk_level}")
            console.print(f"[bold]Activity:[/bold] {profile.activity_pattern}")
            console.print(f"[bold]Use Case:[/bold] {profile.primary_use_case}")
            console.print(f"[bold]Sophistication:[/bold] {profile.sophistication_score}/10\n")

            console.print("[bold]Key Insights:[/bold]")
            for insight in profile.key_insights:
                console.print(f"  • {insight}")

            console.print(f"\n[bold]Recommended Approach:[/bold]\n  {profile.recommended_approach}\n")

            # Transaction pattern
            with console.status("[bold green]Detecting transaction patterns..."):
                pattern = analyzer.detect_transaction_pattern(whale_addr)

            console.print(f"[bold]Transaction Pattern:[/bold] {pattern.pattern_type}")
            console.print(f"[bold]Confidence:[/bold] {pattern.confidence:.1%}")
            console.print(f"[bold]Explanation:[/bold] {pattern.explanation}\n")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")

    # Analyze regular wallet
    if regular:
        console.print("[bold yellow]═══ Regular Wallet Analysis ═══[/bold yellow]\n")
        regular_addr = regular[0]
        console.print(f"Wallet: [cyan]{regular_addr}[/cyan]\n")

        try:
            with console.status("[bold green]Analyzing regular wallet..."):
                profile = analyzer.analyze_wallet_structured(regular_addr)

            console.print(f"[bold]Type:[/bold] {profile.wallet_type}")
            console.print(f"[bold]Risk:[/bold] {profile.risk_level}")
            console.print(f"[bold]Sophistication:[/bold] {profile.sophistication_score}/10\n")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")

    # Analyze cohorts
    if cohort_count > 0:
        console.print("[bold yellow]═══ Cohort Analysis ═══[/bold yellow]\n")

        for cohort_id in range(min(3, cohort_count)):  # Analyze first 3 cohorts
            try:
                with console.status(f"[bold green]Analyzing cohort {cohort_id}..."):
                    analysis = analyzer.analyze_cohort_structured(cohort_id)

                console.print(f"\n[bold cyan]Cohort {cohort_id}: {analysis.cohort_name}[/bold cyan]")
                console.print(f"  Behavior: {analysis.typical_behavior}")
                console.print(f"  Strategy: {analysis.engagement_strategy}\n")

            except Exception as e:
                console.print(f"[red]Cohort {cohort_id} error: {e}[/red]\n")

    console.print(Panel(
        "[green]✓[/green] Structured analytics demo complete!\n\n"
        "Next steps:\n"
        "  • Run: python cli/dashboard.py for interactive mode\n"
        "  • Use OpenAI-compatible API with Pydantic models\n"
        "  • Export profiles to CRM systems",
        title="Demo Complete",
        border_style="green"
    ))

if __name__ == "__main__":
    main()
