def test_ui_module_imports():
    from modules import ui_DogeAutoSub
    assert hasattr(ui_DogeAutoSub, "Ui_MainWindow")


def test_ui_class_has_setupui():
    from modules.ui_DogeAutoSub import Ui_MainWindow
    assert callable(Ui_MainWindow.setupUi)
