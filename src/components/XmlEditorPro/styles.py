QSS = """
QWidget {
    background: #f5f5f7;
    color: #1d1d1f;
    font-family: "SF Pro Display", "SF Pro Text", "PingFang SC", "Helvetica Neue", "Segoe UI", "Noto Sans CJK SC";
    font-size: 13px;
}

QFrame#HeaderBar {
    background: rgba(255, 255, 255, 210);
    border-bottom: 1px solid #d2d2d7;
}

QLabel#LogoIcon {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0a84ff, stop:1 #64d2ff);
    color: #ffffff;
    border-radius: 10px;
    padding: 8px 10px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QLabel#LogoText {
    font-size: 18px;
    font-weight: 700;
    color: #1d1d1f;
}

QFrame#Panel {
    background: #ffffff;
    border-right: 1px solid #d2d2d7;
}

QFrame#PanelRight {
    background: #ffffff;
    border-left: 1px solid #d2d2d7;
}

QFrame#PanelHeader {
    background: #ffffff;
    border-bottom: 1px solid #e5e5ea;
}

QLabel#PanelTitle {
    color: #6e6e73;
    font-weight: 700;
    letter-spacing: 1px;
    font-size: 12px;
}

QPushButton, QToolButton {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    padding: 7px 12px;
    border-radius: 10px;
    color: #1d1d1f;
}

QPushButton:hover, QToolButton:hover {
    background: #f2f2f7;
    border-color: #c7c7cc;
}

QPushButton:pressed, QToolButton:pressed {
    background: #e5e5ea;
}

QPushButton#PrimaryButton {
    background: #0a84ff;
    border: 1px solid rgba(10, 132, 255, 190);
    font-weight: 700;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background: #007aff;
}

QPushButton#SuccessButton {
    background: #34c759;
    border: 1px solid rgba(52, 199, 89, 190);
    font-weight: 700;
    color: #ffffff;
}

QPushButton#DangerButton {
    background: #ff3b30;
    border: 1px solid rgba(255, 59, 48, 190);
    font-weight: 700;
    color: #ffffff;
}

QLineEdit, QPlainTextEdit, QTextEdit {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 10px;
    padding: 10px 12px;
    selection-background-color: rgba(10, 132, 255, 80);
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #0a84ff;
    outline: none;
}

QSplitter::handle {
    background: #d2d2d7;
}

QTreeWidget {
    background: transparent;
    border: none;
    outline: none;
}

QTreeWidget::item {
    padding: 7px 10px;
    border-radius: 10px;
    margin: 2px 6px;
}

QTreeWidget::item:hover {
    background: #f2f2f7;
}

QTreeWidget::item:selected {
    background: rgba(10, 132, 255, 32);
    border: 1px solid rgba(10, 132, 255, 90);
    color: #003366;
}

QTableWidget {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
}

QTableWidget::item {
    padding: 1px 1px;
    border-bottom: 1px solid #f2f2f7;
    background: #ffffff;
}
QTableWidget::item:focus {
    border: 2px solid #0a84ff;
    padding: 1px 1px;
}

QTableWidget QLineEdit {
    border-radius: 8px;
    padding: 3px 6px;
}

QTableWidget::item:selected {
    background: rgba(10, 132, 255, 32);
    color: #003366;
}

QTableCornerButton::section {
    background: #f5f5f7;
    border: none;
}

QHeaderView::section {
    background: #f5f5f7;
    border: none;
    border-bottom: 1px solid #e5e5ea;
    padding: 8px 10px;
    color: #6e6e73;
    font-weight: 700;
}

QTabWidget::pane {
    border: none;
}

QTabBar::tab {
    background: transparent;
    border: none;
    padding: 12px 16px;
    color: #6e6e73;
    font-weight: 700;
}

QTabBar::tab:hover {
    color: #1d1d1f;
}

QTabBar::tab:selected {
    color: #0a84ff;
    border-bottom: 2px solid #0a84ff;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px 2px 2px 2px;
}

QScrollBar::handle:vertical {
    background: #c7c7cc;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #aeaeb2;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMenu {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 12px;
    border-radius: 10px;
    color: #1d1d1f;
}

QMenu::item:selected {
    background: #f2f2f7;
}

QDialog {
    background: #ffffff;
}

QFrame#Toast {
    background: rgba(255, 255, 255, 235);
    border: 1px solid #d2d2d7;
    border-radius: 12px;
}
"""
