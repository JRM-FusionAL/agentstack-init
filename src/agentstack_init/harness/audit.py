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

    mcp_config = config_dir / "claude_mcp_settings.json"
    if not mcp_config.exists():
        issues.append(AuditIssue(
            severity="error",
            code="MISSING_MCP_CONFIG",
            message="No MCP config at ~/.claude/claude_mcp_settings.json",
            fix="Run: agentstack-init init --harness claude_code",
        ))
    else:
        issues.extend(_check_mcp_servers(mcp_config))

    return issues


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

    servers = (raw.get("mcp") or {}).get("servers") or []
    if not servers:
        issues.append(AuditIssue(
            severity="error",
            code="MISSING_MCP_CONFIG",
            message="No MCP servers configured in ~/.hermes/config.yaml",
            fix="Run: agentstack-init init --harness hermes",
        ))

    return issues


def _check_mcp_servers(mcp_config_path: Path) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    try:
        config = json.loads(mcp_config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return issues

    for name, server in (config.get("mcpServers") or {}).items():
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
