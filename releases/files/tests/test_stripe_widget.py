import pytest
from PySide6.QtWidgets import QApplication

from modules.stripe_widget import StripeWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_default_palette_is_atari(app):
    s = StripeWidget()
    assert s.palette_id() == "atari"


def test_set_palette_updates_id(app):
    s = StripeWidget()
    s.set_palette("crt")
    assert s.palette_id() == "crt"


def test_unknown_palette_is_ignored(app):
    s = StripeWidget()
    s.set_palette("solarized")
    assert s.palette_id() == "atari"


def test_band_count_matches_palette(app):
    s = StripeWidget()
    s.set_palette("rainbow")  # 6 bands
    assert s.band_count() == 6
    s.set_palette("atari")    # 4 bands
    assert s.band_count() == 4
