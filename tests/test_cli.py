import json
from pathlib import Path

from typer.testing import CliRunner

from agentstack_init.cli import app

runner = CliRunner()


def test_init_creates_fusional_dir(fake_claude_dir, tmp_path):
    result = runner.invoke(
        app, ["init", "--harness", "claude_code", "--project-name", "test-proj",
              "--project-dir", str(tmp_path)],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert (tmp_path / ".fusional").is_dir()


def test_init_creates_claude_md(fake_claude_dir, tmp_path):
    runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj",
                        "--project-dir", str(tmp_path)],
                  catch_exceptions=False)
    assert (tmp_path / ".fusional" / "CLAUDE.md").exists()


def test_init_creates_mcp_config(fake_claude_dir, tmp_path):
    runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj",
                        "--project-dir", str(tmp_path)],
                  catch_exceptions=False)
    assert (tmp_path / ".fusional" / "mcp-config.json").exists()


def test_init_creates_memory_setup(fake_claude_dir, tmp_path):
    runner.invoke(app, ["init", "--harness", "claude_code", "--project-name", "test-proj",
                        "--project-dir", str(tmp_path)],
                  catch_exceptions=False)
    assert (tmp_path / ".fusional" / "memory-setup.md").exists()


def test_audit_creates_report_json(fake_claude_dir, tmp_path):
    result = runner.invoke(app, ["audit", "--harness", "claude_code", "--project-dir", str(tmp_path)],
                           catch_exceptions=False)
    assert result.exit_code == 0
    report_path = tmp_path / ".fusional" / "audit-report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert "score" in data


def test_audit_prints_cta(fake_claude_dir, tmp_path):
    result = runner.invoke(app, ["audit", "--harness", "claude_code", "--project-dir", str(tmp_path)],
                           catch_exceptions=False)
    assert "agentstack.fyi/audit" in result.output


def test_audit_prints_issue_symbols(fake_claude_dir, tmp_path):
    result = runner.invoke(app, ["audit", "--harness", "claude_code", "--project-dir", str(tmp_path)],
                           catch_exceptions=False)
    assert "✗" in result.output or "✓" in result.output


def test_update_check_runs_without_error(fake_claude_dir, tmp_path):
    result = runner.invoke(app, ["update-check"], catch_exceptions=False)
    assert result.exit_code == 0
