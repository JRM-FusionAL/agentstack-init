from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

import httpx
import yaml


@dataclass
class AuditIssue:
    severity: str   # "error" | "warning"
    code: str
    message: str
    fix: str


@dataclass
class AuditReport:
    harness: str
    issues: list[AuditIssue] = field(default_factory=list)
    score: int = 100

    def to_dict(self) -> dict:
        return asdict(self)


def audit_harness(config_dir: Path, harness_name: str, project_dir: Path) -> AuditReport:
    if harness_name == "claude_code":
        issues = _audit_claude_code(config_dir, project_dir)
    elif harness_name == "hermes":
        issues = _audit_hermes(config_dir)
    else:
        issues = []

    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    score = max(0, 100 - errors * 20 - warnings * 5)

    return AuditReport(harness=harness_name, issues=issues, score=score)


def _audit_claude_code(config_dir: Path, project_dir: Path) -> list[AuditIssue]:
    issues: list[AuditIssue] = []

    if not (project_dir / "CLAUDE.md").exists():
        issues.append(AuditIssue(
            severity="error",
            code="MISSING_CLAUDE_MD",
            message="CLAUDE.md not found at project root",
            fix="Run: agentstack-init init --harness claude_code",
        ))

    servers = _collect_claude_code_servers(config_dir, project_dir)
    if not servers:
        issues.append(AuditIssue(
            severity="error",
            code="MISSING_MCP_CONFIG",
            message="No MCP servers configured (checked .mcp.json and ~/.claude.json)",
            fix="Run: agentstack-init init --harness claude_code",
        ))
    else:
        issues.extend(_check_mcp_servers(servers))

    return issues


def _collect_claude_code_servers(config_dir: Path, project_dir: Path) -> dict:
    """Gather MCP servers from the locations Claude Code actually reads:
    <project>/.mcp.json (project scope), then ~/.claude.json top-level
    mcpServers and its per-project projects[<abs path>].mcpServers entry."""
    servers: dict = {}

    servers.update(_read_mcp_servers_json(project_dir / ".mcp.json"))

    claude_json = config_dir.parent / ".claude.json"
    try:
        user_config = json.loads(claude_json.read_text())
    except (json.JSONDecodeError, OSError):
        return servers

    servers.update(user_config.get("mcpServers") or {})
    project_entry = (user_config.get("projects") or {}).get(str(project_dir.resolve())) or {}
    servers.update(project_entry.get("mcpServers") or {})
    return servers


def _read_mcp_servers_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()).get("mcpServers") or {}
    except (json.JSONDecodeError, OSError):
        return {}


def _audit_hermes(config_dir: Path) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    config_file = config_dir / "config.yaml"

    try:
        raw = yaml.safe_load(config_file.read_text()) or {}
    except (yaml.YAMLError, OSError):
        issues.append(AuditIssue(
            severity="error",
            code="UNREADABLE_CONFIG",
            message="~/.hermes/config.yaml is missing or unreadable",
            fix="Reinstall Hermes Agent or restore config.yaml",
        ))
        return issues

    # Hermes >= 0.15 stores servers as a top-level `mcp_servers` mapping;
    # older configs used a `mcp.servers` list. Accept either.
    servers = raw.get("mcp_servers") or (raw.get("mcp") or {}).get("servers") or {}
    if not servers:
        issues.append(AuditIssue(
            severity="error",
            code="MISSING_MCP_CONFIG",
            message="No MCP servers configured in ~/.hermes/config.yaml (mcp_servers)",
            fix="Run: agentstack-init init --harness hermes",
        ))

    return issues


def _check_mcp_servers(servers: dict) -> list[AuditIssue]:
    issues: list[AuditIssue] = []

    for name, server in servers.items():
        url = server.get("url")
        if url and url.startswith("http"):
            try:
                httpx.get(url, timeout=2.0)
            except Exception:
                issues.append(AuditIssue(
                    severity="error",
                    code="MCP_SERVER_UNREACHABLE",
                    message=f"MCP server '{name}' unreachable at {url}",
                    fix=f"Ensure the service is running: {url}",
                ))

    return issues
