import pytest

from modules.theme_tokens import PALETTES, build_stylesheet, SHARED_TOKENS


PALETTE_IDS = {"atari", "rainbow", "crt", "famicom"}


def test_palettes_has_all_four():
    assert set(PALETTES.keys()) == PALETTE_IDS


def test_each_palette_has_required_keys():
    required = {"name", "stripe", "accent", "accent_text"}
    for pid in PALETTE_IDS:
        missing = required - set(PALETTES[pid].keys())
        assert not missing, f"{pid} missing: {missing}"


def test_stripe_has_at_least_three_bands():
    for pid in PALETTE_IDS:
        assert len(PALETTES[pid]["stripe"]) >= 3, pid


def test_atari_is_default_first_in_dict():
    assert next(iter(PALETTES.keys())) == "atari"


def test_shared_tokens_present():
    required = {
        "desktop_bg", "window_bg", "sidebar_bg", "titlebar_bg", "input_bg",
        "border", "text_primary", "text_secondary", "text_tertiary",
        "error",
    }
    missing = required - set(SHARED_TOKENS.keys())
    assert not missing


def test_build_stylesheet_returns_long_string_per_palette():
    for pid in PALETTE_IDS:
        css = build_stylesheet(pid)
        assert isinstance(css, str)
        assert len(css) > 500
        assert "QMainWindow" in css


def test_build_stylesheet_embeds_accent_color():
    css = build_stylesheet("atari")
    assert PALETTES["atari"]["accent"] in css


def test_build_stylesheet_unknown_palette_raises():
    with pytest.raises(KeyError):
        build_stylesheet("solarized")
