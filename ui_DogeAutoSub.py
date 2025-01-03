# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DogeAutoSubtnFCMh.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QSizePolicy, QSlider, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(500, 750)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QSize(500, 750))
        Dialog.setMaximumSize(QSize(500, 750))
        icon = QIcon()
        icon.addFile(u"../icons/favicon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setStyleSheet(u"")
        self.verticalLayout_2 = QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.InOutLayout = QFrame(Dialog)
        self.InOutLayout.setObjectName(u"InOutLayout")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.InOutLayout.sizePolicy().hasHeightForWidth())
        self.InOutLayout.setSizePolicy(sizePolicy1)
        self.InOutLayout.setMinimumSize(QSize(0, 0))
        self.InOutLayout.setMaximumSize(QSize(16777215, 50))
        self.InOutLayout.setFrameShape(QFrame.Shape.StyledPanel)
        self.InOutLayout.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.InOutLayout)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.input_file_button = QPushButton(self.InOutLayout)
        self.input_file_button.setObjectName(u"input_file_button")

        self.horizontalLayout.addWidget(self.input_file_button)

        self.output_folder_button = QPushButton(self.InOutLayout)
        self.output_folder_button.setObjectName(u"output_folder_button")

        self.horizontalLayout.addWidget(self.output_folder_button)

        self.openBtn = QPushButton(self.InOutLayout)
        self.openBtn.setObjectName(u"openBtn")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.openBtn.sizePolicy().hasHeightForWidth())
        self.openBtn.setSizePolicy(sizePolicy2)
        self.openBtn.setMinimumSize(QSize(32, 0))
        self.openBtn.setMaximumSize(QSize(32, 16777215))
        icon1 = QIcon()
        icon1.addFile(u"../icons/folder.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.openBtn.setIcon(icon1)

        self.horizontalLayout.addWidget(self.openBtn)

        self.themeBtn = QPushButton(self.InOutLayout)
        self.themeBtn.setObjectName(u"themeBtn")
        sizePolicy2.setHeightForWidth(self.themeBtn.sizePolicy().hasHeightForWidth())
        self.themeBtn.setSizePolicy(sizePolicy2)
        self.themeBtn.setMinimumSize(QSize(32, 0))
        self.themeBtn.setMaximumSize(QSize(32, 16777215))
        icon2 = QIcon()
        icon2.addFile(u"../icons/paint.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.themeBtn.setIcon(icon2)

        self.horizontalLayout.addWidget(self.themeBtn)


        self.verticalLayout_2.addWidget(self.InOutLayout)

        self.pathLayout = QFrame(Dialog)
        self.pathLayout.setObjectName(u"pathLayout")
        self.pathLayout.setMaximumSize(QSize(16777215, 50))
        self.pathLayout.setFrameShape(QFrame.Shape.StyledPanel)
        self.pathLayout.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.pathLayout)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.output_file_label = QLabel(self.pathLayout)
        self.output_file_label.setObjectName(u"output_file_label")
        sizePolicy1.setHeightForWidth(self.output_file_label.sizePolicy().hasHeightForWidth())
        self.output_file_label.setSizePolicy(sizePolicy1)
        self.output_file_label.setMinimumSize(QSize(0, 0))
        self.output_file_label.setMaximumSize(QSize(16777215, 50))
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setBold(True)
        self.output_file_label.setFont(font)

        self.horizontalLayout_4.addWidget(self.output_file_label)

        self.output_file_path_display = QLabel(self.pathLayout)
        self.output_file_path_display.setObjectName(u"output_file_path_display")
        self.output_file_path_display.setMinimumSize(QSize(0, 0))
        self.output_file_path_display.setMaximumSize(QSize(16777215, 50))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        self.output_file_path_display.setFont(font1)

        self.horizontalLayout_4.addWidget(self.output_file_path_display)


        self.verticalLayout_2.addWidget(self.pathLayout)

        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setMaximumSize(QSize(16777215, 50))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.output_file_label_2 = QLabel(self.frame)
        self.output_file_label_2.setObjectName(u"output_file_label_2")
        sizePolicy1.setHeightForWidth(self.output_file_label_2.sizePolicy().hasHeightForWidth())
        self.output_file_label_2.setSizePolicy(sizePolicy1)
        self.output_file_label_2.setMinimumSize(QSize(80, 0))
        self.output_file_label_2.setMaximumSize(QSize(150, 50))
        self.output_file_label_2.setFont(font)

        self.horizontalLayout_5.addWidget(self.output_file_label_2)

        self.boostSlider = QSlider(self.frame)
        self.boostSlider.setObjectName(u"boostSlider")
        self.boostSlider.setMinimum(1)
        self.boostSlider.setMaximum(10)
        self.boostSlider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_5.addWidget(self.boostSlider)

        self.boostLb = QLabel(self.frame)
        self.boostLb.setObjectName(u"boostLb")
        self.boostLb.setMinimumSize(QSize(80, 0))
        self.boostLb.setMaximumSize(QSize(80, 50))

        self.horizontalLayout_5.addWidget(self.boostLb)


        self.verticalLayout_2.addWidget(self.frame)

        self.modelFrame = QFrame(Dialog)
        self.modelFrame.setObjectName(u"modelFrame")
        self.modelFrame.setMinimumSize(QSize(0, 0))
        self.modelFrame.setMaximumSize(QSize(16777215, 50))
        self.modelFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.modelFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.modelFrame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.model_size_label = QLabel(self.modelFrame)
        self.model_size_label.setObjectName(u"model_size_label")
        sizePolicy2.setHeightForWidth(self.model_size_label.sizePolicy().hasHeightForWidth())
        self.model_size_label.setSizePolicy(sizePolicy2)
        self.model_size_label.setMinimumSize(QSize(90, 0))
        self.model_size_label.setMaximumSize(QSize(80, 100))
        self.model_size_label.setFont(font)

        self.horizontalLayout_2.addWidget(self.model_size_label)

        self.model_size_dropdown = QComboBox(self.modelFrame)
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.addItem("")
        self.model_size_dropdown.setObjectName(u"model_size_dropdown")
        sizePolicy2.setHeightForWidth(self.model_size_dropdown.sizePolicy().hasHeightForWidth())
        self.model_size_dropdown.setSizePolicy(sizePolicy2)
        self.model_size_dropdown.setMinimumSize(QSize(80, 0))
        self.model_size_dropdown.setMaximumSize(QSize(80, 50))
        self.model_size_dropdown.setFont(font1)

        self.horizontalLayout_2.addWidget(self.model_size_dropdown)

        self.label = QLabel(self.modelFrame)
        self.label.setObjectName(u"label")
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)
        self.label.setMinimumSize(QSize(60, 0))
        self.label.setMaximumSize(QSize(60, 100))

        self.horizontalLayout_2.addWidget(self.label)

        self.VRamUsage = QLabel(self.modelFrame)
        self.VRamUsage.setObjectName(u"VRamUsage")
        sizePolicy2.setHeightForWidth(self.VRamUsage.sizePolicy().hasHeightForWidth())
        self.VRamUsage.setSizePolicy(sizePolicy2)
        self.VRamUsage.setMinimumSize(QSize(40, 0))
        self.VRamUsage.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_2.addWidget(self.VRamUsage)

        self.label_2 = QLabel(self.modelFrame)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setMinimumSize(QSize(60, 0))
        self.label_2.setMaximumSize(QSize(80, 100))

        self.horizontalLayout_2.addWidget(self.label_2)

        self.rSpeed = QLabel(self.modelFrame)
        self.rSpeed.setObjectName(u"rSpeed")
        sizePolicy2.setHeightForWidth(self.rSpeed.sizePolicy().hasHeightForWidth())
        self.rSpeed.setSizePolicy(sizePolicy2)
        self.rSpeed.setMinimumSize(QSize(40, 0))
        self.rSpeed.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_2.addWidget(self.rSpeed)


        self.verticalLayout_2.addWidget(self.modelFrame)

        self.translateFrame = QFrame(Dialog)
        self.translateFrame.setObjectName(u"translateFrame")
        self.translateFrame.setMaximumSize(QSize(16777215, 130))
        self.translateFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.translateFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.translateFrame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.source_language_label = QLabel(self.translateFrame)
        self.source_language_label.setObjectName(u"source_language_label")
        self.source_language_label.setMaximumSize(QSize(200, 50))
        self.source_language_label.setFont(font)

        self.gridLayout_2.addWidget(self.source_language_label, 0, 0, 1, 1)

        self.target_language_label = QLabel(self.translateFrame)
        self.target_language_label.setObjectName(u"target_language_label")
        self.target_language_label.setMaximumSize(QSize(200, 50))
        self.target_language_label.setFont(font)

        self.gridLayout_2.addWidget(self.target_language_label, 0, 1, 1, 1)

        self.source_language_dropdown = QComboBox(self.translateFrame)
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
        self.source_language_dropdown.setMaximumSize(QSize(200, 16777215))
        self.source_language_dropdown.setFont(font1)

        self.gridLayout_2.addWidget(self.source_language_dropdown, 1, 0, 1, 1)

        self.target_language_dropdown = QComboBox(self.translateFrame)
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
        self.target_language_dropdown.setMaximumSize(QSize(200, 16777215))
        self.target_language_dropdown.setFont(font1)

        self.gridLayout_2.addWidget(self.target_language_dropdown, 1, 1, 1, 1)

        self.target_engine_label = QLabel(self.translateFrame)
        self.target_engine_label.setObjectName(u"target_engine_label")
        self.target_engine_label.setMaximumSize(QSize(200, 50))
        self.target_engine_label.setFont(font)

        self.gridLayout_2.addWidget(self.target_engine_label, 2, 0, 1, 1)

        self.target_engine = QComboBox(self.translateFrame)
        self.target_engine.addItem("")
        self.target_engine.addItem("")
        self.target_engine.setObjectName(u"target_engine")
        self.target_engine.setMaximumSize(QSize(200, 16777215))
        self.target_engine.setFont(font1)

        self.gridLayout_2.addWidget(self.target_engine, 2, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.translateFrame)

        self.startFrame = QFrame(Dialog)
        self.startFrame.setObjectName(u"startFrame")
        self.startFrame.setMinimumSize(QSize(0, 0))
        self.startFrame.setMaximumSize(QSize(16777215, 50))
        self.startFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.startFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.startFrame)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.start_button = QPushButton(self.startFrame)
        self.start_button.setObjectName(u"start_button")

        self.horizontalLayout_3.addWidget(self.start_button)


        self.verticalLayout_2.addWidget(self.startFrame)

        self.statusFrame = QFrame(Dialog)
        self.statusFrame.setObjectName(u"statusFrame")
        self.statusFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.statusFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.statusFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.progressBar = QProgressBar(self.statusFrame)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.verticalLayout.addWidget(self.progressBar)

        self.statusLb = QLabel(self.statusFrame)
        self.statusLb.setObjectName(u"statusLb")
        self.statusLb.setMinimumSize(QSize(300, 0))
        self.statusLb.setMaximumSize(QSize(300, 30))

        self.verticalLayout.addWidget(self.statusLb)

        self.estlb = QLabel(self.statusFrame)
        self.estlb.setObjectName(u"estlb")
        self.estlb.setMinimumSize(QSize(300, 0))
        self.estlb.setMaximumSize(QSize(300, 30))

        self.verticalLayout.addWidget(self.estlb)

        self.statusimage = QLabel(self.statusFrame)
        self.statusimage.setObjectName(u"statusimage")
        self.statusimage.setMaximumSize(QSize(150, 150))

        self.verticalLayout.addWidget(self.statusimage)


        self.verticalLayout_2.addWidget(self.statusFrame)


        self.retranslateUi(Dialog)
        self.boostSlider.valueChanged.connect(self.boostLb.setNum)

        self.model_size_dropdown.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"DOGE AUTOSUB", None))
#if QT_CONFIG(tooltip)
        self.input_file_button.setToolTip(QCoreApplication.translate("Dialog", u"source file", None))
#endif // QT_CONFIG(tooltip)
        self.input_file_button.setText(QCoreApplication.translate("Dialog", u"SOURCE FILE", None))
#if QT_CONFIG(tooltip)
        self.output_folder_button.setToolTip(QCoreApplication.translate("Dialog", u"choose output folder", None))
#endif // QT_CONFIG(tooltip)
        self.output_folder_button.setText(QCoreApplication.translate("Dialog", u"OUTPUT FOLDER ", None))
#if QT_CONFIG(tooltip)
        self.openBtn.setToolTip(QCoreApplication.translate("Dialog", u"open output folder", None))
#endif // QT_CONFIG(tooltip)
        self.openBtn.setText("")
#if QT_CONFIG(tooltip)
        self.themeBtn.setToolTip(QCoreApplication.translate("Dialog", u"change themes", None))
#endif // QT_CONFIG(tooltip)
        self.themeBtn.setText("")
        self.output_file_label.setText(QCoreApplication.translate("Dialog", u"OUTPUT FILE PATH :", None))
        self.output_file_path_display.setText(QCoreApplication.translate("Dialog", u"no files selected", None))
#if QT_CONFIG(tooltip)
        self.output_file_label_2.setToolTip(QCoreApplication.translate("Dialog", u"Try increase the volume if the original volumes was too low", None))
#endif // QT_CONFIG(tooltip)
        self.output_file_label_2.setText(QCoreApplication.translate("Dialog", u"VOLUME BOOST :", None))
#if QT_CONFIG(tooltip)
        self.boostSlider.setToolTip(QCoreApplication.translate("Dialog", u"Try increase the volume if the original volumes was too low", None))
#endif // QT_CONFIG(tooltip)
        self.boostLb.setText(QCoreApplication.translate("Dialog", u"1", None))
        self.model_size_label.setText(QCoreApplication.translate("Dialog", u"Model Size :", None))
        self.model_size_dropdown.setItemText(0, QCoreApplication.translate("Dialog", u"base", None))
        self.model_size_dropdown.setItemText(1, QCoreApplication.translate("Dialog", u"tiny", None))
        self.model_size_dropdown.setItemText(2, QCoreApplication.translate("Dialog", u"small", None))
        self.model_size_dropdown.setItemText(3, QCoreApplication.translate("Dialog", u"medium", None))
        self.model_size_dropdown.setItemText(4, QCoreApplication.translate("Dialog", u"large", None))
        self.model_size_dropdown.setItemText(5, QCoreApplication.translate("Dialog", u"turbo", None))

#if QT_CONFIG(tooltip)
        self.model_size_dropdown.setToolTip(QCoreApplication.translate("Dialog", u"change model size", None))
#endif // QT_CONFIG(tooltip)
        self.model_size_dropdown.setCurrentText(QCoreApplication.translate("Dialog", u"small", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"VRAM:", None))
#if QT_CONFIG(tooltip)
        self.VRamUsage.setToolTip(QCoreApplication.translate("Dialog", u"Required VRAM", None))
#endif // QT_CONFIG(tooltip)
        self.VRamUsage.setText(QCoreApplication.translate("Dialog", u"2 GB", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"SPEED:", None))
#if QT_CONFIG(tooltip)
        self.rSpeed.setToolTip(QCoreApplication.translate("Dialog", u"Relative Speed", None))
#endif // QT_CONFIG(tooltip)
        self.rSpeed.setText(QCoreApplication.translate("Dialog", u"4x", None))
        self.source_language_label.setText(QCoreApplication.translate("Dialog", u"Source Language :", None))
        self.target_language_label.setText(QCoreApplication.translate("Dialog", u"Translate To :", None))
        self.source_language_dropdown.setItemText(0, QCoreApplication.translate("Dialog", u"Auto Detect", None))
        self.source_language_dropdown.setItemText(1, QCoreApplication.translate("Dialog", u"English", None))
        self.source_language_dropdown.setItemText(2, QCoreApplication.translate("Dialog", u"Chinese", None))
        self.source_language_dropdown.setItemText(3, QCoreApplication.translate("Dialog", u"Japanese", None))
        self.source_language_dropdown.setItemText(4, QCoreApplication.translate("Dialog", u"Korean", None))
        self.source_language_dropdown.setItemText(5, QCoreApplication.translate("Dialog", u"German", None))
        self.source_language_dropdown.setItemText(6, QCoreApplication.translate("Dialog", u"Spanish", None))
        self.source_language_dropdown.setItemText(7, QCoreApplication.translate("Dialog", u"Russian", None))
        self.source_language_dropdown.setItemText(8, QCoreApplication.translate("Dialog", u"French", None))
        self.source_language_dropdown.setItemText(9, QCoreApplication.translate("Dialog", u"Vietnamese", None))
        self.source_language_dropdown.setItemText(10, QCoreApplication.translate("Dialog", u"Thai", None))

#if QT_CONFIG(tooltip)
        self.source_language_dropdown.setToolTip(QCoreApplication.translate("Dialog", u"Source language. If not sure, just leave it as default ", None))
#endif // QT_CONFIG(tooltip)
        self.target_language_dropdown.setItemText(0, QCoreApplication.translate("Dialog", u"Auto Detect", None))
        self.target_language_dropdown.setItemText(1, QCoreApplication.translate("Dialog", u"English", None))
        self.target_language_dropdown.setItemText(2, QCoreApplication.translate("Dialog", u"Chinese", None))
        self.target_language_dropdown.setItemText(3, QCoreApplication.translate("Dialog", u"Japanese", None))
        self.target_language_dropdown.setItemText(4, QCoreApplication.translate("Dialog", u"Korean", None))
        self.target_language_dropdown.setItemText(5, QCoreApplication.translate("Dialog", u"German", None))
        self.target_language_dropdown.setItemText(6, QCoreApplication.translate("Dialog", u"Spanish", None))
        self.target_language_dropdown.setItemText(7, QCoreApplication.translate("Dialog", u"Russian", None))
        self.target_language_dropdown.setItemText(8, QCoreApplication.translate("Dialog", u"French", None))
        self.target_language_dropdown.setItemText(9, QCoreApplication.translate("Dialog", u"Vietnamese", None))
        self.target_language_dropdown.setItemText(10, QCoreApplication.translate("Dialog", u"Thai", None))

#if QT_CONFIG(tooltip)
        self.target_language_dropdown.setToolTip(QCoreApplication.translate("Dialog", u"Change to language that you want to translate the subtitle to.", None))
#endif // QT_CONFIG(tooltip)
        self.target_engine_label.setText(QCoreApplication.translate("Dialog", u"Translate Engine :", None))
        self.target_engine.setItemText(0, QCoreApplication.translate("Dialog", u"google", None))
        self.target_engine.setItemText(1, QCoreApplication.translate("Dialog", u"whisper", None))

#if QT_CONFIG(tooltip)
        self.target_engine.setToolTip(QCoreApplication.translate("Dialog", u"better use whisper to translate from other languages to english", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.start_button.setToolTip(QCoreApplication.translate("Dialog", u"Start the Doge", None))
#endif // QT_CONFIG(tooltip)
        self.start_button.setText(QCoreApplication.translate("Dialog", u"START", None))
#if QT_CONFIG(tooltip)
        self.progressBar.setToolTip(QCoreApplication.translate("Dialog", u"This is just for show, not really working at all ", None))
#endif // QT_CONFIG(tooltip)
        self.statusLb.setText(QCoreApplication.translate("Dialog", u"Standby", None))
        self.estlb.setText(QCoreApplication.translate("Dialog", u"Estimate: ", None))
        self.statusimage.setText("")
    # retranslateUi

