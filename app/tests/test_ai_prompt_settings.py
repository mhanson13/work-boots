from __future__ import annotations

from app.services.ai_prompt_settings import resolve_ai_prompt_text


def test_resolve_ai_prompt_text_prefers_admin_override() -> None:
    resolved = resolve_ai_prompt_text(
        admin_prompt_text="  Admin prompt override  ",
        env_prompt_text="Env prompt fallback",
        env_legacy_config_used=True,
    )

    assert resolved.prompt_text == "Admin prompt override"
    assert resolved.prompt_source == "admin_config"
    assert resolved.legacy_config_used is False


def test_resolve_ai_prompt_text_uses_env_when_admin_blank() -> None:
    resolved = resolve_ai_prompt_text(
        admin_prompt_text="   ",
        env_prompt_text="  Env prompt fallback  ",
        env_legacy_config_used=True,
    )

    assert resolved.prompt_text == "Env prompt fallback"
    assert resolved.prompt_source == "env"
    assert resolved.legacy_config_used is True


def test_resolve_ai_prompt_text_uses_default_when_all_unset() -> None:
    resolved = resolve_ai_prompt_text(
        admin_prompt_text=None,
        env_prompt_text="  ",
        env_legacy_config_used=False,
    )

    assert resolved.prompt_text == ""
    assert resolved.prompt_source == "default"
    assert resolved.legacy_config_used is False
