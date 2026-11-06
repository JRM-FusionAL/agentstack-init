# agentstack-init

Audit and scaffold AI harness configs (Claude Code, Hermes Agent) — score your setup out of 100.

Most agent setups fail quietly: a missing permission rule, a drifted path, an MCP server that never connects. `agentstack-init` checks your harness config, tells you what's wrong, and generates a working baseline.

## Install

```bash
pip install agentstack-init
```

Requires Python 3.12+.

## Usage

```bash
agentstack-init audit   # score your current setup out of 100 and list findings
agentstack-init init    # scaffold a baseline harness config
```

## What it does

- **Audit** — inspects your Claude Code / Hermes Agent configuration and reports a score with specific, fixable findings.
- **Scaffold** — generates a starting config from templates so you don't hand-write it.
- **MCP server** — also runs as an MCP server (`agentstack_init.server`) so an agent can audit itself.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for internals.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).

## Need it fixed, not just scored?

Book a free 30-minute review: https://fusional.dev/agentstack
