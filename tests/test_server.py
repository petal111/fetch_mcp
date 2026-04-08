# tests/test_server.py
import pytest
from mcp_server_fetch.server import FetchParams


def test_fetch_params_defaults():
    params = FetchParams(url="https://example.com")
    assert str(params.url) == "https://example.com/"
    assert params.max_length == 5000
    assert params.start_index == 0
    assert params.raw is False
    assert params.force_browser is False


def test_fetch_params_custom():
    params = FetchParams(
        url="https://example.com",
        max_length=1000,
        start_index=500,
        raw=True,
        force_browser=True,
    )
    assert params.max_length == 1000
    assert params.start_index == 500
    assert params.raw is True
    assert params.force_browser is True


def test_fetch_params_invalid_url():
    with pytest.raises(Exception):
        FetchParams(url="not-a-url")
