# agentstack-init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an open-source MCP server + CLI scaffolder that audits and repairs broken AI harness configs (Claude Code, Hermes), feeding leads into a $4K–10K consulting funnel.

**Architecture:** A Python package with two entry points — a FastMCP server exposing 4 tools (`detect_harness`, `audit_harness`, `scaffold_claude_md`, `scaffold_mcp_config`) and a Typer CLI (`agentstack-init init` / `audit` / `update-check`) that calls those same functions. The CLI writes output to `.fusional/` in the project directory; the MCP server exposes the same logic to any MCP-capable harness.

**Tech Stack:** Python 3.12, hatchling, `mcp[cli]` + FastMCP (same as FusionAL-Recall), Typer, PyYAML, Jinja2, httpx, pytest + pytest-asyncio, ruff

## Global Constraints

- Python ≥ 3.12 (`python3.12 -m venv` always; never bare `python3`)
- `mcp.server.fastmcp.FastMCP` import path (matches FusionAL-Recall)
- hatchling build backend (matches FusionAL-Recall)
- All tests in `tests/`; run with `pytest`
- ruff line-length 100, target py312
- No auto-write to system directories in v1 — generated files go to `.fusional/` only
- MIT license

---

## File Map

```
agentstack-init/
  src/agentstack_init/
    __init__.py              ← version constant
    harness/
      __init__.py
      detect.py             ← detect_harness() — finds Claude Code + Hermes installs
      audit.py              ← audit_harness() — checks config completeness + MCP reachability
      scaffold.py           ← scaffold_claude_md(), scaffold_mcp_config() — Jinja2 rendering
    server.py               ← FastMCP server wiring all 4 tools
    cli.py                  ← Typer app: init, audit, update-check commands
  tests/
    conftest.py             ← shared fixtures (tmp_home, fake_claude_dir, fake_hermes_dir)
    test_detect.py
    test_audit.py
    test_scaffold.py
    test_server.py
    test_cli.py
  pyproject.toml
  .env.example
```

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/agentstack_init/__init__.py`
- Create: `src/agentstack_init/harness/__init__.py`
- Create: `.env.example`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: installable package `agentstack-init`; entry point `agentstack-init` CLI; `pytest` runs green on empty suite

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentstack-init"
version = "0.1.0"
description = "Audit and scaffold AI harness configs (Claude Code, Hermes) — lead magnet for agentstack consulting"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "Jonathan Melton" }]
requires-python = ">=3.12"
dependencies = [
    "mcp[cli]>=1.1.0",
    "typer>=0.12.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "uvicorn>=0.29.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
]

[project.scripts]
agentstack-init = "agentstack_init.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/agentstack_init"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

- [ ] **Step 2: Create package init**

`src/agentstack_init/__init__.py`:
```python
__version__ = "0.1.0"
```

`src/agentstack_init/harness/__init__.py`:
```python
```

- [ ] **Step 3: Create `.env.example`**

```
# MCP server host/port (used when running as a server)
AGENTSTACK_HOST=0.0.0.0
AGENTSTACK_PORT=8200
```

- [ ] **Step 4: Create `tests/conftest.py`**

```python
import pytest
from pathlib import Path


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Redirect Path.home() to a temp directory so tests never touch real ~/.claude or ~/.hermes."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def fake_claude_dir(tmp_home):
    """Create a minimal ~/.claude directory."""
    d = tmp_home / ".claude"
    d.mkdir()
    return d


@pytest.fixture
def fake_hermes_dir(tmp_home):
    """Create a minimal ~/.hermes directory with a valid config.yaml."""
    d = tmp_home / ".hermes"
    d.mkdir()
    (d / "config.yaml").write_text("version: 0.15\nmcp:\n  servers: []\n")
    return d
```

- [ ] **Step 5: Create venv and install**

```bash
cd ~/Projects/agentstack-init
python3.12 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

- [ ] **Step 6: Run pytest to confirm empty suite passes**

```bash
pytest
```

Expected: `no tests ran` (exit 0, or `collected 0 items`)

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml src/ tests/ .env.example
git commit -m "feat: initial project scaffold"
```

---

### Task 2: Harness detection

**Files:**
- Create: `src/agentstack_init/harness/detect.py`
- Create: `tests/test_detect.py`

**Interfaces:**
- Produces: `detect_harness(project_dir: Path) -> list[HarnessInfo]`
- `HarnessInfo` dataclass: `name: str`, `version: str | None`, `config_root: Path`, `known_issues: list[str]`

- [ ] **Step 1: Write failing tests**

`tests/test_detect.py`:
```python
from pathlib import Path
from agentstack_init.harness.detect import detect_harness, HarnessInfo


def test_returns_empty_when_no_harness(tmp_home):
    result = detect_harness(tmp_home)
    assert result == []


def test_detects_claude_code_when_dir_exists(fake_claude_dir, tmp_home):
    result = detect_harness(tmp_home)
    assert len(result) == 1
    assert result[0].name == "claude_code"
    assert result[0].config_root == fake_claude_dir


def test_detects_hermes_when_config_exists(fake_hermes_dir, tmp_home):
    result = detect_harness(tmp_home)
    assert any(h.name == "hermes" for h in result)


def test_hermes_version_parsed(fake_hermes_dir, tmp_home):
    result = detect_harness(tmp_home)
    hermes = next(h for h in result if h.name == "hermes")
    assert hermes.version == "0.15"


def test_detects_both_harnesses(fake_claude_dir, fake_hermes_dir, tmp_home):
    result = detect_harness(tmp_home)
    names = {h.name for h in result}
    assert names == {"claude_code", "hermes"}
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_detect.py -v
```

Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Implement `detect.py`**

`src/agentstack_init/harness/detect.py`:
```python
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
            version=None,  # Claude Code doesn't expose a version file
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_detect.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/agentstack_init/harness/detect.py tests/test_detect.py tests/conftest.py
git commit -m "feat: harness detection for claude_code and hermes"
```

---

### Task 3: Audit logic

**Files:**
- Create: `src/agentstack_init/harness/audit.py`
- Create: `tests/test_audit.py`

**Interfaces:**
- Consumes: `HarnessInfo` from `detect.py`
- Produces: `audit_harness(config_dir: Path, harness_name: str, project_dir: Path) -> AuditReport`
- `AuditIssue` dataclass: `severity: str`, `code: str`, `message: str`, `fix: str`
- `AuditReport` dataclass: `harness: str`, `issues: list[AuditIssue]`, `score: int`, `to_dict() -> dict`

- [ ] **Step 1: Write failing tests**

`tests/test_audit.py`:
```python
import json
from pathlib import Path
from agentstack_init.harness.audit import audit_harness, AuditReport, AuditIssue


def test_flags_missing_claude_md(fake_claude_dir, tmp_path):
    # project_dir has no CLAUDE.md
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    codes = {i.code for i in report.issues}
    assert "MISSING_CLAUDE_MD" in codes


def test_no_claude_md_issue_when_present(fake_claude_dir, tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project\n")
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    codes = {i.code for i in report.issues}
    assert "MISSING_CLAUDE_MD" not in codes


def test_flags_missing_mcp_config_claude(fake_claude_dir, tmp_path):
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    codes = {i.code for i in report.issues}
    assert "MISSING_MCP_CONFIG" in codes


def test_no_mcp_issue_when_config_present(fake_claude_dir, tmp_path):
    (fake_claude_dir / "claude_mcp_settings.json").write_text('{"mcpServers": {}}')
    (tmp_path / "CLAUDE.md").write_text("# Project\n")
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    codes = {i.code for i in report.issues}
    assert "MISSING_MCP_CONFIG" not in codes


def test_score_100_when_no_issues(fake_claude_dir, tmp_path):
    (fake_claude_dir / "claude_mcp_settings.json").write_text('{"mcpServers": {}}')
    (tmp_path / "CLAUDE.md").write_text("# Project\n")
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    assert report.score == 100


def test_score_decreases_with_errors(fake_claude_dir, tmp_path):
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    assert report.score < 100


def test_flags_missing_mcp_config_hermes(fake_hermes_dir, tmp_path):
    report = audit_harness(fake_hermes_dir, "hermes", tmp_path)
    codes = {i.code for i in report.issues}
    assert "MISSING_MCP_CONFIG" in codes


def test_hermes_no_issue_when_servers_present(fake_hermes_dir, tmp_path):
    (fake_hermes_dir / "config.yaml").write_text(
        "version: 0.15\nmcp:\n  servers:\n    - name: recall\n      url: http://localhost:8107/mcp\n"
    )
    report = audit_harness(fake_hermes_dir, "hermes", tmp_path)
    codes = {i.code for i in report.issues}
    assert "MISSING_MCP_CONFIG" not in codes


def test_to_dict_is_serialisable(fake_claude_dir, tmp_path):
    report = audit_harness(fake_claude_dir, "claude_code", tmp_path)
    d = report.to_dict()
    json.dumps(d)  # must not raise
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_audit.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `audit.py`**

`src/agentstack_init/harness/audit.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_audit.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/agentstack_init/harness/audit.py tests/test_audit.py
git commit -m "feat: harness audit logic for claude_code and hermes"
```

---

### Task 4: Scaffold generation

**Files:**
- Create: `src/agentstack_init/harness/scaffold.py`
- Create: `tests/test_scaffold.py`

**Interfaces:**
- Produces:
  - `scaffold_claude_md(harness_name: str, project_name: str) -> str` — returns rendered CLAUDE.md content
  - `scaffold_mcp_config(harness_name: str) -> str` — returns ready-to-paste config block as a string

- [ ] **Step 1: Write failing tests**

`tests/test_scaffold.py`:
```python
import json
import yaml
from agentstack_init.harness.scaffold import scaffold_claude_md, scaffold_mcp_config


def test_claude_md_contains_project_name():
    result = scaffold_claude_md("claude_code", "my-project")
    assert "my-project" in result


def test_claude_md_contains_memory_section():
    result = scaffold_claude_md("claude_code", "my-project")
    assert "recall" in result.lower()


def test_claude_md_hermes_variant():
    result = scaffold_claude_md("hermes", "my-project")
    assert "my-project" in result
    assert "hermes" in result.lower() or "recall" in result.lower()


def test_mcp_config_claude_code_is_valid_json():
    result = scaffold_mcp_config("claude_code")
    parsed = json.loads(result)
    assert "mcpServers" in parsed


def test_mcp_config_claude_code_includes_agentstack():
    result = scaffold_mcp_config("claude_code")
    parsed = json.loads(result)
    assert "agentstack" in parsed["mcpServers"]


def test_mcp_config_hermes_is_valid_yaml():
    result = scaffold_mcp_config("hermes")
    parsed = yaml.safe_load(result)
    assert "mcp" in parsed
    servers = parsed["mcp"]["servers"]
    assert any(s["name"] == "agentstack" for s in servers)


def test_unknown_harness_raises():
    import pytest
    with pytest.raises(ValueError, match="Unsupported harness"):
        scaffold_mcp_config("unknown_harness")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_scaffold.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `scaffold.py`**

`src/agentstack_init/harness/scaffold.py`:
```python
from __future__ import annotations

import json

from jinja2 import Environment

_CLAUDE_MD_TEMPLATE = """\
# {{ project_name }}

## Memory

This project uses agentstack memory (FusionAL-Recall at :8107).
- Before debugging: `recall <symptom>`
- After fixing: `remember <what-you-learned>`

## Harness

Configured for: {{ harness_name }}

## Dev Commands

```bash
# add your project-specific commands here
```

## Rules

- Read before editing: always Read a file before modifying it.
- No trailing summaries: don't narrate what you just did.
- Prefer editing over creating new files.
"""

_HERMES_CLAUDE_MD_TEMPLATE = """\
# {{ project_name }}

## Memory (Hermes + FusionAL-Recall)

- Before debugging: use the `recall` MCP tool with the symptom
- After fixing: use the `remember` MCP tool with the solution

## Harness

Configured for: hermes

## Dev Commands

```bash
hermes                # CLI
hermes gateway        # Telegram/Discord
```

## Rules

- Read before editing.
- No trailing summaries.
"""

_MCP_CONFIG_CLAUDE_CODE = {
    "mcpServers": {
        "agentstack": {
            "url": "http://localhost:8200/mcp"
        }
    }
}

_MCP_CONFIG_HERMES_TEMPLATE = """\
mcp:
  servers:
    - name: agentstack
      url: http://localhost:8200/mcp
"""

_env = Environment()


def scaffold_claude_md(harness_name: str, project_name: str) -> str:
    if harness_name == "hermes":
        tmpl = _env.from_string(_HERMES_CLAUDE_MD_TEMPLATE)
    else:
        tmpl = _env.from_string(_CLAUDE_MD_TEMPLATE)
    return tmpl.render(project_name=project_name, harness_name=harness_name)


def scaffold_mcp_config(harness_name: str) -> str:
    if harness_name == "claude_code":
        return json.dumps(_MCP_CONFIG_CLAUDE_CODE, indent=2)
    elif harness_name == "hermes":
        return _MCP_CONFIG_HERMES_TEMPLATE
    else:
        raise ValueError(f"Unsupported harness: {harness_name}")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_scaffold.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/agentstack_init/harness/scaffold.py tests/test_scaffold.py
git commit -m "feat: CLAUDE.md and MCP config scaffold generation"
```

---

### Task 5: MCP server

**Files:**
- Create: `src/agentstack_init/server.py`
- Create: `tests/test_server.py`

**Interfaces:**
- Consumes: `detect_harness`, `audit_harness`, `scaffold_claude_md`, `scaffold_mcp_config`
- Produces: `mcp` FastMCP instance with 4 tools; `main()` entry point runs on `AGENTSTACK_HOST:AGENTSTACK_PORT`

- [ ] **Step 1: Write failing tests**

`tests/test_server.py`:
```python
import pytest
from agentstack_init.server import mcp


def test_server_has_detect_harness_tool():
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}
    assert "detect_harness" in tool_names


def test_server_has_audit_harness_tool():
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}
    assert "audit_harness" in tool_names


def test_server_has_scaffold_claude_md_tool():
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}
    assert "scaffold_claude_md" in tool_names


def test_server_has_scaffold_mcp_config_tool():
    tool_names = {t.name for t in mcp._tool_manager.list_tools()}
    assert "scaffold_mcp_config" in tool_names
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_server.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `server.py`**

`src/agentstack_init/server.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_server.py -v
```

Expected: 4 passed

- [ ] **Step 5: Confirm full suite still passes**

```bash
pytest -v
```

Expected: all previous tests + 4 new = all green

- [ ] **Step 6: Commit**

```bash
git add src/agentstack_init/server.py tests/test_server.py
git commit -m "feat: FastMCP server exposing 4 harness tools"
```

---

### Task 6: CLI (`init`, `audit`, `update-check`)

**Files:**
- Create: `src/agentstack_init/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `detect_harness`, `audit_harness`, `scaffold_claude_md`, `scaffold_mcp_config`
- Produces:
  - `agentstack-init init [--harness NAME] [--project-name NAME]` — writes `.fusional/` to cwd
  - `agentstack-init audit [--harness NAME]` — prints human-readable report + writes `.fusional/audit-report.json`; always prints `→ Book a free 30-min review: agentstack.fyi/audit`
  - `agentstack-init update-check` — checks harness version drift, prints warnings

- [ ] **Step 1: Write failing tests**

`tests/test_cli.py`:
```python
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentstack_init.cli import app

runner = CliRunner()


def test_init_creates_fusional_dir(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj"])
    assert result.exit_code == 0
    assert (tmp_path / ".fusional").is_dir()


def test_init_creates_claude_md(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj"])
    assert (tmp_path / ".fusional" / "CLAUDE.md").exists()


def test_init_creates_mcp_config(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj"])
    assert (tmp_path / ".fusional" / "mcp-config.json").exists()


def test_init_creates_memory_setup(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj"])
    assert (tmp_path / ".fusional" / "memory-setup.md").exists()


def test_audit_creates_report_json(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["audit", "--harness", "claude_code"])
    assert result.exit_code == 0
    report_path = tmp_path / ".fusional" / "audit-report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert "score" in data


def test_audit_prints_cta(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["audit", "--harness", "claude_code"])
    assert "agentstack.fyi/audit" in result.output


def test_audit_prints_issue_symbols(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["audit", "--harness", "claude_code"])
    # Should show ✗ for errors
    assert "✗" in result.output or "✓" in result.output


def test_update_check_runs_without_error(fake_claude_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["update-check"])
    assert result.exit_code == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `cli.py`**

`src/agentstack_init/cli.py`:
```python
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

1. Ensure agentstack MCP server is running:
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


def _ensure_fusional(cwd: Path) -> Path:
    d = cwd / ".fusional"
    d.mkdir(exist_ok=True)
    return d


@app.command()
def init(
    harness: str = typer.Option("claude_code", help="Harness to scaffold: claude_code | hermes"),
    project_name: Optional[str] = typer.Option(None, help="Project name for CLAUDE.md"),
):
    """Detect harness, scaffold CLAUDE.md + MCP config, write to .fusional/"""
    cwd = Path.cwd()
    name = project_name or cwd.name

    out = _ensure_fusional(cwd)

    (out / "CLAUDE.md").write_text(_scaffold_claude_md(harness, name))
    typer.echo(f"✓  .fusional/CLAUDE.md")

    config_content = _scaffold_mcp_config(harness)
    ext = ".json" if harness == "claude_code" else ".yaml"
    (out / f"mcp-config{ext}").write_text(config_content)
    # always write a .json for discoverability
    if ext != ".json":
        import yaml as _yaml
        parsed = _yaml.safe_load(config_content)
        (out / "mcp-config.json").write_text(json.dumps(parsed, indent=2))
    typer.echo(f"✓  .fusional/mcp-config{ext}")

    (out / "memory-setup.md").write_text(_MEMORY_SETUP)
    typer.echo(f"✓  .fusional/memory-setup.md")

    typer.echo(f"\nCopy files from .fusional/ into your {harness} config directory.")
    typer.echo(CTA)


@app.command()
def audit(
    harness: str = typer.Option("claude_code", help="Harness to audit: claude_code | hermes"),
):
    """Run harness-optimizer audit, print report, write .fusional/audit-report.json"""
    cwd = Path.cwd()
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
    cwd = Path.cwd()
    harnesses = _detect_harness(cwd)

    if not harnesses:
        typer.echo("No harnesses detected.")
        raise typer.Exit(0)

    for h in harnesses:
        typer.echo(f"✓  {h.name}: config_root={h.config_root}")
        if h.known_issues:
            for issue in h.known_issues:
                typer.echo(f"   ⚠  {issue}")

    typer.echo("\nAll detected harnesses checked.")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: 8 passed

- [ ] **Step 5: Run full suite**

```bash
pytest -v
```

Expected: all tasks green (target: 26+ tests)

- [ ] **Step 6: Smoke-test the CLI manually**

```bash
agentstack-init --help
agentstack-init init --harness claude_code --project-name smoke-test
ls .fusional/
agentstack-init audit --harness claude_code
```

Expected: `.fusional/` created with CLAUDE.md, mcp-config.json, memory-setup.md; audit prints issues + CTA + writes audit-report.json

- [ ] **Step 7: Commit**

```bash
git add src/agentstack_init/cli.py tests/test_cli.py
git commit -m "feat: CLI commands init, audit, update-check"
```

---

## Appendix: Release Checklist (operational steps)

Run in parallel with code tasks where noted. These are not code tasks — they use existing agents and external services.

### Funnel infrastructure (start immediately — launch-blocking)

- [ ] Register `agentstack.fyi` domain — needed for the CTA URL baked into every audit output; do not wait for code to finish
- [ ] Build landing page — must include: visible starting price ($750 solo session), Calendly embed (audit call), email capture ("get breaking-change alerts"), one-line value prop per tier
- [ ] Set up Calendly (or equivalent) for audit call booking — 30-min slot, no auto-confirm, manual review
- [ ] Write tier one-pager (PDF or landing page section) — solo wired session $750–$1,500 / team $4K–$10K — show before the audit call, not on the call
- [ ] Install Plausible or Fathom on landing page — track `/audit` visits and Calendly embed clicks before any traffic arrives
- [ ] Set up email sending for `--email` flag (Resend or Postmark free tier) — needed for Task 6 follow-up; 1-day integration

### Opensource pipeline (run after Task 6 passes)

- [ ] Run `opensource-forker` agent on `~/Projects/agentstack-init` — strips secrets, internal refs, personal paths
- [ ] Run `opensource-sanitizer` agent — confirm PASS before pushing anything public
- [ ] Run `opensource-packager` agent — generates README, LICENSE (MIT), CONTRIBUTING.md, `setup.sh`

### Launch (after pipeline passes)

- [ ] Create GitHub repo under a standalone org (not JRM-FusionAL) — e.g. `agentstack-init/agentstack-init`
- [ ] Push sanitized + packaged repo
- [ ] Add demo GIF to README — record `agentstack-init audit` run showing broken config output + CTA line
- [ ] Submit to MCP registries **same day as GitHub publish** (highest-intent channel):
  - `awesome-mcp-servers` GitHub list (open a PR)
  - Claude Code plugin marketplace / MCP server directory
  - modelcontextprotocol.io community page
- [ ] Write dev.to post #1: *"Why your Hermes Agent MCP servers aren't connecting (and how to fix it)"* — link to repo
- [ ] Write dev.to post #2: *"Why your Claude Code MCP servers aren't connecting (and how to fix it)"* — link to repo
- [ ] Show HN post (upside, not launch): *"Show HN: agentstack-init – audit and fix broken Claude Code / Hermes MCP configs"* — submit once repo has some stars and at least one dev.to post is live
