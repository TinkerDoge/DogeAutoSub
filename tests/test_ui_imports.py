import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_ui_module_imports():
    from modules import ui_DogeAutoSub
    assert hasattr(ui_DogeAutoSub, "Ui_MainWindow")


def test_ui_class_has_setupui():
    from modules.ui_DogeAutoSub import Ui_MainWindow
    assert callable(Ui_MainWindow.setupUi)


def test_required_widgets_present_after_setupUi(app):
    from PySide6.QtWidgets import QMainWindow
    from modules.ui_DogeAutoSub import Ui_MainWindow
    win = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(win)

    required = [
        "startButton", "progressBar", "statusLabel", "etaLabel",
        "filePathLabel", "source_language_dropdown", "target_language_dropdown",
        "target_engine", "boostSlider", "boostLabel",
        "bearerTokenEdit", "getTokenBtn",
        "themeBtn", "openFolderBtn",
        "selectFileBtn", "selectOutputBtn",
        "model_size_dropdown",
        # New widgets
        "sidebar", "sidebarSubtitlesItem", "sidebarNotesItem", "sidebarTranslateItem",
        "phaseStrip", "paletteMenuButton", "paletteStripe",
        "workflowStack", "statusBar", "logPanelHost", "mascotHost",
    ]
    missing = [n for n in required if not hasattr(ui, n)]
    assert not missing, f"missing widgets: {missing}"
