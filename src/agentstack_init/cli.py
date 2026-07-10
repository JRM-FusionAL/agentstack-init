from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .harness.audit import audit_harness as _audit_harness
from .harness.detect import detect_harness as _detect_harness
from .harness.scaffold import scaffold_claude_md as _scaffold_claude_md
from .harness.scaffold import scaffold_mcp_config as _scaffold_mcp_config

app = typer.Typer(help="Audit and scaffold AI harness configs.")

CTA = "\n→ Book a free 30-min review: agentstack.fyi/audit\n"

_MEMORY_SETUP = """\
# Memory Setup

Connect to agentstack memory (FusionAL-Recall).

## Quickstart

1. Ensure the agentstack MCP server is running:
   agentstack-init serve

2. Add the config block from mcp-config.json to your harness MCP settings.

3. Test: open your harness and run:
   recall hello world

## Tools available via MCP

- recall <query>       — search past solutions
- remember <solution>  — save a solution for future recall
- list_recent          — list recent entries
- verify <id>          — look up a specific entry
"""


def _ensure_fusional(project_dir: Path) -> Path:
    d = project_dir / ".fusional"
    d.mkdir(parents=True, exist_ok=True)
    return d


@app.command()
def init(
    harness: str = typer.Option("claude_code", help="Harness to scaffold: claude_code | hermes"),
    project_name: Optional[str] = typer.Option(None, help="Project name for CLAUDE.md"),
    project_dir: str = typer.Option(".", help="Project root directory"),
):
    """Detect harness, scaffold CLAUDE.md + MCP config, write to .fusional/"""
    cwd = Path(project_dir).resolve()
    name = project_name or cwd.name

    out = _ensure_fusional(cwd)

    (out / "CLAUDE.md").write_text(_scaffold_claude_md(harness, name))
    typer.echo(f"✓  .fusional/CLAUDE.md")

    config_content = _scaffold_mcp_config(harness)
    if harness == "hermes":
        import yaml as _yaml
        (out / "mcp-config.yaml").write_text(config_content)
        parsed = _yaml.safe_load(config_content)
        (out / "mcp-config.json").write_text(json.dumps(parsed, indent=2))
        typer.echo("✓  .fusional/mcp-config.yaml")
    else:
        (out / "mcp-config.json").write_text(config_content)
        typer.echo("✓  .fusional/mcp-config.json")

    (out / "memory-setup.md").write_text(_MEMORY_SETUP)
    typer.echo("✓  .fusional/memory-setup.md")

    typer.echo(f"\nCopy files from .fusional/ into your {harness} config directory.")
    typer.echo(CTA)


@app.command()
def audit(
    harness: str = typer.Option("claude_code", help="Harness to audit: claude_code | hermes"),
    project_dir: str = typer.Option(".", help="Project root directory"),
):
    """Run harness audit, print report, write .fusional/audit-report.json"""
    cwd = Path(project_dir).resolve()
    harnesses = _detect_harness(cwd)

    matched = next((h for h in harnesses if h.name == harness), None)
    if matched is None:
        typer.echo(f"⚠  Harness '{harness}' not detected on this system.")
        typer.echo(CTA)
        raise typer.Exit(0)

    report = _audit_harness(matched.config_root, harness, cwd)

    for issue in report.issues:
        symbol = "✗" if issue.severity == "error" else "⚠"
        typer.echo(f"{symbol}  {issue.message}")
        typer.echo(f"   Fix: {issue.fix}")

    if not report.issues:
        typer.echo("✓  No issues found.")

    typer.echo(f"\nScore: {report.score}/100")

    out = _ensure_fusional(cwd)
    report_path = out / "audit-report.json"
    report_path.write_text(json.dumps(report.to_dict(), indent=2))
    typer.echo(f"Full report: {report_path}")
    typer.echo(CTA)


@app.command(name="update-check")
def update_check():
    """Check for harness version drift against last known-good configs."""
    harnesses = _detect_harness(Path("."))

    if not harnesses:
        typer.echo("No harnesses detected.")
        raise typer.Exit(0)

    for h in harnesses:
        typer.echo(f"✓  {h.name}: config_root={h.config_root}")
        for issue in h.known_issues:
            typer.echo(f"   ⚠  {issue}")

    typer.echo("\nAll detected harnesses checked.")
