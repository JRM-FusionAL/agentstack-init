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
