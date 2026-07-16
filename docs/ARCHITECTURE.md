# agentstack-init — Architecture

> **Lead-magnet CLI + MCP server** for auditing and scaffolding AI harness configs
> (Claude Code, Hermes Agent). Part of the [FusionAL](https://fusional.dev) ecosystem.

---

## Table of Contents

- [Overview](#overview)
- [Package Layout](#package-layout)
- [CLI Commands](#cli-commands)
  - [`audit`](#audit)
  - [`init`](#init)
  - [`update-check`](#update-check)
- [MCP Server](#mcp-server)
- [Harness Detection](#harness-detection)
- [Harness Auditing](#harness-auditing)
- [Scaffolding](#scaffolding)
- [Baseline / Drift Tracking](#baseline--drift-tracking)
- [Output Artifacts](#output-artifacts)
- [Data Flow](#data-flow)
- [Testing Strategy](#testing-strategy)
- [Configuration Schema Reference](#configuration-schema-reference)

---

## Overview

`agentstack-init` is a dual-mode tool:

1. **CLI** (entry point: `agentstack-init`) — three commands for auditing, scaffolding,
   and drift-tracking AI harness configurations.
2. **MCP server** — exposes the same audit/scaffold functions as MCP tools over SSE
   on port 8200, so agents can use them programmatically.

It is a lead magnet for [FusionAL](https://fusional.dev) agentstack consulting. Every
command output includes the CTA: *"Book a free 30-min review: fusional.dev/agentstack"*.

**Tech stack:** Python 3.12+, [Typer](https://typer.tiangolo.com/) for CLI,
[FastMCP](https://github.com/jlowin/fastmcp) for MCP server, [Jinja2](https://jinja.palletsprojects.com/)
for templates, [httpx](https://www.python-httpx.org/) for reachability checks,
[pyyaml](https://pyyaml.org/) for YAML config parsing.

---

## Package Layout

```
src/agentstack_init/
├── __init__.py              # Version: 0.1.0
├── cli.py                   # Typer app — three CLI commands
├── server.py                # FastMCP server — four MCP tools
└── harness/
    ├── __init__.py           # Empty
    ├── detect.py             # detect_harness() — discover installed harnesses
    ├── audit.py              # audit_harness() — inspect config health
    └── scaffold.py           # Scaffolding templates and generators

docs/
└── ARCHITECTURE.md           # This file

tests/
├── conftest.py               # Fixtures: tmp_home, fake_claude_dir, fake_hermes_dir
├── test_cli.py               # CLI integration tests (init, audit, update-check)
├── test_audit.py             # Audit logic unit tests
└── test_detect.py            # Detection logic unit tests
```

---

## CLI Commands

All three commands respect a `--project-dir` option (default `.`) and write output
to `<project-dir>/.fusional/`.

### `audit`

```
agentstack-init audit [--harness claude_code|hermes] [--project-dir <path>]
```

1. Calls `detect_harness()` to find installed harnesses on the system.
2. Matches the requested harness by name; if not found, prints a CTA and exits.
3. Calls `audit_harness()` — inspects the harness config directory for:
   - **Claude Code:** missing `CLAUDE.md`, missing MCP servers (checks `.mcp.json`,
     `~/.claude.json` user-scoped and project-scoped), unreachable server URLs.
   - **Hermes:** missing or unreadable `~/.hermes/config.yaml`, missing MCP servers
     (checks `mcp_servers` top-level mapping and legacy `mcp.servers` list).
4. Prints issues with severity symbols (`✗` error, `⚠` warning) and remediation.
5. Prints a **score** out of 100 (error = −20, warning = −5, floor 0).
6. Writes `audit-report.json` to `.fusional/`.

### `init`

```
agentstack-init init [--harness claude_code|hermes] [--project-name <name>] [--project-dir <path>]
```

Generates scaffold files into `.fusional/`:

| File | Contents |
|---|---|
| `CLAUDE.md` | Project guide with memory, harness info, dev commands, rules |
| `mcp-config.json` | For Claude Code: `mcpServers.agentstack` pointing to local MCP |
| `mcp-config.yaml` | For Hermes: `mcp.servers` list (JSON also emitted) |
| `memory-setup.md` | Quickstart for connecting FusionAL-Recall MCP memory |

Optional `--project-name` defaults to the directory basename.

### `update-check`

```
agentstack-init update-check [--project-dir <path>] [--set-baseline]
```

Tracks version drift of installed harnesses:

1. Calls `detect_harness()` to get current `{name: version}` pairs.
2. Reads `.fusional/known-good.json` (if it exists).
3. **First run** (no baseline): records current versions as known-good baseline.
4. **`--set-baseline`:** overwrites the stored baseline with current versions.
5. **Normal run:** compares each harness version to the baseline and reports drift.

---

## MCP Server

```
agentstack-init serve    # via systemd unit; runs on 0.0.0.0:8200
```

Uses `FastMCP` with SSE transport. Exposes four tools — thin wrappers over the
`harness/` module:

| MCP Tool | Wraps | Returns |
|---|---|---|
| `detect_harness(project_dir)` | `detect.detect_harness()` | `{harnesses: [{name, version, config_root, known_issues}]}` |
| `audit_harness(config_dir, harness_name, project_dir)` | `audit.audit_harness()` | `AuditReport` dict (score, issues) |
| `scaffold_claude_md(harness_name, project_name)` | `scaffold.scaffold_claude_md()` | Rendered markdown string |
| `scaffold_mcp_config(harness_name)` | `scaffold.scaffold_mcp_config()` | JSON or YAML string |

Configured via environment variables `AGENTSTACK_HOST` (default `0.0.0.0`) and
`AGENTSTACK_PORT` (default `8200`). Uses `python-dotenv` to load `.env`.

---

## Harness Detection

File: `src/agentstack_init/harness/detect.py`

```python
def detect_harness(project_dir: Path) -> list[HarnessInfo]
```

Scans the user's home directory for installed harnesses:

| Harness | Detection Signal | Version Source | Config Root |
|---|---|---|---|
| `claude_code` | `~/.claude/` exists | `claude --version` CLI | `~/.claude/` |
| `hermes` | `~/.hermes/config.yaml` exists | `hermes --version` CLI (fallback: `version` key in YAML) | `~/.hermes/` |

`HarnessInfo` is a dataclass: `name, version, config_root, known_issues`.

Version extraction uses regex `v?(\d+\.\d+(?:\.\d+)?)` on CLI stdout.
If the CLI binary is absent or the version key is missing, the version is `None`.

---

## Harness Auditing

File: `src/agentstack_init/harness/audit.py`

### Audit Models

```python
@dataclass
class AuditIssue:
    severity: str    # "error" | "warning"
    code: str        # Machine-readable identifier
    message: str     # Human-readable description
    fix: str         # Remediation instruction

@dataclass
class AuditReport:
    harness: str
    issues: list[AuditIssue]
    score: int       # 100 minus errors*20 minus warnings*5 (floor 0)
```

### Claude Code Audit (`_audit_claude_code`)

Checks, in order:

1. **`CLAUDE.md`** exists at project root — error `MISSING_CLAUDE_MD` if missing.
2. **MCP servers**, collected from three locations (merged in precedence order):
   - `<project>/.mcp.json` (`mcpServers`) — project-local override.
   - `~/.claude.json` (`mcpServers`) — user-wide config.
   - `~/.claude.json` (`projects[<abs_project_path>].mcpServers`) — per-project
     user config.
   - Error `MISSING_MCP_CONFIG` if the merged result is empty.
3. **Server reachability** — for each HTTP-based server (`url` starts with `http`),
   issues a `httpx.get(url, timeout=2.0)`. Error `MCP_SERVER_UNREACHABLE` on failure.

**Important:** The legacy path `~/.claude/claude_mcp_settings.json` is *not* checked
— Claude Code stopped reading it years ago.

### Hermes Audit (`_audit_hermes`)

1. Load `~/.hermes/config.yaml`. Error `UNREADABLE_CONFIG` if missing or parse error.
2. Extract servers from:
   - **New schema:** `mcp_servers` — top-level dict (Hermes ≥ 0.15, `_config_version: 33`).
   - **Legacy schema:** `mcp.servers` — list under a nested `mcp` key.
   - Error `MISSING_MCP_CONFIG` if both are empty.

---

## Scaffolding

File: `src/agentstack_init/harness/scaffold.py`

### `scaffold_claude_md(harness_name, project_name) -> str`

Renders a Jinja2 template. Two variants:

- **claude_code:** CLAUDE.md with `recall`/`remember` memory commands, dev command
  placeholder, and reading/editing rules.
- **hermes:** Same structure, but dev commands show `hermes` CLI and `hermes gateway`
  for Telegram/Discord.

### `scaffold_mcp_config(harness_name) -> str`

Returns a pre-built config block:

- **claude_code:** JSON with `mcpServers.agentstack.url: http://localhost:8200/mcp`.
- **hermes:** YAML with `mcp.servers[0]` pointing to the same URL.

The actual printed format for the `init` command is:
- Claude Code: writes `mcp-config.json` (JSON).
- Hermes: writes both `mcp-config.yaml` (YAML) and `mcp-config.json` (parsed/converted).

---

## Baseline / Drift Tracking

Managed by the `update-check` command and stored in `.fusional/known-good.json`.

```json
{
  "harnesses": {
    "claude_code": "2.1.191",
    "hermes": "0.18.2"
  },
  "recorded": "2026-07-13T13:12:26"
}
```

Logic:

- **No baseline file:** auto-record current versions as known-good.
- **`--set-baseline` flag:** overwrite stored baseline unconditionally.
- **Normal run:** compare `current[name]` vs `baseline[name]`. Report drift if
  versions differ or a harness is missing from the baseline.
- After drift is flagged, the user is prompted to re-audit then accept the new
  versions with `--set-baseline`.

---

## Output Artifacts

All artifacts are written to `.fusional/` (gitignored per the project `.gitignore`):

| File | Created By | Format | Contents |
|---|---|---|---|
| `CLAUDE.md` | `init` | Markdown | Project-specific agent instructions |
| `mcp-config.json` | `init` | JSON | `mcpServers.agentstack` URL config |
| `mcp-config.yaml` | `init` (Hermes) | YAML | Hermes `mcp.servers` config |
| `memory-setup.md` | `init` | Markdown | FusionAL-Recall MCP quickstart |
| `audit-report.json` | `audit` | JSON | Full `AuditReport` with score and issues |
| `known-good.json` | `update-check` | JSON | Harness version baseline for drift detection |

---

## Data Flow

```
User runs: agentstack-init audit --harness claude_code
                               │
                    ┌──────────▼──────────┐
                    │  detect_harness()    │  ← scans ~/.claude/, ~/.hermes/
                    │  returns [HarnessInfo]│
                    └──────────┬──────────┘
                               │ match by name
                    ┌──────────▼──────────┐
                    │  audit_harness()     │  ← inspects config files, checks
                    │  returns AuditReport │     MCP server reachability
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   Print issues         Print score         Write .fusional/
   (stderr/TTY)         (stderr/TTY)        audit-report.json
```

```
User runs: agentstack-init init --harness claude_code
                               │
                    ┌──────────▼──────────┐
                    │  scaffold_claude_md()│  ← Jinja2 render of CLAUDE.md
                    │  scaffold_mcp_config()│ ← pre-built JSON/YAML block
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  .fusional/         │
                    │  ├── CLAUDE.md      │
                    │  ├── mcp-config.json│
                    │  └── memory-setup.md│
                    └─────────────────────┘
```

---

## Testing Strategy

**Framework:** pytest 8+ with `pytest-asyncio` and `pytest-cov`.

**Fixtures** (`tests/conftest.py`):

| Fixture | Purpose |
|---|---|
| `tmp_home` | Monkey-patches `Path.home()` to a temp dir — tests never touch real `~/.claude` or `~/.hermes` |
| `fake_claude_dir` | Creates `~/.claude/` (empty) |
| `fake_hermes_dir` | Creates `~/.hermes/config.yaml` with legacy schema |

**Test files:**

| File | Tests | Count |
|---|---|---|
| `test_cli.py` | Integration tests via Typer `CliRunner` | 14 |
| `test_audit.py` | Audit logic edge cases (missing files, empty config, both schemas) | 13 |
| `test_detect.py` | Detection of zero/one/both harnesses, version extraction from CLI/config | 8 |

**Key coverage areas:**
- Version extraction from CLI output (multiple harness formats).
- Config schema compatibility — Hermes new (`mcp_servers`) vs legacy (`mcp.servers`).
- Three Claude Code MCP config sources (`.mcp.json`, `~/.claude.json` user-scoped,
  `~/.claude.json` project-scoped).
- Score computation (errors, warnings, empty issues).
- Baseline drift detection (no baseline, matching baseline, drifted, set-baseline).
- Serialisation of `AuditReport` to dict and JSON.

---

## Configuration Schema Reference

### Claude Code — MCP Config Sources (merged in this order)

1. `<project>/.mcp.json`
   ```json
   { "mcpServers": { "<name>": { "command": "...", "args": [...] } } }
   ```
2. `~/.claude.json` (user-wide)
   ```json
   { "mcpServers": { "<name>": { "url": "..." } } }
   ```
3. `~/.claude.json` (per-project)
   ```json
   {
     "projects": {
       "/abs/path/to/project": {
         "mcpServers": { "<name>": { ... } }
       }
     }
   }
   ```

### Hermes — Config Schema (new style, ≥ 0.15)

File: `~/.hermes/config.yaml`

```yaml
_config_version: 33
mcp_servers:
  fusional-recall:
    url: http://localhost:9107/mcp
    # or: command: uvx
    #      args: [fusional-recall]
```

### Hermes — Config Schema (legacy, < 0.15)

```yaml
version: 0.15
mcp:
  servers:
    - name: agentstack
      url: http://localhost:8200/mcp
```
