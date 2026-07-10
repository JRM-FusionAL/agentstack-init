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

_MCP_CONFIG_HERMES = """\
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
        return _MCP_CONFIG_HERMES
    else:
        raise ValueError(f"Unsupported harness: {harness_name}")
