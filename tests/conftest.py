import pytest
from pathlib import Path


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Redirect Path.home() to a temp directory so tests never touch real ~/.claude or ~/.hermes."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def fake_claude_dir(tmp_home):
    """Create a minimal ~/.claude directory."""
    d = tmp_home / ".claude"
    d.mkdir()
    return d


@pytest.fixture
def fake_hermes_dir(tmp_home):
    """Create a minimal ~/.hermes directory with a valid config.yaml."""
    d = tmp_home / ".hermes"
    d.mkdir()
    (d / "config.yaml").write_text("version: 0.15\nmcp:\n  servers: []\n")
    return d
