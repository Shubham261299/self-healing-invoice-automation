"""Entry point — CLI runner for the invoice automation."""
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.automation import InvoiceBot
from src.invoice_tracker import append_result
from src.logger import get_logger

log = get_logger()
console = Console()


def print_summary(result: dict, simulate: bool):
    table = Table(title="🧾 Invoice Automation Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Mode", "🩹 Self-Healing Demo" if simulate else "✓ Healthy Selectors")
    table.add_row("Login", "✓ Success" if result["login_ok"] else "✗ Failed")
    table.add_row("Invoices Found", str(result["invoices_found"]))
    table.add_row("Sample Download", "✓ Success" if result["download_ok"] else "✗ Failed")
    table.add_row("Heal Events", str(len(result["heal_events"])))

    console.print(table)

    if result["heal_events"]:
        console.print("\n[bold yellow]🩹 Self-Healing Events:[/bold yellow]")
        for i, h in enumerate(result["heal_events"], 1):
            console.print(Panel.fit(
                f"[bold]Purpose:[/bold] {h['purpose']}\n"
                f"[red]Broken:[/red]  {h['broken']}\n"
                f"[green]Healed:[/green]  {h['healed']}\n"
                f"[dim]Why:[/dim]    {h['reasoning']}",
                title=f"Heal #{i}",
                border_style="yellow",
            ))


def main():
    parser = argparse.ArgumentParser(description="Self-Healing Invoice Automation")
    parser.add_argument("--simulate-breakage", action="store_true",
                        help="Inject broken selectors to demo self-healing")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]Self-Healing Invoice Automation System[/bold cyan]\n"
        f"Mode: {'[yellow]SIMULATE BREAKAGE[/yellow]' if args.simulate_breakage else '[green]NORMAL[/green]'}",
        border_style="cyan",
    ))

    bot = InvoiceBot(simulate_breakage=args.simulate_breakage)
    result = bot.run()

    # Persist to Excel
    append_result({
        "mode": "simulated_breakage" if args.simulate_breakage else "normal",
        "login_ok": result["login_ok"],
        "invoices_found": result["invoices_found"],
        "download_ok": result["download_ok"],
        "heal_count": len(result["heal_events"]),
    })

    print_summary(result, args.simulate_breakage)


if __name__ == "__main__":
    main()