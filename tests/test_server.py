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


def test_server_settings_use_configured_address(monkeypatch):
    import importlib
    monkeypatch.setenv("AGENTSTACK_HOST", "127.0.0.1")
    monkeypatch.setenv("AGENTSTACK_PORT", "18200")
    from agentstack_init import server
    importlib.reload(server)
    assert server.mcp.settings.host == "127.0.0.1"
    assert server.mcp.settings.port == 18200


def test_main_passes_only_supported_run_arguments():
    from unittest.mock import patch

    from agentstack_init import server
    with patch.object(server.mcp, "run", autospec=True) as run:
        server.main()
    run.assert_called_once_with(transport="sse")
