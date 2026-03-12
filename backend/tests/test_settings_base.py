from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


def load_base_settings_module() -> ModuleType:
    sys.modules.pop("config.settings.base", None)
    return importlib.import_module("config.settings.base")


def test_env_required_rejects_whitespace_only_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import base

    monkeypatch.setenv("REQUIRED_VALUE", "   ")

    with pytest.raises(RuntimeError, match="Environment variable 'REQUIRED_VALUE' is required"):
        base.env_required("REQUIRED_VALUE")


@pytest.mark.parametrize("settings_module", ["config.settings.uat", "config.settings.prod"])
@pytest.mark.parametrize(
    ("missing_key", "expected_message"),
    [
        ("DJANGO_SECRET_KEY", "Environment variable 'DJANGO_SECRET_KEY' is required"),
        ("POSTGRES_DB", "Environment variable 'POSTGRES_DB' is required"),
        ("POSTGRES_USER", "Environment variable 'POSTGRES_USER' is required"),
        ("POSTGRES_PASSWORD", "Environment variable 'POSTGRES_PASSWORD' is required"),
    ],
)
def test_non_dev_settings_require_critical_secrets_and_database_credentials(
    monkeypatch: pytest.MonkeyPatch, settings_module: str, missing_key: str, expected_message: str
) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", settings_module)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "non-dev-secret")
    monkeypatch.setenv("POSTGRES_DB", "dle_saas")
    monkeypatch.setenv("POSTGRES_USER", "dle_saas")
    monkeypatch.setenv("POSTGRES_PASSWORD", "non-dev-password")
    monkeypatch.setenv("POSTGRES_HOST", "db")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv(missing_key, "   ")

    with pytest.raises(RuntimeError, match=expected_message):
        load_base_settings_module()
