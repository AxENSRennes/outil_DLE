from __future__ import annotations

import importlib
import re
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


def test_rest_framework_defaults_to_session_authentication_only() -> None:
    from config.settings import base

    assert base.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] == [
        "rest_framework.authentication.SessionAuthentication"
    ]
    assert base.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]


def test_build_test_database_name_uses_explicit_name() -> None:
    from config.settings import base

    assert (
        base.build_test_database_name(
            "dle_saas",
            explicit_name="test_dle_saas_manual",
            generated_suffix="unused",
        )
        == "test_dle_saas_manual"
    )


def test_build_test_database_name_uses_explicit_suffix_and_sanitizes() -> None:
    from config.settings import base

    assert (
        base.build_test_database_name(
            "dle_saas",
            explicit_suffix="agent alpha/1",
            generated_suffix="unused",
        )
        == "test_dle_saas_agent_alpha_1"
    )


def test_build_test_database_name_truncates_to_postgresql_identifier_limit() -> None:
    from config.settings import base

    name = base.build_test_database_name(
        "dle_saas_with_a_name_that_is_far_longer_than_postgresql_would_normally_allow",
        generated_suffix="20260313_233700_123456_48291",
    )

    assert len(name) <= 63
    assert name.endswith("_20260313_233700_123456_4")


def test_default_test_database_suffix_includes_timestamp_and_pid() -> None:
    from config.settings import base

    suffix = base.default_test_database_suffix()

    assert re.fullmatch(r"\d{8}_\d{6}_\d{6}_\d+", suffix) is not None


def test_dev_settings_define_automatic_unique_test_database_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    monkeypatch.delenv("POSTGRES_TEST_DB_NAME", raising=False)
    monkeypatch.delenv("POSTGRES_TEST_DB_SUFFIX", raising=False)

    module = load_base_settings_module()
    test_name = module.DATABASES["default"]["TEST"]["NAME"]

    assert re.fullmatch(r"test_dle_saas_\d{8}_\d{6}_\d{6}_\d+", test_name) is not None


def test_dev_settings_use_explicit_test_database_name_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    monkeypatch.setenv("POSTGRES_TEST_DB_NAME", "test_dle_saas_shared")

    module = load_base_settings_module()

    assert module.DATABASES["default"]["TEST"]["NAME"] == "test_dle_saas_shared"
