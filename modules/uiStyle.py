class Style():

    style_bt_standard = (
        """
        QPushButton {
            background-color: #F29325;
            color: #002333;
            border: none;
            text-align: center;
            border-radius: 10px;
            font-size: 12px;
            padding: 10px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #D94F04;
            color: #BFBFBF;
        }
        
        QPushButton:pressed {
            background-color: #C2BB00;
            color: #FFFFFF;
        }
        
        QComboBox {
            border: 1px solid #F29325;
            border-radius: 10px;
            padding: 5px;
            font-size: 14px;
            background-color: #747E7E;
            color: #002333;
        }
        
        QComboBox:hover {
            border: 3px solid #D94F04;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left-width: 1px;
            border-left-color: #F29325;
            border-left-style: solid;
            background-color: #F29325;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        }
        
        QComboBox::down-arrow {
            image: url(icons/drop-down-menu.png);
            width: 16px;
            height: 16px;
        }
        
        QLabel {
            color: #002333;
            font-size: 12px;
            background-color: transparent;
            border: none;
        }
        """
        
    )
    
    styleLable = (
        """
        QLabel {
            color: #002333;
            font-size: 14px;
            background-color: transparent;
            border: none;
        }
        """
    )
    
    styleLineEdit = (
    """
    QLineEdit {
        border: 2px solid #BFBFBF;
        border-radius: 10px;
        padding: 5px;
        font-size: 14px;
        background-color: #2E2E2E;
        color: #BFBFBF;
    }
    
    QLineEdit:hover {
        border: 2px solid #8AA6A3;
    }
    """
    )

    stylePlainTextEdit = (
    """
    QPlainTextEdit {
        border: 2px solid #BFBFBF;
        border-radius: 10px;
        padding: 5px;
        font-size: 14px;
        background-color: #2E2E2E;
        color: #BFBFBF;
    }
    
    QPlainTextEdit:hover {
        border: 2px solid #8AA6A3;
    }
    """
    )
    ProcessLable = (
        """
        QLabel {
            color: #002333;
            font-size: 16px;
            background-color: transparent;
            border: none;
        }
        """
    )
