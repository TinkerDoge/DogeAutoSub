from modules.theme_tokens import TOKENS, build_stylesheet


def test_tokens_has_both_themes():
    assert "light" in TOKENS
    assert "dark" in TOKENS


def test_token_keys_match_across_themes():
    assert set(TOKENS["light"].keys()) == set(TOKENS["dark"].keys())


def test_required_tokens_present():
    required = {
        "chrome_bg", "interior_bg", "card_bg", "card_border",
        "title_bar_start", "title_bar_end", "desktop_bg",
        "text_primary", "text_secondary", "text_muted",
        "accent_primary", "accent_success", "accent_warn", "accent_error",
    }
    for theme in ("light", "dark"):
        missing = required - set(TOKENS[theme].keys())
        assert not missing, f"{theme} missing: {missing}"


def test_build_stylesheet_returns_non_empty_string():
    css = build_stylesheet("light")
    assert isinstance(css, str)
    assert len(css) > 500
    assert "QMainWindow" in css


def test_build_stylesheet_substitutes_tokens():
    css = build_stylesheet("light")
    assert TOKENS["light"]["chrome_bg"] in css
    assert TOKENS["light"]["title_bar_start"] in css


def test_build_stylesheet_unknown_theme_raises():
    import pytest
    with pytest.raises(KeyError):
        build_stylesheet("solarized")
