import json
from pathlib import Path
from agentstack_init.harness.audit import audit_harness, AuditReport, AuditIssue


def test_flags_missing_claude_md(fake_claude_dir, tmp_path):
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
