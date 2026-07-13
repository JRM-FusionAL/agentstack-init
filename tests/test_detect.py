import subprocess

import pytest

from pathlib import Path
from agentstack_init.harness import detect as detect_mod
from agentstack_init.harness.detect import detect_harness, HarnessInfo


def _fake_cli(output: str):
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=output, stderr="")
    return run


def _no_cli(cmd, **kwargs):
    raise FileNotFoundError(cmd[0])


@pytest.fixture(autouse=True)
def cli_absent(monkeypatch):
    """Default every test to a machine without harness CLIs; version tests override."""
    monkeypatch.setattr(detect_mod.subprocess, "run", _no_cli)


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


def test_claude_code_version_from_cli(fake_claude_dir, tmp_home, monkeypatch):
    monkeypatch.setattr(detect_mod.subprocess, "run", _fake_cli("2.1.191 (Claude Code)\n"))
    result = detect_harness(tmp_home)
    claude = next(h for h in result if h.name == "claude_code")
    assert claude.version == "2.1.191"


def test_claude_code_version_none_when_cli_missing(fake_claude_dir, tmp_home):
    result = detect_harness(tmp_home)
    claude = next(h for h in result if h.name == "claude_code")
    assert claude.version is None


def test_hermes_version_from_cli(fake_hermes_dir, tmp_home, monkeypatch):
    # Real Hermes configs carry no `version` key (only `_config_version`);
    # the agent version comes from the CLI.
    (fake_hermes_dir / "config.yaml").write_text("_config_version: 33\nmcp_servers: {}\n")
    monkeypatch.setattr(
        detect_mod.subprocess, "run",
        _fake_cli("Hermes Agent v0.18.2 (2026.7.7.2) · upstream 7b5ba205\n"),
    )
    result = detect_harness(tmp_home)
    hermes = next(h for h in result if h.name == "hermes")
    assert hermes.version == "0.18.2"


def test_hermes_version_falls_back_to_config_key(fake_hermes_dir, tmp_home):
    # Legacy configs with an explicit version key still parse when no CLI exists.
    result = detect_harness(tmp_home)
    hermes = next(h for h in result if h.name == "hermes")
    assert hermes.version == "0.15"


def test_hermes_version_none_when_no_source(fake_hermes_dir, tmp_home):
    (fake_hermes_dir / "config.yaml").write_text("_config_version: 33\nmcp_servers: {}\n")
    result = detect_harness(tmp_home)
    hermes = next(h for h in result if h.name == "hermes")
    assert hermes.version is None


def test_detects_both_harnesses(fake_claude_dir, fake_hermes_dir, tmp_home):
    result = detect_harness(tmp_home)
    names = {h.name for h in result}
    assert names == {"claude_code", "hermes"}
