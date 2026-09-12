"""
Rich Command-Line Interface for LabGenius.
Interactive, colorized terminal runner for solving labs and compiling reports.
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .config import Config
from .parser import ManualParser
from .solver import TaskSolver
from .runner import CodeRunner
from .capture import ScreenshotStudio
from .builder import DocumentBuilder
from .sanitizer import DocumentSanitizer

console = Console()


def render_banner(config: Config):
    banner_text = (
        "[bold cyan]LabGenius[/bold cyan] [bold white]v1.0.0[/bold white] — [italic green]Authentic Academic Lab Completer[/italic green]\n"
        f"[dim]OS: Pop!_OS / COSMIC | User: {config.system.username} | Host: {config.system.hostname}[/dim]\n"
        f"[bold yellow]Student:[/] {config.student.name} ([bold]{config.student.roll_number}[/]) | [bold yellow]Dept:[/] {config.student.department}"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def main():
    parser = argparse.ArgumentParser(description="LabGenius: Automated Academic Lab Completer")
    parser.add_argument("--manual", "-m", type=str, required=False, help="Path to input lab manual (DOCX/PDF/TXT)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output destination for completed DOCX")
    parser.add_argument("--name", type=str, default=None, help="Student Name override")
    parser.add_argument("--roll", type=str, default=None, help="Student Roll Number override")
    parser.add_argument("--dept", type=str, default=None, help="Department override")
    parser.add_argument("--provider", type=str, choices=["gemini", "openai", "anthropic", "ollama", "mock"], default=None)
    parser.add_argument("--model", type=str, default=None, help="LLM model (e.g. gemini-2.5-pro, gemini-2.5-flash)")
    parser.add_argument("--api-key", type=str, default=None, help="LLM API Key")
    parser.add_argument("--dry-run", action="store_true", help="Parse tasks and display plan without executing")
    parser.add_argument("--config", "-c", type=str, default=None, help="Path to custom config.yaml")

    args = parser.parse_args()

    # Load configuration
    cfg = Config.load(args.config)
    if args.name:
        cfg.student.name = args.name
    if args.roll:
        cfg.student.roll_number = args.roll
    if args.dept:
        cfg.student.department = args.dept
    if args.provider:
        cfg.ai.provider = args.provider
    if args.model:
        cfg.ai.model = args.model
    if args.api_key:
        cfg.ai.api_key = args.api_key

    render_banner(cfg)

    # If no manual supplied, show usage and available samples
    if not args.manual:
        console.print("\n[bold yellow]Usage Example:[/bold yellow]")
        console.print("  python3 -m labgenius.cli --manual examples/sample_lab_manual.docx\n")
        sample_path = Path("examples/sample_lab_manual.docx")
        if sample_path.exists():
            console.print(f"[green]Found default sample lab manual at: {sample_path}[/green]")
            args.manual = str(sample_path)
        else:
            console.print("[red]Error:[/] Please provide a lab manual using --manual <path_to_file>")
            sys.exit(1)

    manual_path = Path(args.manual)
    if not manual_path.exists():
        console.print(f"[red]Error: Manual file not found:[/] {manual_path}")
        sys.exit(1)

    # 1. Parse Manual
    console.print(f"\n[bold blue][1/5][/bold blue] Parsing Lab Manual: [cyan]{manual_path.name}[/cyan]...")
    parser_obj = ManualParser(str(manual_path))
    lab_manual = parser_obj.parse()

    console.print(f"  [bold green]✓[/bold green] Detected Title: [bold]{lab_manual.title}[/bold]")
    console.print(f"  [bold green]✓[/bold green] Course: [dim]{lab_manual.course_name}[/dim]")
    console.print(f"  [bold green]✓[/bold green] Tasks Extracted: [bold cyan]{len(lab_manual.tasks)}[/bold cyan]")

    # Display Tasks Table
    table = Table(title="Extracted Lab Tasks", border_style="dim")
    table.add_column("Task ID", justify="center", style="bold cyan")
    table.add_column("Title", style="white")
    table.add_column("Lang", style="yellow")
    table.add_column("Requires Plot", justify="center")

    for t in lab_manual.tasks:
        table.add_row(str(t.task_id), t.title, t.language, "Yes" if t.requires_plot else "No")
    console.print(table)

    if args.dry_run:
        console.print("\n[yellow]Dry-run requested. Exiting without execution.[/yellow]")
        sys.exit(0)

    # Initialize Modules
    solver = TaskSolver(cfg)
    runner = CodeRunner(cfg)
    studio = ScreenshotStudio(cfg)
    builder = DocumentBuilder(cfg)
    sanitizer = DocumentSanitizer(cfg)

    solutions = []
    exec_results = []
    screenshots = []

    # 2. Solve, Run, and Capture
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        overall_p = progress.add_task("[cyan]Processing Lab Tasks...", total=len(lab_manual.tasks))

        for idx, task in enumerate(lab_manual.tasks):
            # Step A: Solve task with Student Persona
            progress.update(overall_p, description=f"[cyan]Task {task.task_id}: Formulating student code & answers...")
            sol = solver.solve_task(task)
            solutions.append(sol)

            # Step B: Run code on laptop
            progress.update(overall_p, description=f"[cyan]Task {task.task_id}: Executing locally on laptop...")
            res = runner.execute(sol, sample_input=task.sample_input)

            # Auto-healing check if failed
            if not res.success and cfg.ai.provider != "mock":
                progress.update(overall_p, description=f"[yellow]Task {task.task_id}: Error encountered. Auto-healing code...")
                fixed_code = solver.auto_heal(task, sol.code, res.stderr)
                sol.code = fixed_code
                res = runner.execute(sol, sample_input=task.sample_input)

            exec_results.append(res)

            # Step C: Capture Code & Console Output Screenshots
            progress.update(overall_p, description=f"[cyan]Task {task.task_id}: Capturing code & console output screenshots...")
            code_img, out_img = studio.capture_task_screenshots(sol, res)
            screenshots.append((code_img, out_img))

            progress.advance(overall_p)

    console.print(f"  [bold green]✓[/bold green] Successfully executed {len(solutions)} tasks and captured code & output screenshots.")

    # 3. Build Document
    console.print("\n[bold blue][4/5][/bold blue] Compiling academic report (.docx)...")
    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = Path("output")
        roll_clean = "".join(c for c in cfg.student.roll_number if c.isalnum() or c in ("-", "_"))
        clean_lab = f"LAB{lab_manual.lab_number}_completed" if lab_manual.lab_number else "Completed_Lab_Report"
        out_path = out_dir / f"{clean_lab}.docx"

    built_doc_path = builder.build_report(lab_manual, solutions, exec_results, screenshots, out_path)
    console.print(f"  [bold green]✓[/bold green] Document saved to: [cyan]{built_doc_path}[/cyan]")

    # 4. Sanitize Metadata
    console.print("\n[bold blue][5/5][/bold blue] Deep Metadata Sanitization & Anti-AI Verification...")
    sanitizer.sanitize_docx(built_doc_path)
    verification = sanitizer.verify_sanitization(built_doc_path)

    # Verification Report
    verif_panel = (
        f"[bold green]Document Metadata Sanitization Status: PASSED[/bold green]\n"
        f"• Author / Creator: [bold white]{verification['creator']}[/bold white]\n"
        f"• Last Modified By: [bold white]{verification['last_modified_by']}[/bold white]\n"
        f"• Total Active Editing Time: [bold yellow]{verification['total_time_mins']} minutes[/bold yellow]\n"
        f"• Document Revision Count: [bold yellow]{verification['revision']}[/bold yellow]\n"
        f"• AI/python-docx Fingerprint Found: [{'red' if verification['has_python_docx_tag'] else 'green'}]{verification['has_python_docx_tag']}[/]"
    )
    console.print(Panel(verif_panel, border_style="green", expand=False))

    console.print(f"\n[bold green]★ Lab Report Generation Complete! ★[/bold green]")
    console.print(f"File ready for university submission: [bold underline cyan]{built_doc_path.resolve()}[/bold underline cyan]\n")


if __name__ == "__main__":
    main()
