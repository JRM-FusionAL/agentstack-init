from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .harness.audit import audit_harness as _audit_harness
from .harness.detect import detect_harness as _detect_harness
from .harness.scaffold import scaffold_claude_md as _scaffold_claude_md
from .harness.scaffold import scaffold_mcp_config as _scaffold_mcp_config

load_dotenv()

HOST = os.getenv("AGENTSTACK_HOST", "0.0.0.0")
PORT = int(os.getenv("AGENTSTACK_PORT", "8200"))

mcp = FastMCP("agentstack-init")


@mcp.tool()
def detect_harness(project_dir: str = ".") -> dict:
    """Detect which AI harnesses (Claude Code, Hermes) are installed."""
    results = _detect_harness(Path(project_dir))
    return {
        "harnesses": [
            {
                "name": h.name,
                "version": h.version,
                "config_root": str(h.config_root),
                "known_issues": h.known_issues,
            }
            for h in results
        ]
    }


@mcp.tool()
def audit_harness(config_dir: str, harness_name: str, project_dir: str = ".") -> dict:
    """Audit a harness config for broken MCP wiring, missing CLAUDE.md, and unreachable servers."""
    report = _audit_harness(Path(config_dir), harness_name, Path(project_dir))
    return report.to_dict()


@mcp.tool()
def scaffold_claude_md(harness_name: str, project_name: str) -> str:
    """Generate a CLAUDE.md scaffold tuned for the specified harness."""
    return _scaffold_claude_md(harness_name, project_name)


@mcp.tool()
def scaffold_mcp_config(harness_name: str) -> str:
    """Generate a ready-to-paste MCP server config block for the specified harness."""
    return _scaffold_mcp_config(harness_name)


def main() -> None:
    mcp.run(transport="sse", host=HOST, port=PORT)


if __name__ == "__main__":
    main()
