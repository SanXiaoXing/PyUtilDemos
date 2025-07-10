import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QSizePolicy
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont


class HoverFrame(QFrame):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self.default_style())

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style())
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def default_style(self):
        return """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dddddd;
                border-radius: 10px;
                padding: 10px;
            }
        """

    def hover_style(self):
        return """
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #3399ff;
                border-radius: 10px;
                padding: 10px;
            }
        """


class CardWidget(HoverFrame):
    def __init__(self, svg_path: str, title: str, description: str, parent=None):
        super().__init__()
        self.title = title  # 用于点击事件中使用

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 左侧 SVG 图标
        svg_widget = QSvgWidget(svg_path)
        svg_widget.setFixedSize(QSize(48, 48))
        layout.addWidget(svg_widget)

        # 右侧文字
        text_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #555555; font-size: 10pt;")
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout)
        self.setLayout(layout)

        # 绑定点击事件
        self.clicked.connect(self.on_click)

    def on_click(self):
        print(f"点击了卡片: {self.title}")


class CardGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("卡片网格（含SVG、Hover、点击）")
        self.resize(1000, 600)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # 添加 8 个卡片
        for i in range(8):
            svg_path = "icon.svg"  # 替换成你本地 SVG 路径
            title = f"功能模块 {i+1}"
            desc = "这里是功能的简要描述，可以包含多行内容，用于介绍模块用途。"
            card = CardWidget(svg_path, title, desc)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row = i // 4
            col = i % 4
            grid_layout.addWidget(card, row, col)

        self.setLayout(grid_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CardGrid()
    window.show()
    sys.exit(app.exec_())
