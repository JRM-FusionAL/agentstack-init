from __future__ import annotations

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


def detect_harness(project_dir: Path) -> list[HarnessInfo]:
    results: list[HarnessInfo] = []
    home = Path.home()

    claude_dir = home / ".claude"
    if claude_dir.exists():
        results.append(HarnessInfo(
            name="claude_code",
            version=None,
            config_root=claude_dir,
            known_issues=[],
        ))

    hermes_config = home / ".hermes" / "config.yaml"
    if hermes_config.exists():
        try:
            raw = yaml.safe_load(hermes_config.read_text()) or {}
        except yaml.YAMLError:
            raw = {}
        version = raw.get("version")
        results.append(HarnessInfo(
            name="hermes",
            version=str(version) if version is not None else None,
            config_root=hermes_config.parent,
            known_issues=[],
        ))

    return results
