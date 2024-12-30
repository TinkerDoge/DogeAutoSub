# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DogeAutoSubnnBmzs.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide2.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DogeAutoSub(object):
    def setupUi(self, DogeAutoSub):
        if not DogeAutoSub.objectName():
            DogeAutoSub.setObjectName(u"DogeAutoSub")
        DogeAutoSub.resize(328, 426)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DogeAutoSub.sizePolicy().hasHeightForWidth())
        DogeAutoSub.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u"icons/favicon.png", QSize(), QIcon.Normal, QIcon.Off)
        DogeAutoSub.setWindowIcon(icon)
        DogeAutoSub.setStyleSheet(u"background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n"
"                                                stop: 0 grey, stop: 1 grey);\n"
"            border-radius: 10px;")
        self.verticalLayout_2 = QVBoxLayout(DogeAutoSub)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.InOutLayout = QVBoxLayout()
        self.InOutLayout.setObjectName(u"InOutLayout")
        self.input_file_button = QPushButton(DogeAutoSub)
        self.input_file_button.setObjectName(u"input_file_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.input_file_button.sizePolicy().hasHeightForWidth())
        self.input_file_button.setSizePolicy(sizePolicy1)
        self.input_file_button.setMinimumSize(QSize(300, 30))

        self.InOutLayout.addWidget(self.input_file_button)

        self.output_folder_button = QPushButton(DogeAutoSub)
        self.output_folder_button.setObjectName(u"output_folder_button")
        sizePolicy1.setHeightForWidth(self.output_folder_button.sizePolicy().hasHeightForWidth())
        self.output_folder_button.setSizePolicy(sizePolicy1)
        self.output_folder_button.setMinimumSize(QSize(300, 30))

        self.InOutLayout.addWidget(self.output_folder_button)


        self.verticalLayout_2.addLayout(self.InOutLayout)

        self.pathLayout = QVBoxLayout()
        self.pathLayout.setObjectName(u"pathLayout")
        self.output_file_label = QLabel(DogeAutoSub)
        self.output_file_label.setObjectName(u"output_file_label")
        sizePolicy1.setHeightForWidth(self.output_file_label.sizePolicy().hasHeightForWidth())
        self.output_file_label.setSizePolicy(sizePolicy1)
        self.output_file_label.setMinimumSize(QSize(150, 50))

        self.pathLayout.addWidget(self.output_file_label)

        self.output_file_path_display = QLabel(DogeAutoSub)
        self.output_file_path_display.setObjectName(u"output_file_path_display")
        sizePolicy1.setHeightForWidth(self.output_file_path_display.sizePolicy().hasHeightForWidth())
        self.output_file_path_display.setSizePolicy(sizePolicy1)
        self.output_file_path_display.setMinimumSize(QSize(300, 30))

        self.pathLayout.addWidget(self.output_file_path_display)


        self.verticalLayout_2.addLayout(self.pathLayout)

        self.trow = QGridLayout()
        self.trow.setSpacing(8)
        self.trow.setObjectName(u"trow")
        self.target_engine = QComboBox(DogeAutoSub)
        self.target_engine.addItem("")
        self.target_engine.addItem("")
        self.target_engine.setObjectName(u"target_engine")
        sizePolicy1.setHeightForWidth(self.target_engine.sizePolicy().hasHeightForWidth())
        self.target_engine.setSizePolicy(sizePolicy1)
        self.target_engine.setMinimumSize(QSize(140, 30))

        self.trow.addWidget(self.target_engine, 3, 1, 1, 1)

        self.target_language_dropdown = QComboBox(DogeAutoSub)
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.addItem("")
        self.target_language_dropdown.setObjectName(u"target_language_dropdown")
        sizePolicy1.setHeightForWidth(self.target_language_dropdown.sizePolicy().hasHeightForWidth())
        self.target_language_dropdown.setSizePolicy(sizePolicy1)
        self.target_language_dropdown.setMinimumSize(QSize(150, 30))

        self.trow.addWidget(self.target_language_dropdown, 1, 1, 1, 1)

        self.target_engine_label = QLabel(DogeAutoSub)
        self.target_engine_label.setObjectName(u"target_engine_label")
        sizePolicy1.setHeightForWidth(self.target_engine_label.sizePolicy().hasHeightForWidth())
        self.target_engine_label.setSizePolicy(sizePolicy1)
        self.target_engine_label.setMinimumSize(QSize(140, 30))

        self.trow.addWidget(self.target_engine_label, 3, 0, 1, 1)

        self.source_language_dropdown = QComboBox(DogeAutoSub)
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.addItem("")
        self.source_language_dropdown.setObjectName(u"source_language_dropdown")
        sizePolicy1.setHeightForWidth(self.source_language_dropdown.sizePolicy().hasHeightForWidth())
        self.source_language_dropdown.setSizePolicy(sizePolicy1)
        self.source_language_dropdown.setMinimumSize(QSize(150, 30))

        self.trow.addWidget(self.source_language_dropdown, 1, 0, 1, 1)

        self.source_language_label = QLabel(DogeAutoSub)
        self.source_language_label.setObjectName(u"source_language_label")
        sizePolicy1.setHeightForWidth(self.source_language_label.sizePolicy().hasHeightForWidth())
        self.source_language_label.setSizePolicy(sizePolicy1)
        self.source_language_label.setMinimumSize(QSize(150, 30))

        self.trow.addWidget(self.source_language_label, 0, 0, 1, 1)

        self.target_language_label = QLabel(DogeAutoSub)
        self.target_language_label.setObjectName(u"target_language_label")
        sizePolicy1.setHeightForWidth(self.target_language_label.sizePolicy().hasHeightForWidth())
        self.target_language_label.setSizePolicy(sizePolicy1)
        self.target_language_label.setMinimumSize(QSize(150, 30))

        self.trow.addWidget(self.target_language_label, 0, 1, 1, 1)

        self.model_size_label = QLabel(DogeAutoSub)
        self.model_size_label.setObjectName(u"model_size_label")
        sizePolicy1.setHeightForWidth(self.model_size_label.sizePolicy().hasHeightForWidth())
        self.model_size_label.setSizePolicy(sizePolicy1)
        self.model_size_label.setMinimumSize(QSize(150, 30))

        self.trow.addWidget(self.model_size_label, 2, 0, 1, 1)

        self.model_size_dropdown = QComboBox(DogeAutoSub)
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.setObjectName(u"model_size_dropdown")
        sizePolicy1.setHeightForWidth(self.model_size_dropdown.sizePolicy().hasHeightForWidth())
        self.model_size_dropdown.setSizePolicy(sizePolicy1)
        self.model_size_dropdown.setMinimumSize(QSize(150, 30))

        self.trow.addWidget(self.model_size_dropdown, 2, 1, 1, 1)

        self.verticalLayout_2.addLayout(self.trow)

        self.start_button = QPushButton(DogeAutoSub)
        self.start_button.setObjectName(u"start_button")
        self.start_button.setMinimumSize(QSize(300, 30))

        self.verticalLayout_2.addWidget(self.start_button)

        self.brow = QGridLayout()
        self.brow.setSpacing(8)
        self.brow.setObjectName(u"brow")

        self.verticalLayout_2.addLayout(self.brow)

        self.retranslateUi(DogeAutoSub)

        QMetaObject.connectSlotsByName(DogeAutoSub)
    # setupUi

    def retranslateUi(self, DogeAutoSub):
        DogeAutoSub.setWindowTitle(QCoreApplication.translate("DogeAutoSub", u"Doge AutoSub", None))
        self.input_file_button.setText(QCoreApplication.translate("DogeAutoSub", u"SELECT INPUT", None))
        self.output_folder_button.setText(QCoreApplication.translate("DogeAutoSub", u"OUTPUT FOLDER", None))
        self.output_file_label.setText(QCoreApplication.translate("DogeAutoSub", u"Output File Path:", None))
        self.output_file_path_display.setText(QCoreApplication.translate("DogeAutoSub", u"No folder selected", None))
        self.target_engine.setItemText(1, QCoreApplication.translate("DogeAutoSub", u"whisper", None))
        self.target_engine.setItemText(0, QCoreApplication.translate("DogeAutoSub", u"google", None))

        self.target_language_dropdown.setItemText(0, QCoreApplication.translate("DogeAutoSub", u"Auto Detect", None))
        self.target_language_dropdown.setItemText(1, QCoreApplication.translate("DogeAutoSub", u"en-US", None))
        self.target_language_dropdown.setItemText(2, QCoreApplication.translate("DogeAutoSub", u"en-GB", None))
        self.target_language_dropdown.setItemText(3, QCoreApplication.translate("DogeAutoSub", u"es-ES", None))
        self.target_language_dropdown.setItemText(4, QCoreApplication.translate("DogeAutoSub", u"zh-CN", None))
        self.target_language_dropdown.setItemText(5, QCoreApplication.translate("DogeAutoSub", u"fr-FR", None))
        self.target_language_dropdown.setItemText(6, QCoreApplication.translate("DogeAutoSub", u"de-DE", None))
        self.target_language_dropdown.setItemText(7, QCoreApplication.translate("DogeAutoSub", u"it-IT", None))
        self.target_language_dropdown.setItemText(8, QCoreApplication.translate("DogeAutoSub", u"cmn-Hans-CN", None))
        self.target_language_dropdown.setItemText(9, QCoreApplication.translate("DogeAutoSub", u"zh-CN", None))
        self.target_language_dropdown.setItemText(10, QCoreApplication.translate("DogeAutoSub", u"ja-JP", None))
        self.target_language_dropdown.setItemText(11, QCoreApplication.translate("DogeAutoSub", u"ko-KR", None))
        self.target_language_dropdown.setItemText(12, QCoreApplication.translate("DogeAutoSub", u"vi-VN", None))

        self.target_engine_label.setText(QCoreApplication.translate("DogeAutoSub", u"Translate Engine:", None))
        
        self.source_language_dropdown.setItemText(0, QCoreApplication.translate("DogeAutoSub", u"Auto Detect", None))
        self.source_language_dropdown.setItemText(1, QCoreApplication.translate("DogeAutoSub", u"en-US", None))
        self.source_language_dropdown.setItemText(2, QCoreApplication.translate("DogeAutoSub", u"en-GB", None))
        self.source_language_dropdown.setItemText(3, QCoreApplication.translate("DogeAutoSub", u"es-ES", None))
        self.source_language_dropdown.setItemText(4, QCoreApplication.translate("DogeAutoSub", u"zh-CN", None))
        self.source_language_dropdown.setItemText(5, QCoreApplication.translate("DogeAutoSub", u"fr-FR", None))
        self.source_language_dropdown.setItemText(6, QCoreApplication.translate("DogeAutoSub", u"de-DE", None))
        self.source_language_dropdown.setItemText(7, QCoreApplication.translate("DogeAutoSub", u"it-IT", None))
        self.source_language_dropdown.setItemText(8, QCoreApplication.translate("DogeAutoSub", u"cmn-Hans-CN", None))
        self.source_language_dropdown.setItemText(9, QCoreApplication.translate("DogeAutoSub", u"zh-CN", None))
        self.source_language_dropdown.setItemText(10, QCoreApplication.translate("DogeAutoSub", u"ja-JP", None))
        self.source_language_dropdown.setItemText(11, QCoreApplication.translate("DogeAutoSub", u"ko-KR", None))
        self.source_language_dropdown.setItemText(12, QCoreApplication.translate("DogeAutoSub", u"vi-VN", None))

        self.source_language_label.setText(QCoreApplication.translate("DogeAutoSub", u"Source Language:", None))
        self.target_language_label.setText(QCoreApplication.translate("DogeAutoSub", u"Translate to:", None))
        self.model_size_label.setText(QCoreApplication.translate("DogeAutoSub", u"Model Size:", None))
        self.model_size_dropdown.setItemText(0, QCoreApplication.translate("DogeAutoSub", u"tiny", None))
        self.model_size_dropdown.setItemText(1, QCoreApplication.translate("DogeAutoSub", u"base", None))
        self.model_size_dropdown.setItemText(2, QCoreApplication.translate("DogeAutoSub", u"small", None))
        self.model_size_dropdown.setItemText(3, QCoreApplication.translate("DogeAutoSub", u"medium", None))
        self.model_size_dropdown.setItemText(4, QCoreApplication.translate("DogeAutoSub", u"large", None))
        self.model_size_dropdown.setItemText(5, QCoreApplication.translate("DogeAutoSub", u"turbo", None))
        self.model_size_dropdown.setCurrentIndex(2)
        self.start_button.setText(QCoreApplication.translate("DogeAutoSub", u"START", None))
    # retranslateUi