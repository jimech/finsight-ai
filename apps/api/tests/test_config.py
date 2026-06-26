import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_cors_origins_include_local_development():
    settings = Settings()
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://localhost:3001" in settings.cors_origins


def test_cors_origins_include_frontend_url(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://finsight.example.com")
    settings = Settings()
    assert "https://finsight.example.com" in settings.cors_origins


def test_cors_origins_normalize_frontend_url_trailing_slash(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://finsight.example.com/")
    settings = Settings()
    assert "https://finsight.example.com" in settings.cors_origins
    assert "https://finsight.example.com/" not in settings.cors_origins


def test_cors_origins_do_not_use_wildcard():
    settings = Settings()
    assert "*" not in settings.cors_origins
