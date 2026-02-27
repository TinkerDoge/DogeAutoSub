# -*- coding: utf-8 -*-
"""
DogeAutoSub — Modern UI Layout
Hand-coded replacement for Qt Designer generated file.
Provides a QMainWindow with tabbed interface (Subtitles + Meeting Notes).
"""

from PySide6.QtCore import (QCoreApplication, QMetaObject, QSize, Qt)
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QSizePolicy, QSlider, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QSpacerItem,
)


class Ui_MainWindow(object):
    """Modern tabbed UI for DogeAutoSub."""

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 950)
        MainWindow.setMinimumSize(QSize(610, 950))
        MainWindow.setMaximumSize(QSize(610, 950))
        MainWindow.setWindowTitle("DogeAutoSub")

        # Fonts
        self.font_title = QFont()
        self.font_title.setFamilies(["Segoe UI", "Inter", "Arial"])
        self.font_title.setPointSize(11)
        self.font_title.setBold(True)

        self.font_body = QFont()
        self.font_body.setFamilies(["Segoe UI", "Inter", "Arial"])
        self.font_body.setPointSize(10)

        self.font_small = QFont()
        self.font_small.setFamilies(["Segoe UI", "Inter", "Arial"])
        self.font_small.setPointSize(9)

        # ── Central Widget ──────────────────────────────────────
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setContentsMargins(16, 12, 16, 12)
        self.mainLayout.setSpacing(8)

        # ── Header Row (Title + Theme/Folder buttons) ───────────
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(8)

        self.appTitle = QLabel("DogeAutoSub")
        self.appTitle.setFont(self.font_title)
        self.appTitle.setObjectName("sectionTitle")
        self.headerLayout.addWidget(self.appTitle)

        self.versionLabel = QLabel("")
        self.versionLabel.setFont(self.font_small)
        self.versionLabel.setObjectName("versionLabel")
        self.versionLabel.setStyleSheet("color: #8b949e; padding-left: 4px;")
        self.headerLayout.addWidget(self.versionLabel)

        self.headerLayout.addStretch()

        self.openFolderBtn = QPushButton("📂")
        self.openFolderBtn.setObjectName("openFolderBtn")
        self.openFolderBtn.setToolTip("Open output folder")
        self.headerLayout.addWidget(self.openFolderBtn)

        self.themeBtn = QPushButton("🎨")
        self.themeBtn.setObjectName("themeBtn")
        self.themeBtn.setToolTip("Toggle dark/light theme")
        self.headerLayout.addWidget(self.themeBtn)

        self.mainLayout.addLayout(self.headerLayout)

        # ── Tab Widget ──────────────────────────────────────────
        self.tabWidget = QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        self.mainLayout.addWidget(self.tabWidget)

        # ════════════════════════════════════════════════════════
        # TAB 1: SUBTITLES
        # ════════════════════════════════════════════════════════
        self.subtitleTab = QWidget()
        self.subtitleTab.setObjectName("subtitleTab")
        self.subtitleTabLayout = QVBoxLayout(self.subtitleTab)
        self.subtitleTabLayout.setContentsMargins(8, 12, 8, 8)
        self.subtitleTabLayout.setSpacing(10)

        # ── File Selection Card ─────────────────────────────────
        self.fileCard = QFrame()
        self.fileCard.setObjectName("fileCard")
        self.fileCard.setFrameShape(QFrame.Shape.StyledPanel)
        fileCardLayout = QVBoxLayout(self.fileCard)
        fileCardLayout.setSpacing(8)

        fileHeaderLayout = QHBoxLayout()
        fileSectionLabel = QLabel("📁 Input / Output")
        fileSectionLabel.setFont(self.font_title)
        fileSectionLabel.setObjectName("sectionTitle")
        fileHeaderLayout.addWidget(fileSectionLabel)
        fileHeaderLayout.addStretch()
        fileCardLayout.addLayout(fileHeaderLayout)

        fileBtnLayout = QHBoxLayout()
        fileBtnLayout.setSpacing(8)

        self.selectFileBtn = QPushButton("🎬  Select Video File")
        self.selectFileBtn.setObjectName("selectFileBtn")
        self.selectFileBtn.setToolTip("Click or drag a video/audio file here")
        self.selectFileBtn.setMinimumHeight(48)
        fileBtnLayout.addWidget(self.selectFileBtn, stretch=2)

        self.selectOutputBtn = QPushButton("📁  Output Folder")
        self.selectOutputBtn.setObjectName("selectOutputBtn")
        self.selectOutputBtn.setToolTip("Choose where to save subtitle files")
        self.selectOutputBtn.setMinimumHeight(48)
        fileBtnLayout.addWidget(self.selectOutputBtn, stretch=1)

        fileCardLayout.addLayout(fileBtnLayout)

        self.filePathLabel = QLabel("No file selected")
        self.filePathLabel.setObjectName("filePathLabel")
        self.filePathLabel.setFont(self.font_small)
        self.filePathLabel.setWordWrap(True)
        fileCardLayout.addWidget(self.filePathLabel)

        self.subtitleTabLayout.addWidget(self.fileCard)

        # ── Settings Card ───────────────────────────────────────
        self.settingsCard = QFrame()
        self.settingsCard.setObjectName("settingsCard")
        self.settingsCard.setFrameShape(QFrame.Shape.StyledPanel)
        settingsLayout = QVBoxLayout(self.settingsCard)
        settingsLayout.setSpacing(10)

        settingsTitle = QLabel("⚙️ Settings")
        settingsTitle.setFont(self.font_title)
        settingsTitle.setObjectName("sectionTitle")
        settingsLayout.addWidget(settingsTitle)

        # Hidden model dropdown (kept for backend compatibility, not shown)
        self.model_size_dropdown = QComboBox()
        self.model_size_dropdown.setObjectName("modelDropdown")
        self.model_size_dropdown.setVisible(False)
        settingsLayout.addWidget(self.model_size_dropdown)

        # Hidden labels (kept for backend compatibility)
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

        settingsLayout.addLayout(langGrid)

        # Engine + Volume row
        engineVolGrid = QGridLayout()
        engineVolGrid.setHorizontalSpacing(12)
        engineVolGrid.setVerticalSpacing(6)

        engineVolGrid.addWidget(self._label("Translation Engine"), 0, 0)
        self.target_engine = QComboBox()
        self.target_engine.setObjectName("engineDropdown")
        self.target_engine.setFont(self.font_body)
        self.target_engine.setToolTip("MLAAS (fastest, uses internal API). Google for offline fallback. Whisper can only translate to English.")
        engineVolGrid.addWidget(self.target_engine, 1, 0)

        engineVolGrid.addWidget(self._label("Volume Boost"), 0, 1)
        volLayout = QHBoxLayout()
        volLayout.setSpacing(8)
        self.boostSlider = QSlider(Qt.Orientation.Horizontal)
        self.boostSlider.setObjectName("boostSlider")
        self.boostSlider.setMinimum(1)
        self.boostSlider.setMaximum(10)
        self.boostSlider.setValue(3)
        self.boostSlider.setToolTip("Increase if the source audio volume is too low")
        volLayout.addWidget(self.boostSlider)
        self.boostLabel = QLabel("3")
        self.boostLabel.setFont(self.font_body)
        self.boostLabel.setMinimumWidth(20)
        volLayout.addWidget(self.boostLabel)
        engineVolGrid.addLayout(volLayout, 1, 1)

        settingsLayout.addLayout(engineVolGrid)

        # ── MLAAS Auth Card (inside settings) ───────────────────
        mlaasFrame = QFrame()
        mlaasFrame.setObjectName("fileCard")
        mlaasFrame.setFrameShape(QFrame.Shape.StyledPanel)
        mlaasLayout = QVBoxLayout(mlaasFrame)
        mlaasLayout.setContentsMargins(8, 6, 8, 6)
        mlaasLayout.setSpacing(6)

        mlaasTitleRow = QHBoxLayout()
        mlaasTitle = QLabel("🔑 MLAAS API Token")
        mlaasTitle.setFont(self.font_title)
        mlaasTitle.setObjectName("sectionTitle")
        mlaasTitleRow.addWidget(mlaasTitle)
        mlaasTitleRow.addStretch()

        self.getTokenBtn = QPushButton("🔗 Get Token")
        self.getTokenBtn.setObjectName("getTokenBtn")
        self.getTokenBtn.setToolTip("Open https://mlaas.virtuosgames.com/auth/token in browser")
        self.getTokenBtn.setFont(self.font_small)
        self.getTokenBtn.setFixedHeight(22)
        mlaasTitleRow.addWidget(self.getTokenBtn)
        mlaasLayout.addLayout(mlaasTitleRow)

        self.mlaasTokenInput = QLineEdit()
        self.mlaasTokenInput.setObjectName("mlaasTokenInput")
        self.mlaasTokenInput.setPlaceholderText("Paste Bearer token here (expires ~2h)…")
        self.mlaasTokenInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.mlaasTokenInput.setFont(self.font_body)
        self.mlaasTokenInput.setFixedWidth(300)
        self.mlaasTokenInput.setMinimumHeight(32)
        mlaasLayout.addWidget(self.mlaasTokenInput)

        settingsLayout.addWidget(mlaasFrame)

        self.subtitleTabLayout.addWidget(self.settingsCard)

        # ── Action Card (Start + Progress) ──────────────────────
        self.actionCard = QFrame()
        self.actionCard.setObjectName("actionCard")
        self.actionCard.setFrameShape(QFrame.Shape.StyledPanel)
        actionLayout = QVBoxLayout(self.actionCard)
        actionLayout.setSpacing(10)

        self.startButton = QPushButton("▶  START PROCESSING")
        self.startButton.setObjectName("startButton")
        self.startButton.setToolTip("Begin subtitle generation")
        self.startButton.setFont(self.font_title)
        actionLayout.addWidget(self.startButton)

        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        actionLayout.addWidget(self.progressBar)

        # Status row
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

        actionLayout.addLayout(statusRow)

        # Status image (loading animation)
        self.statusImage = QLabel()
        self.statusImage.setObjectName("statusImage")
        self.statusImage.setMaximumSize(QSize(130, 130))
        self.statusImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actionLayout.addWidget(self.statusImage, alignment=Qt.AlignmentFlag.AlignCenter)

        self.subtitleTabLayout.addWidget(self.actionCard)

        # Add stretch at bottom
        self.subtitleTabLayout.addStretch()

        self.tabWidget.addTab(self.subtitleTab, "📝 Subtitles")

        # ════════════════════════════════════════════════════════
        # TAB 2: MEETING NOTES
        # ════════════════════════════════════════════════════════
        self.notesTab = QWidget()
        self.notesTab.setObjectName("notesTab")
        self.notesTabLayout = QVBoxLayout(self.notesTab)
        self.notesTabLayout.setContentsMargins(8, 12, 8, 8)
        self.notesTabLayout.setSpacing(10)

        # ── File Upload Card ────────────────────────────────────
        self.notesFileCard = QFrame()
        self.notesFileCard.setObjectName("notesFileCard")
        self.notesFileCard.setFrameShape(QFrame.Shape.StyledPanel)
        notesFileLayout = QVBoxLayout(self.notesFileCard)
        notesFileLayout.setSpacing(8)

        notesFileTitle = QLabel("📄 Meeting Transcript")
        notesFileTitle.setFont(self.font_title)
        notesFileTitle.setObjectName("sectionTitle")
        notesFileLayout.addWidget(notesFileTitle)

        self.selectDocxBtn = QPushButton("📎  Upload DOCX Transcript")
        self.selectDocxBtn.setObjectName("selectFileBtn")
        self.selectDocxBtn.setToolTip("Upload a Teams or Zoom meeting transcript (.docx)")
        self.selectDocxBtn.setMinimumHeight(48)
        notesFileLayout.addWidget(self.selectDocxBtn)

        self.docxPathLabel = QLabel("No transcript uploaded")
        self.docxPathLabel.setObjectName("filePathLabel")
        self.docxPathLabel.setFont(self.font_small)
        self.docxPathLabel.setWordWrap(True)
        notesFileLayout.addWidget(self.docxPathLabel)

        self.notesTabLayout.addWidget(self.notesFileCard)

        # Meeting Notes reuses MLAAS config from Subtitles tab
        # No separate LLM config card needed
        mlaasNoteInfo = QLabel("ℹ️ Uses MLAAS API token from Subtitles tab for summarization.")
        mlaasNoteInfo.setFont(self.font_small)
        mlaasNoteInfo.setWordWrap(True)
        self.notesTabLayout.addWidget(mlaasNoteInfo)

        # Hidden widgets for backward compatibility with AutoUI.py
        self.llmApiUrl = QLineEdit()
        self.llmApiUrl.setVisible(False)
        self.llmApiKey = QLineEdit()
        self.llmApiKey.setVisible(False)
        self.llmModelName = QLineEdit()
        self.llmModelName.setVisible(False)

        # ── Generate + Output Card ──────────────────────────────
        self.notesOutputCard = QFrame()
        self.notesOutputCard.setObjectName("notesOutputCard")
        self.notesOutputCard.setFrameShape(QFrame.Shape.StyledPanel)
        notesOutLayout = QVBoxLayout(self.notesOutputCard)
        notesOutLayout.setSpacing(8)

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

        notesOutLayout.addLayout(notesBtnRow)

        self.notesStatusLabel = QLabel("")
        self.notesStatusLabel.setObjectName("statusLabel")
        self.notesStatusLabel.setFont(self.font_small)
        notesOutLayout.addWidget(self.notesStatusLabel)

        self.notesOutput = QTextEdit()
        self.notesOutput.setObjectName("notesOutput")
        self.notesOutput.setPlaceholderText("Meeting notes will appear here after generation...")
        self.notesOutput.setFont(self.font_body)
        self.notesOutput.setMinimumHeight(200)
        self.notesOutput.setReadOnly(False)
        notesOutLayout.addWidget(self.notesOutput)

        self.notesTabLayout.addWidget(self.notesOutputCard)

        self.tabWidget.addTab(self.notesTab, "📋 Meeting Notes")

        # ════════════════════════════════════════════════════════
        # TAB 3: TRANSLATE FILE
        # ════════════════════════════════════════════════════════
        self.translateTab = QWidget()
        self.translateTab.setObjectName("translateTab")
        self.translateTabLayout = QVBoxLayout(self.translateTab)
        self.translateTabLayout.setContentsMargins(8, 12, 8, 8)
        self.translateTabLayout.setSpacing(10)

        # ── File Upload Card ────────────────────────────────────
        self.transFileCard = QFrame()
        self.transFileCard.setObjectName("fileCard")
        self.transFileCard.setFrameShape(QFrame.Shape.StyledPanel)
        transFileLayout = QVBoxLayout(self.transFileCard)
        transFileLayout.setSpacing(8)

        transFileTitle = QLabel("📄 Source File")
        transFileTitle.setFont(self.font_title)
        transFileTitle.setObjectName("sectionTitle")
        transFileLayout.addWidget(transFileTitle)

        self.selectTransFileBtn = QPushButton("📎  Upload File (.srt, .docx, .txt)")
        self.selectTransFileBtn.setObjectName("selectFileBtn")
        self.selectTransFileBtn.setToolTip("Upload a subtitle or transcript file to translate")
        self.selectTransFileBtn.setMinimumHeight(48)
        transFileLayout.addWidget(self.selectTransFileBtn)

        self.transFilePathLabel = QLabel("No file selected")
        self.transFilePathLabel.setObjectName("filePathLabel")
        self.transFilePathLabel.setFont(self.font_small)
        self.transFilePathLabel.setWordWrap(True)
        transFileLayout.addWidget(self.transFilePathLabel)

        self.translateTabLayout.addWidget(self.transFileCard)

        # ── Translation Settings Card ───────────────────────────
        self.transSettingsCard = QFrame()
        self.transSettingsCard.setObjectName("settingsCard")
        self.transSettingsCard.setFrameShape(QFrame.Shape.StyledPanel)
        transSettingsLayout = QVBoxLayout(self.transSettingsCard)
        transSettingsLayout.setSpacing(8)

        transSettingsTitle = QLabel("⚙️ Translation Settings")
        transSettingsTitle.setFont(self.font_title)
        transSettingsTitle.setObjectName("sectionTitle")
        transSettingsLayout.addWidget(transSettingsTitle)

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

        transSettingsLayout.addLayout(transLangGrid)

        transEngineRow = QHBoxLayout()
        transEngineRow.setSpacing(12)
        transEngineRow.addWidget(self._label("Engine:"))
        self.trans_engine = QComboBox()
        self.trans_engine.setObjectName("transEngine")
        self.trans_engine.setFont(self.font_body)
        transEngineRow.addWidget(self.trans_engine, stretch=1)
        transSettingsLayout.addLayout(transEngineRow)

        transTokenInfo = QLabel("ℹ️ Uses MLAAS token from Subtitles tab if MLAAS engine is selected.")
        transTokenInfo.setFont(self.font_small)
        transTokenInfo.setWordWrap(True)
        transSettingsLayout.addWidget(transTokenInfo)

        self.translateTabLayout.addWidget(self.transSettingsCard)

        # ── Translate Action + Output Card ──────────────────────
        self.transOutputCard = QFrame()
        self.transOutputCard.setObjectName("notesOutputCard")
        self.transOutputCard.setFrameShape(QFrame.Shape.StyledPanel)
        transOutLayout = QVBoxLayout(self.transOutputCard)
        transOutLayout.setSpacing(8)

        transBtnRow = QHBoxLayout()
        self.translateFileBtn = QPushButton("🌐  Translate File")
        self.translateFileBtn.setObjectName("generateNotesBtn")
        self.translateFileBtn.setFont(self.font_title)
        self.translateFileBtn.setMinimumHeight(44)
        transBtnRow.addWidget(self.translateFileBtn)

        self.saveTransBtn = QPushButton("💾 Save")
        self.saveTransBtn.setObjectName("saveNotesBtn")
        self.saveTransBtn.setMinimumHeight(44)
        transBtnRow.addWidget(self.saveTransBtn)

        transOutLayout.addLayout(transBtnRow)

        self.transStatusLabel = QLabel("")
        self.transStatusLabel.setObjectName("statusLabel")
        self.transStatusLabel.setFont(self.font_small)
        transOutLayout.addWidget(self.transStatusLabel)

        self.transOutput = QTextEdit()
        self.transOutput.setObjectName("transOutput")
        self.transOutput.setPlaceholderText("Translated content will appear here...")
        self.transOutput.setFont(self.font_body)
        self.transOutput.setMinimumHeight(200)
        self.transOutput.setReadOnly(False)
        transOutLayout.addWidget(self.transOutput)

        self.translateTabLayout.addWidget(self.transOutputCard)

        self.tabWidget.addTab(self.translateTab, "🌐 Translate")

        # ── Wire up slider → label ──────────────────────────────
        self.boostSlider.valueChanged.connect(lambda v: self.boostLabel.setText(str(v)))

        QMetaObject.connectSlotsByName(MainWindow)

    # ── Helper ──────────────────────────────────────────────────
    def _label(self, text: str) -> QLabel:
        """Create a small descriptive label."""
        lbl = QLabel(text)
        lbl.setFont(self.font_small)
        return lbl
