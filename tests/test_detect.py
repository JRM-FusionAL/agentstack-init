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
