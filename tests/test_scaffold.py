import json
import yaml
import pytest
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
    with pytest.raises(ValueError, match="Unsupported harness"):
        scaffold_mcp_config("unknown_harness")
