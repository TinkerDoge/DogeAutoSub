# -*- coding: utf-8 -*-
"""DogeAutoSub — Win95-modernized UI layout.

Hand-coded layout. Preserves every widget name and signal previously
used by AutoUI.py so that file requires no changes during Phase A.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QSlider, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)


class Ui_MainWindow(object):
    """Tabbed UI: Subtitles + Meeting Notes + Translate File."""

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _label(self, text: str, *, small: bool = False) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self.font_small if small else self.font_body)
        return lbl

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        lbl.setFont(self.font_title)
        return lbl

    def _card(self) -> QFrame:
        f = QFrame()
        f.setObjectName("card")
        f.setFrameShape(QFrame.Shape.StyledPanel)
        return f

    # ── setupUi ──────────────────────────────────────────────────────────────
    def setupUi(self, MainWindow: QMainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(650, 900)
        MainWindow.setMinimumSize(QSize(650, 900))
        MainWindow.setMaximumSize(QSize(720, 1080))
        MainWindow.setWindowTitle("DogeAutoSub")

        self.font_title = QFont()
        self.font_title.setPointSize(11)
        self.font_title.setBold(True)
        self.font_body = QFont()
        self.font_body.setPointSize(10)
        self.font_small = QFont()
        self.font_small.setPointSize(9)

        # ── Central widget ────────────────────────────────────────────────
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        outer = QVBoxLayout(self.centralWidget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Faux Win95 title bar (cosmetic decoration) ────────────────────
        self.fauxTitleBar = QFrame()
        self.fauxTitleBar.setObjectName("fauxTitleBar")
        ttl = QHBoxLayout(self.fauxTitleBar)
        ttl.setContentsMargins(8, 0, 6, 0)
        ttl.setSpacing(4)

        self.fauxTitleText = QLabel("🐕 DogeAutoSub")
        self.fauxTitleText.setObjectName("fauxTitleText")
        ttl.addWidget(self.fauxTitleText)

        self.versionLabel = QLabel("")
        self.versionLabel.setStyleSheet("color: #c0d0f0; padding-left: 4px;")
        self.versionLabel.setFont(self.font_small)
        ttl.addWidget(self.versionLabel)
        ttl.addStretch()

        for ch in ("_", "□", "×"):
            b = QLabel(ch)
            b.setStyleSheet(
                "color:#000; background:#c0c0c0;"
                "border:1px solid #fff; padding:0 6px; font-size:10px;"
                "min-width:14px; max-height:14px; border-radius:2px;"
            )
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ttl.addWidget(b)

        #outer.addWidget(self.fauxTitleBar)

        # ── Cosmetic menu bar ────────────────────────────────────────────
        self.menuBarFrame = QFrame()
        self.menuBarFrame.setObjectName("menuBar")
        menu = QHBoxLayout(self.menuBarFrame)
        menu.setContentsMargins(4, 0, 4, 0)
        menu.setSpacing(2)

        self.menuItems: dict[str, QLabel] = {}
        for name in ("File", "Edit", "View", "Help"):
            lbl = QLabel(name)
            lbl.setObjectName("menuItem")
            menu.addWidget(lbl)
            self.menuItems[name] = lbl
        menu.addStretch()

        self.openFolderBtn = QPushButton("📂")
        self.openFolderBtn.setObjectName("openFolderBtn")
        self.openFolderBtn.setFixedSize(24, 20)
        self.openFolderBtn.setToolTip("Open output folder")
        menu.addWidget(self.openFolderBtn)

        self.themeBtn = QPushButton("🎨")
        self.themeBtn.setObjectName("themeBtn")
        self.themeBtn.setFixedSize(24, 20)
        self.themeBtn.setToolTip("Toggle dark/light theme")
        menu.addWidget(self.themeBtn)

        outer.addWidget(self.menuBarFrame)

        # ── App body ─────────────────────────────────────────────────────
        body = QFrame()
        body.setObjectName("body")
        bodyLay = QVBoxLayout(body)
        bodyLay.setContentsMargins(14, 10, 14, 14)
        bodyLay.setSpacing(8)
        outer.addWidget(body, 1)

        # Kept for backward-compat; hidden — title is now in fauxTitleBar
        self.appTitle = QLabel("DogeAutoSub")
        self.appTitle.setObjectName("sectionTitle")
        self.appTitle.setVisible(False)
        bodyLay.addWidget(self.appTitle)

        # ── Tab widget ───────────────────────────────────────────────────
        self.tabWidget = QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        bodyLay.addWidget(self.tabWidget, 1)

        self._build_subtitles_tab()
        self._build_notes_tab()
        self._build_translate_tab()

        # ── Wire slider → label ───────────────────────────────────────────
        self.boostSlider.valueChanged.connect(lambda v: self.boostLabel.setText(str(v)))

    # ── Tab builders ─────────────────────────────────────────────────────────

    def _build_subtitles_tab(self):
        self.subtitleTab = QWidget()
        self.subtitleTab.setObjectName("subtitleTab")
        lay = QVBoxLayout(self.subtitleTab)
        lay.setContentsMargins(8, 12, 8, 8)
        lay.setSpacing(10)

        # ── File card ────────────────────────────────────────────────────
        self.fileCard = QFrame()
        self.fileCard.setObjectName("card")
        self.fileCard.setFrameShape(QFrame.Shape.StyledPanel)
        flay = QVBoxLayout(self.fileCard)
        flay.setSpacing(8)

        flay.addWidget(self._section_title("📁 Input / Output"))

        btnRow = QHBoxLayout()
        btnRow.setSpacing(8)

        self.selectFileBtn = QPushButton("🎬  Select Video File")
        self.selectFileBtn.setObjectName("selectFileBtn")
        self.selectFileBtn.setToolTip("Click or drag a video/audio file here")
        self.selectFileBtn.setMinimumHeight(48)
        btnRow.addWidget(self.selectFileBtn, stretch=2)

        self.selectOutputBtn = QPushButton("📁  Output Folder")
        self.selectOutputBtn.setObjectName("selectOutputBtn")
        self.selectOutputBtn.setToolTip("Choose where to save subtitle files")
        self.selectOutputBtn.setMinimumHeight(48)
        btnRow.addWidget(self.selectOutputBtn, stretch=1)

        flay.addLayout(btnRow)

        self.filePathLabel = QLabel("No file selected")
        self.filePathLabel.setObjectName("filePathLabel")
        self.filePathLabel.setFont(self.font_small)
        self.filePathLabel.setWordWrap(True)
        flay.addWidget(self.filePathLabel)

        lay.addWidget(self.fileCard)

        # ── Settings card ────────────────────────────────────────────────
        self.settingsCard = QFrame()
        self.settingsCard.setObjectName("card")
        self.settingsCard.setFrameShape(QFrame.Shape.StyledPanel)
        slay = QVBoxLayout(self.settingsCard)
        slay.setSpacing(10)

        slay.addWidget(self._section_title("⚙️ Settings"))

        # Hidden — kept for backend compatibility
        self.model_size_dropdown = QComboBox()
        self.model_size_dropdown.setObjectName("modelDropdown")
        self.model_size_dropdown.setVisible(False)
        slay.addWidget(self.model_size_dropdown)

        self.VRamUsage = QLabel("")
        self.VRamUsage.setVisible(False)
        self.rSpeed = QLabel("")
        self.rSpeed.setVisible(False)

        # Language row
        langGrid = QGridLayout()
        langGrid.setHorizontalSpacing(12)
        langGrid.setVerticalSpacing(6)

        langGrid.addWidget(self._label("Source Language"), 0, 0)
        self.source_language_dropdown = QComboBox()
        self.source_language_dropdown.setObjectName("srcLangDropdown")
        self.source_language_dropdown.setFont(self.font_body)
        self.source_language_dropdown.setToolTip("Language of the source video (Auto = auto-detect)")
        langGrid.addWidget(self.source_language_dropdown, 1, 0)

        langGrid.addWidget(self._label("Target Language"), 0, 1)
        self.target_language_dropdown = QComboBox()
        self.target_language_dropdown.setObjectName("tgtLangDropdown")
        self.target_language_dropdown.setFont(self.font_body)
        self.target_language_dropdown.setToolTip("Language to translate subtitles to")
        langGrid.addWidget(self.target_language_dropdown, 1, 1)

        slay.addLayout(langGrid)

        # Engine + Volume row
        evGrid = QGridLayout()
        evGrid.setHorizontalSpacing(12)
        evGrid.setVerticalSpacing(6)

        evGrid.addWidget(self._label("Translation Engine"), 0, 0)
        self.target_engine = QComboBox()
        self.target_engine.setObjectName("engineDropdown")
        self.target_engine.setFont(self.font_body)
        self.target_engine.setToolTip(
            "Claude/GPT use MLAAS API. Google Translate for offline fallback. "
            "Whisper can only translate to English."
        )
        evGrid.addWidget(self.target_engine, 1, 0)

        evGrid.addWidget(self._label("Volume Boost"), 0, 1)
        volRow = QHBoxLayout()
        volRow.setSpacing(8)
        self.boostSlider = QSlider(Qt.Orientation.Horizontal)
        self.boostSlider.setObjectName("boostSlider")
        self.boostSlider.setMinimum(1)
        self.boostSlider.setMaximum(10)
        self.boostSlider.setValue(3)
        self.boostSlider.setToolTip("Increase if the source audio volume is too low")
        volRow.addWidget(self.boostSlider)
        self.boostLabel = QLabel("3")
        self.boostLabel.setFont(self.font_body)
        self.boostLabel.setMinimumWidth(20)
        volRow.addWidget(self.boostLabel)
        evGrid.addLayout(volRow, 1, 1)

        slay.addLayout(evGrid)

        # MLAAS API sub-card
        mlaasFrame = QFrame()
        mlaasFrame.setObjectName("card")
        mlaasFrame.setFrameShape(QFrame.Shape.StyledPanel)
        mlay = QVBoxLayout(mlaasFrame)
        mlay.setContentsMargins(8, 6, 8, 6)
        mlay.setSpacing(4)

        mlaasTop = QHBoxLayout()
        mlaasTop.setSpacing(8)
        mlaasTop.addWidget(self._section_title("🔑 MLAAS API"))
        self.mlaasStatusLabel = QLabel("Loading…")
        self.mlaasStatusLabel.setFont(self.font_body)
        self.mlaasStatusLabel.setStyleSheet("color: #888;")
        mlaasTop.addWidget(self.mlaasStatusLabel)
        mlaasTop.addStretch()
        mlay.addLayout(mlaasTop)

        bearerRow = QHBoxLayout()
        bearerRow.setSpacing(6)
        self.bearerTokenEdit = QLineEdit()
        self.bearerTokenEdit.setPlaceholderText(
            "Paste Bearer JWT token here (optional, overrides API key)…"
        )
        self.bearerTokenEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.bearerTokenEdit.setFont(self.font_body)
        self.bearerTokenEdit.setToolTip(
            "Personal JWT token from mlaas.virtuosgames.com/auth/token\n"
            "Expires every ~2 hours. Use when the shared API key hits rate limits."
        )
        bearerRow.addWidget(self.bearerTokenEdit, 1)
        self.getTokenBtn = QPushButton("🔗 Get Token")
        self.getTokenBtn.setFont(self.font_body)
        self.getTokenBtn.setFixedWidth(100)
        self.getTokenBtn.setToolTip("Open the MLAAS token generator in your browser")
        bearerRow.addWidget(self.getTokenBtn)
        mlay.addLayout(bearerRow)

        slay.addWidget(mlaasFrame)
        lay.addWidget(self.settingsCard)

        # ── Action card ───────────────────────────────────────────────────
        self.actionCard = QFrame()
        self.actionCard.setObjectName("card")
        self.actionCard.setFrameShape(QFrame.Shape.StyledPanel)
        alay = QVBoxLayout(self.actionCard)
        alay.setSpacing(10)

        self.startButton = QPushButton("▶  START PROCESSING")
        self.startButton.setObjectName("startButton")
        self.startButton.setToolTip("Begin subtitle generation")
        self.startButton.setFont(self.font_title)
        alay.addWidget(self.startButton)

        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        alay.addWidget(self.progressBar)

        statusRow = QHBoxLayout()
        statusRow.setSpacing(12)
        self.statusLabel = QLabel("Standby")
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setFont(self.font_body)
        statusRow.addWidget(self.statusLabel)
        statusRow.addStretch()
        self.etaLabel = QLabel("")
        self.etaLabel.setObjectName("etaLabel")
        self.etaLabel.setFont(self.font_small)
        statusRow.addWidget(self.etaLabel)
        alay.addLayout(statusRow)

        # Placeholder for Phase B LogPanel
        self.logPanelHost = QFrame()
        self.logPanelHost.setObjectName("logPanelHost")
        alay.addWidget(self.logPanelHost)

        lay.addWidget(self.actionCard)

        # ── Mascot strip (Phase C will swap this for MascotWidget) ──────
        self.mascotCard = QFrame()
        self.mascotCard.setObjectName("card")
        self.mascotCard.setFrameShape(QFrame.Shape.StyledPanel)
        mascotRow = QHBoxLayout(self.mascotCard)
        mascotRow.setContentsMargins(12, 8, 12, 8)

        self.statusImage = QLabel()
        self.statusImage.setObjectName("statusImage")
        self.statusImage.setMaximumSize(QSize(130, 130))
        self.statusImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mascotRow.addWidget(self.statusImage)

        self.speechBubble = QLabel("")
        self.speechBubble.setObjectName("speechBubble")
        self.speechBubble.setWordWrap(True)
        mascotRow.addWidget(self.speechBubble, 1)

        lay.addWidget(self.mascotCard)
        lay.addStretch()

        self.tabWidget.addTab(self.subtitleTab, "📝 Subtitles")

    def _build_notes_tab(self):
        self.notesTab = QWidget()
        self.notesTab.setObjectName("notesTab")
        lay = QVBoxLayout(self.notesTab)
        lay.setContentsMargins(8, 12, 8, 8)
        lay.setSpacing(10)

        # File upload card
        self.notesFileCard = QFrame()
        self.notesFileCard.setObjectName("card")
        self.notesFileCard.setFrameShape(QFrame.Shape.StyledPanel)
        nflay = QVBoxLayout(self.notesFileCard)
        nflay.setSpacing(8)

        nflay.addWidget(self._section_title("📄 Meeting Transcript"))

        self.selectDocxBtn = QPushButton("📎  Upload DOCX Transcript")
        self.selectDocxBtn.setObjectName("selectDocxBtn")
        self.selectDocxBtn.setToolTip("Upload a Teams or Zoom meeting transcript (.docx)")
        self.selectDocxBtn.setMinimumHeight(48)
        nflay.addWidget(self.selectDocxBtn)

        self.docxPathLabel = QLabel("No transcript uploaded")
        self.docxPathLabel.setObjectName("filePathLabel")
        self.docxPathLabel.setFont(self.font_small)
        self.docxPathLabel.setWordWrap(True)
        nflay.addWidget(self.docxPathLabel)

        lay.addWidget(self.notesFileCard)

        info = QLabel("ℹ️ Uses MLAAS API token from Subtitles tab for summarization.")
        info.setFont(self.font_small)
        info.setWordWrap(True)
        lay.addWidget(info)

        # Hidden — backend compatibility
        self.llmApiUrl = QLineEdit()
        self.llmApiUrl.setVisible(False)
        self.llmApiKey = QLineEdit()
        self.llmApiKey.setVisible(False)
        self.llmModelName = QLineEdit()
        self.llmModelName.setVisible(False)

        # Output card
        self.notesOutputCard = QFrame()
        self.notesOutputCard.setObjectName("card")
        self.notesOutputCard.setFrameShape(QFrame.Shape.StyledPanel)
        nolay = QVBoxLayout(self.notesOutputCard)
        nolay.setSpacing(8)

        notesBtnRow = QHBoxLayout()
        self.generateNotesBtn = QPushButton("✨  Generate Meeting Notes")
        self.generateNotesBtn.setObjectName("generateNotesBtn")
        self.generateNotesBtn.setFont(self.font_title)
        self.generateNotesBtn.setMinimumHeight(44)
        notesBtnRow.addWidget(self.generateNotesBtn)
        self.saveNotesBtn = QPushButton("💾 Save")
        self.saveNotesBtn.setObjectName("saveNotesBtn")
        self.saveNotesBtn.setMinimumHeight(44)
        notesBtnRow.addWidget(self.saveNotesBtn)
        nolay.addLayout(notesBtnRow)

        self.notesStatusLabel = QLabel("")
        self.notesStatusLabel.setObjectName("statusLabel")
        self.notesStatusLabel.setFont(self.font_small)
        nolay.addWidget(self.notesStatusLabel)

        self.notesOutput = QTextEdit()
        self.notesOutput.setObjectName("notesOutput")
        self.notesOutput.setPlaceholderText("Meeting notes will appear here after generation...")
        self.notesOutput.setFont(self.font_body)
        self.notesOutput.setMinimumHeight(200)
        nolay.addWidget(self.notesOutput)

        lay.addWidget(self.notesOutputCard)

        self.tabWidget.addTab(self.notesTab, "📋 Meeting Notes")

    def _build_translate_tab(self):
        self.translateTab = QWidget()
        self.translateTab.setObjectName("translateTab")
        lay = QVBoxLayout(self.translateTab)
        lay.setContentsMargins(8, 12, 8, 8)
        lay.setSpacing(10)

        # File card
        self.transFileCard = QFrame()
        self.transFileCard.setObjectName("card")
        self.transFileCard.setFrameShape(QFrame.Shape.StyledPanel)
        tflay = QVBoxLayout(self.transFileCard)
        tflay.setSpacing(8)

        tflay.addWidget(self._section_title("📄 Source File"))

        self.selectTransFileBtn = QPushButton("📎  Upload File (.srt, .docx, .txt)")
        self.selectTransFileBtn.setObjectName("selectTransFileBtn")
        self.selectTransFileBtn.setToolTip("Upload a subtitle or transcript file to translate")
        self.selectTransFileBtn.setMinimumHeight(48)
        tflay.addWidget(self.selectTransFileBtn)

        self.transFilePathLabel = QLabel("No file selected")
        self.transFilePathLabel.setObjectName("filePathLabel")
        self.transFilePathLabel.setFont(self.font_small)
        self.transFilePathLabel.setWordWrap(True)
        tflay.addWidget(self.transFilePathLabel)

        lay.addWidget(self.transFileCard)

        # Translation settings card
        self.transSettingsCard = QFrame()
        self.transSettingsCard.setObjectName("card")
        self.transSettingsCard.setFrameShape(QFrame.Shape.StyledPanel)
        tslay = QVBoxLayout(self.transSettingsCard)
        tslay.setSpacing(8)

        tslay.addWidget(self._section_title("⚙️ Translation Settings"))

        transLangGrid = QGridLayout()
        transLangGrid.setHorizontalSpacing(12)
        transLangGrid.setVerticalSpacing(6)

        transLangGrid.addWidget(self._label("Source Language"), 0, 0)
        self.trans_src_lang = QComboBox()
        self.trans_src_lang.setObjectName("transSrcLang")
        self.trans_src_lang.setFont(self.font_body)
        transLangGrid.addWidget(self.trans_src_lang, 1, 0)

        transLangGrid.addWidget(self._label("Target Language"), 0, 1)
        self.trans_tgt_lang = QComboBox()
        self.trans_tgt_lang.setObjectName("transTgtLang")
        self.trans_tgt_lang.setFont(self.font_body)
        transLangGrid.addWidget(self.trans_tgt_lang, 1, 1)

        tslay.addLayout(transLangGrid)

        engRow = QHBoxLayout()
        engRow.setSpacing(12)
        engRow.addWidget(self._label("Engine:"))
        self.trans_engine = QComboBox()
        self.trans_engine.setObjectName("transEngine")
        self.trans_engine.setFont(self.font_body)
        engRow.addWidget(self.trans_engine, stretch=1)
        tslay.addLayout(engRow)

        tokInfo = QLabel("ℹ️ Uses MLAAS token from Subtitles tab if MLAAS engine is selected.")
        tokInfo.setFont(self.font_small)
        tokInfo.setWordWrap(True)
        tslay.addWidget(tokInfo)

        lay.addWidget(self.transSettingsCard)

        # Output card
        self.transOutputCard = QFrame()
        self.transOutputCard.setObjectName("card")
        self.transOutputCard.setFrameShape(QFrame.Shape.StyledPanel)
        tolay = QVBoxLayout(self.transOutputCard)
        tolay.setSpacing(8)

        transBtnRow = QHBoxLayout()
        self.translateFileBtn = QPushButton("🌐  Translate File")
        self.translateFileBtn.setObjectName("translateFileBtn")
        self.translateFileBtn.setFont(self.font_title)
        self.translateFileBtn.setMinimumHeight(44)
        transBtnRow.addWidget(self.translateFileBtn)
        self.saveTransBtn = QPushButton("💾 Save")
        self.saveTransBtn.setObjectName("saveTransBtn")
        self.saveTransBtn.setMinimumHeight(44)
        transBtnRow.addWidget(self.saveTransBtn)
        tolay.addLayout(transBtnRow)

        self.transStatusLabel = QLabel("")
        self.transStatusLabel.setObjectName("statusLabel")
        self.transStatusLabel.setFont(self.font_small)
        tolay.addWidget(self.transStatusLabel)

        self.transOutput = QTextEdit()
        self.transOutput.setObjectName("transOutput")
        self.transOutput.setPlaceholderText("Translated content will appear here...")
        self.transOutput.setFont(self.font_body)
        self.transOutput.setMinimumHeight(200)
        tolay.addWidget(self.transOutput)

        lay.addWidget(self.transOutputCard)

        self.tabWidget.addTab(self.translateTab, "🌐 Translate")
