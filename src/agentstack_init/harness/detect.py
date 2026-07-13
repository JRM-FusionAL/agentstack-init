from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class HarnessInfo:
    name: str
    version: Optional[str]
    config_root: Path
    known_issues: list[str] = field(default_factory=list)


_VERSION_RE = re.compile(r"v?(\d+\.\d+(?:\.\d+)?)")


def _cli_version(binary: str) -> Optional[str]:
    """Ask the harness CLI for its version; None when the binary is absent or odd."""
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    match = _VERSION_RE.search(proc.stdout or "")
    return match.group(1) if match else None


def detect_harness(project_dir: Path) -> list[HarnessInfo]:
    results: list[HarnessInfo] = []
    home = Path.home()

    claude_dir = home / ".claude"
    if claude_dir.exists():
        results.append(HarnessInfo(
            name="claude_code",
            version=_cli_version("claude"),
            config_root=claude_dir,
            known_issues=[],
        ))

    hermes_config = home / ".hermes" / "config.yaml"
    if hermes_config.exists():
        try:
            raw = yaml.safe_load(hermes_config.read_text()) or {}
        except yaml.YAMLError:
            raw = {}
        # Real Hermes configs carry no version key; the CLI is authoritative.
        # A legacy explicit `version:` key remains the fallback.
        version = _cli_version("hermes")
        if version is None and raw.get("version") is not None:
            version = str(raw.get("version"))
        results.append(HarnessInfo(
            name="hermes",
            version=version,
            config_root=hermes_config.parent,
            known_issues=[],
        ))

    return results
