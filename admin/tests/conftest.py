from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample():
    """Path to a real report in the project root; skips when it is absent (CI has none)."""

    def get(name: str) -> Path:
        """`name` may be a glob pattern (sample file names carry people's names we keep out of the code)."""
        found = sorted(SAMPLES_DIR.glob(name))
        if not found:
            pytest.skip(f"sample report not available: {name}")
        return found[0]

    return get


@pytest.fixture(autouse=True)
def npsr_home(tmp_path, monkeypatch):
    home = tmp_path / "npsr_home"
    monkeypatch.setenv("NPSR_HOME", str(home))
    return home
