# -*- coding: utf-8 -*-
"""DogeAutoSub — dark macOS sidebar UI.

Every existing widget object name is preserved so AutoUI.py and the
worker threads do not need to be rewired. Tabs are gone; the workflow
selection is driven by the sidebar via a QStackedWidget.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QSlider, QStackedWidget, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from modules.phase_strip import PhaseStrip
from modules.stripe_widget import StripeWidget
from modules.palette_menu import PaletteMenuButton


class Ui_MainWindow(object):

    # ── Helpers ──────────────────────────────────────────────────────────
    def _label(self, text, *, small=False):
        lbl = QLabel(text)
        lbl.setFont(self.font_small if small else self.font_body)
        return lbl

    def _section_title(self, text):
        lbl = QLabel(text.upper())
        lbl.setObjectName("sectionTitle")
        return lbl

    def _card(self):
        f = QFrame()
        f.setObjectName("card")
        return f

    def _sidebar_section(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sidebarSectionLabel")
        return lbl

    def _sidebar_item(self, text, object_name):
        btn = QPushButton(text)
        btn.setObjectName("sidebarItem")
        btn.setProperty("data-name", object_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("active", "false")
        return btn

    # ── setupUi ──────────────────────────────────────────────────────────
    def setupUi(self, MainWindow: QMainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 640)
        MainWindow.setMinimumSize(QSize(800, 580))
        MainWindow.setMaximumSize(QSize(1400, 1080))
        MainWindow.setWindowTitle("DogeAutoSub")
        MainWindow.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.font_body = QFont(); self.font_body.setPointSize(10)
        self.font_small = QFont(); self.font_small.setPointSize(9)
        self.font_title = QFont(); self.font_title.setPointSize(11); self.font_title.setBold(True)

        # ── Central widget ───────────────────────────────────────────────
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        outer = QVBoxLayout(self.centralWidget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Title bar ────────────────────────────────────────────────────
        self.fauxTitleBar = QFrame()
        self.fauxTitleBar.setObjectName("fauxTitleBar")
        tb = QHBoxLayout(self.fauxTitleBar)
        tb.setContentsMargins(10, 0, 8, 0)
        tb.setSpacing(8)

        for name, color in (("closeBtn", "#ff5f57"), ("minBtn", "#febc2e"), ("zoomBtn", "#28c840")):
            b = QPushButton()
            b.setObjectName(name)
            b.setFixedSize(12, 12)
            b.setStyleSheet(
                f"QPushButton#{name} {{ background:{color}; border-radius:6px; border:none; }}"
                f"QPushButton#{name}:hover {{ opacity:0.8; }}"
            )
            tb.addWidget(b)
            setattr(self, name, b)

        tb.addSpacing(8)

        self.fauxTitleText = QLabel("DogeAutoSub")
        self.fauxTitleText.setObjectName("fauxTitleText")
        self.fauxTitleText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb.addWidget(self.fauxTitleText, 1)

        self.paletteMenuButton = PaletteMenuButton(self.fauxTitleBar)
        self.paletteMenuButton.setObjectName("paletteMenuButton")
        self.paletteMenuButton.setFixedHeight(20)
        tb.addWidget(self.paletteMenuButton)

        # Legacy buttons kept hidden so AutoUI.py signal connections don't break
        self.themeBtn = QPushButton()
        self.themeBtn.setObjectName("themeBtn")
        self.themeBtn.setVisible(False)
        tb.addWidget(self.themeBtn)

        self.openFolderBtn = QPushButton()
        self.openFolderBtn.setObjectName("openFolderBtn")
        self.openFolderBtn.setVisible(False)
        tb.addWidget(self.openFolderBtn)

        # Legacy menu bar items kept as hidden labels
        self.menuItems = {}
        for name in ("File", "Edit", "View", "Help"):
            lbl = QLabel(name)
            lbl.setObjectName("menuItem")
            lbl.setVisible(False)
            self.menuItems[name] = lbl

        outer.addWidget(self.fauxTitleBar)

        # ── Stripe ──────────────────────────────────────────────────────
        self.paletteStripe = StripeWidget(self.centralWidget)
        outer.addWidget(self.paletteStripe)

        # ── Body: sidebar + main ────────────────────────────────────────
        body = QFrame()
        bodyLay = QHBoxLayout(body)
        bodyLay.setContentsMargins(0, 0, 0, 0)
        bodyLay.setSpacing(0)
        outer.addWidget(body, 1)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(180)
        sLay = QVBoxLayout(self.sidebar)
        sLay.setContentsMargins(8, 8, 8, 8)
        sLay.setSpacing(2)

        sLay.addWidget(self._sidebar_section("WORKFLOWS"))
        self.sidebarSubtitlesItem = self._sidebar_item("Subtitles", "subtitles")
        self.sidebarNotesItem = self._sidebar_item("Meeting Notes", "notes")
        self.sidebarTranslateItem = self._sidebar_item("Translate File", "translate")
        sLay.addWidget(self.sidebarSubtitlesItem)
        sLay.addWidget(self.sidebarNotesItem)
        sLay.addWidget(self.sidebarTranslateItem)

        sLay.addWidget(self._sidebar_section("RECENT"))
        self.recentList = QFrame()
        self.recentListLayout = QVBoxLayout(self.recentList)
        self.recentListLayout.setContentsMargins(0, 0, 0, 0)
        self.recentListLayout.setSpacing(2)
        sLay.addWidget(self.recentList)
        sLay.addStretch(1)
        bodyLay.addWidget(self.sidebar)

        # Main stacked area
        self.workflowStack = QStackedWidget()
        self.workflowStack.setObjectName("workflowStack")
        bodyLay.addWidget(self.workflowStack, 1)

        # Legacy tabWidget kept as hidden so any AutoUI.py tabWidget reference resolves
        self.tabWidget = QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setVisible(False)

        self._build_subtitles_pane()
        self._build_notes_pane()
        self._build_translate_pane()

        # ── Status bar ───────────────────────────────────────────────────
        self.statusBar = QFrame()
        self.statusBar.setObjectName("statusBar")
        self.statusBar.setFixedHeight(22)
        sbLay = QHBoxLayout(self.statusBar)
        sbLay.setContentsMargins(10, 2, 10, 2)
        sbLay.setSpacing(10)
        self.statusBarVersion = QLabel("v—")
        self.statusBarGpu = QLabel("GPU: —")
        self.statusBarReady = QLabel("● Ready")
        for w in (self.statusBarVersion, self.statusBarGpu, self.statusBarReady):
            w.setStyleSheet("font-size:10px;")
        sbLay.addWidget(self.statusBarVersion)
        sbLay.addStretch(1)
        sbLay.addWidget(self.statusBarGpu)
        sbLay.addWidget(self.statusBarReady)
        outer.addWidget(self.statusBar)

        # Wire slider → label
        self.boostSlider.valueChanged.connect(lambda v: self.boostLabel.setText(str(v)))

    # ── Pane builders ─────────────────────────────────────────────────────
    def _build_subtitles_pane(self):
        pane = QWidget()
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # File card
        fileCard = self._card()
        flay = QVBoxLayout(fileCard)
        flay.setContentsMargins(12, 10, 12, 10)
        flay.setSpacing(6)
        flay.addWidget(self._section_title("SOURCE"))
        btnRow = QHBoxLayout()
        self.selectFileBtn = QPushButton("Select Video File")
        self.selectFileBtn.setObjectName("selectFileBtn")
        btnRow.addWidget(self.selectFileBtn, 2)
        self.selectOutputBtn = QPushButton("Output Folder")
        self.selectOutputBtn.setObjectName("selectOutputBtn")
        btnRow.addWidget(self.selectOutputBtn, 1)
        flay.addLayout(btnRow)
        self.filePathLabel = QLabel("No file selected")
        self.filePathLabel.setObjectName("filePathLabel")
        self.filePathLabel.setWordWrap(True)
        flay.addWidget(self.filePathLabel)
        lay.addWidget(fileCard)
        self.fileCard = fileCard

        # Settings card
        settingsCard = self._card()
        slay = QVBoxLayout(settingsCard)
        slay.setContentsMargins(12, 10, 12, 10)
        slay.setSpacing(8)
        slay.addWidget(self._section_title("LANGUAGES"))

        self.model_size_dropdown = QComboBox()
        self.model_size_dropdown.setObjectName("modelDropdown")
        self.model_size_dropdown.setVisible(False)
        slay.addWidget(self.model_size_dropdown)

        self.VRamUsage = QLabel("")
        self.VRamUsage.setVisible(False)
        self.rSpeed = QLabel("")
        self.rSpeed.setVisible(False)

        langGrid = QGridLayout()
        langGrid.setHorizontalSpacing(10)
        langGrid.addWidget(self._label("Source"), 0, 0)
        self.source_language_dropdown = QComboBox()
        self.source_language_dropdown.setObjectName("srcLangDropdown")
        langGrid.addWidget(self.source_language_dropdown, 1, 0)
        langGrid.addWidget(self._label("Target"), 0, 1)
        self.target_language_dropdown = QComboBox()
        self.target_language_dropdown.setObjectName("tgtLangDropdown")
        langGrid.addWidget(self.target_language_dropdown, 1, 1)
        slay.addLayout(langGrid)

        slay.addWidget(self._section_title("ENGINE"))
        engGrid = QGridLayout()
        engGrid.setHorizontalSpacing(10)
        engGrid.addWidget(self._label("Translation Engine"), 0, 0)
        self.target_engine = QComboBox()
        self.target_engine.setObjectName("engineDropdown")
        engGrid.addWidget(self.target_engine, 1, 0)

        engGrid.addWidget(self._label("Volume Boost"), 0, 1)
        volRow = QHBoxLayout()
        self.boostSlider = QSlider(Qt.Orientation.Horizontal)
        self.boostSlider.setObjectName("boostSlider")
        self.boostSlider.setMinimum(1)
        self.boostSlider.setMaximum(10)
        self.boostSlider.setValue(3)
        volRow.addWidget(self.boostSlider)
        self.boostLabel = QLabel("3")
        self.boostLabel.setMinimumWidth(20)
        volRow.addWidget(self.boostLabel)
        engGrid.addLayout(volRow, 1, 1)
        slay.addLayout(engGrid)

        # MLAAS sub-card
        mlaasFrame = self._card()
        mlay = QVBoxLayout(mlaasFrame)
        mlay.setContentsMargins(10, 8, 10, 8)
        mlay.setSpacing(4)
        mlaasTop = QHBoxLayout()
        mlaasTop.addWidget(self._section_title("MLAAS API"))
        self.mlaasStatusLabel = QLabel("Loading...")
        self.mlaasStatusLabel.setStyleSheet("color:#9a9a9f;")
        mlaasTop.addWidget(self.mlaasStatusLabel)
        mlaasTop.addStretch()
        mlay.addLayout(mlaasTop)
        bearerRow = QHBoxLayout()
        self.bearerTokenEdit = QLineEdit()
        self.bearerTokenEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.bearerTokenEdit.setPlaceholderText("Paste Bearer JWT token here (optional)...")
        bearerRow.addWidget(self.bearerTokenEdit, 1)
        self.getTokenBtn = QPushButton("Get Token")
        self.getTokenBtn.setFixedWidth(96)
        bearerRow.addWidget(self.getTokenBtn)
        mlay.addLayout(bearerRow)
        slay.addWidget(mlaasFrame)
        lay.addWidget(settingsCard)
        self.settingsCard = settingsCard

        # Action card
        actionCard = self._card()
        alay = QVBoxLayout(actionCard)
        alay.setContentsMargins(12, 10, 12, 10)
        alay.setSpacing(8)

        self.startButton = QPushButton("Start Processing")
        self.startButton.setObjectName("startButton")
        alay.addWidget(self.startButton)

        self.phaseStrip = PhaseStrip()
        self.phaseStrip.setObjectName("phaseStrip")
        alay.addWidget(self.phaseStrip)

        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        alay.addWidget(self.progressBar)

        statusRow = QHBoxLayout()
        self.statusLabel = QLabel("Standby")
        self.statusLabel.setObjectName("statusLabel")
        statusRow.addWidget(self.statusLabel)
        statusRow.addStretch()
        self.etaLabel = QLabel("")
        self.etaLabel.setObjectName("etaLabel")
        statusRow.addWidget(self.etaLabel)
        alay.addLayout(statusRow)

        self.logPanelHost = QFrame()
        self.logPanelHost.setObjectName("logPanelHost")
        alay.addWidget(self.logPanelHost)

        lay.addWidget(actionCard)
        self.actionCard = actionCard

        # Mascot host (MascotWidget inserted by AutoUI.py)
        self.mascotHost = QFrame()
        self.mascotHost.setObjectName("mascotHost")
        self.mascotHost.setFixedHeight(140)
        mhLay = QHBoxLayout(self.mascotHost)
        mhLay.setContentsMargins(0, 0, 0, 0)
        mhLay.addStretch(1)
        mhLay.addStretch(1)
        lay.addWidget(self.mascotHost)

        lay.addStretch(1)
        self.subtitleTab = pane
        self.workflowStack.addWidget(pane)

    def _build_notes_pane(self):
        pane = QWidget()
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        card = self._card()
        clay = QVBoxLayout(card)
        clay.setContentsMargins(12, 10, 12, 10)
        clay.setSpacing(6)
        clay.addWidget(self._section_title("MEETING TRANSCRIPT"))
        self.uploadDocxBtn = QPushButton("Upload .docx Transcript")
        self.uploadDocxBtn.setObjectName("uploadDocxBtn")
        clay.addWidget(self.uploadDocxBtn)
        self.docxPathLabel = QLabel("No file selected")
        self.docxPathLabel.setObjectName("docxPathLabel")
        clay.addWidget(self.docxPathLabel)
        self.generateNotesBtn = QPushButton("Generate Meeting Notes")
        self.generateNotesBtn.setObjectName("generateNotesBtn")
        clay.addWidget(self.generateNotesBtn)
        self.notesOutput = QTextEdit()
        self.notesOutput.setObjectName("notesOutput")
        self.notesOutput.setMinimumHeight(200)
        clay.addWidget(self.notesOutput)
        self.saveNotesBtn = QPushButton("Save Notes")
        self.saveNotesBtn.setObjectName("saveNotesBtn")
        clay.addWidget(self.saveNotesBtn)
        lay.addWidget(card)
        lay.addStretch(1)
        self.notesTab = pane
        self.workflowStack.addWidget(pane)

    def _build_translate_pane(self):
        pane = QWidget()
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        card = self._card()
        clay = QVBoxLayout(card)
        clay.setContentsMargins(12, 10, 12, 10)
        clay.setSpacing(6)
        clay.addWidget(self._section_title("FILE"))
        self.uploadTransBtn = QPushButton("Upload File (.srt / .docx / .txt)")
        self.uploadTransBtn.setObjectName("uploadTransBtn")
        clay.addWidget(self.uploadTransBtn)
        self.transFilePathLabel = QLabel("No file selected")
        self.transFilePathLabel.setObjectName("transFilePathLabel")
        clay.addWidget(self.transFilePathLabel)

        clay.addWidget(self._section_title("LANGUAGES"))
        tlGrid = QGridLayout()
        tlGrid.addWidget(self._label("Source"), 0, 0)
        self.transSrcDropdown = QComboBox()
        self.transSrcDropdown.setObjectName("transSrcDropdown")
        tlGrid.addWidget(self.transSrcDropdown, 1, 0)
        tlGrid.addWidget(self._label("Target"), 0, 1)
        self.transTgtDropdown = QComboBox()
        self.transTgtDropdown.setObjectName("transTgtDropdown")
        tlGrid.addWidget(self.transTgtDropdown, 1, 1)
        clay.addLayout(tlGrid)

        self.translateFileBtn = QPushButton("Translate File")
        self.translateFileBtn.setObjectName("translateFileBtn")
        clay.addWidget(self.translateFileBtn)
        lay.addWidget(card)
        lay.addStretch(1)
        self.translateTab = pane
        self.workflowStack.addWidget(pane)
