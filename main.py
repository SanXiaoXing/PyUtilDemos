import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from CalibTool.calib_tool_demo import CalibrationForm
from RTDataPlot.RTdata_plot_demo import DataPlotForm
from LogViewer.log_viewer_demo import LogCheckForm
from BulbStateMonitor.bulb_statemonitor_demo import BulbStateMonitor





class HoverFrame(QFrame):
    clicked = pyqtSignal()

    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

        # 初始化阴影效果
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setOffset(0, 4)
        self.shadow_effect.setColor(QColor(0, 0, 0, 50))  # 阴影透明度
        self.setGraphicsEffect(self.shadow_effect)
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
                border-radius: 8px;
                padding: 10px;

            }
        """

    def hover_style(self):
        return """
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #3399ff;
                border-radius: 8px;
                padding: 10px;
  
            }
        """




class CardWidget(HoverFrame):
    def __init__(self, svg_path: str, title: str, description: str, window_class=None, parent=None):
        super().__init__()
        self.title = title
        self.window_class = window_class

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)

        # 左侧 SVG 图标
        svg_path=str(Path(__file__) .parent/ f'assets/icon/{svg_path}')
        svg_widget = QSvgWidget(svg_path)
        svg_widget.setFixedSize(QSize(60, 60))
        layout.addWidget(svg_widget)

        # 右侧文字（无边框）
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        title_label = QLabel(title)
        title_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title_label.setStyleSheet("border: none;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("微软雅黑", 10))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555555; font-size: 10pt; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout)
        self.setLayout(layout)

        self.clicked.connect(self.on_click)

    def on_click(self):
        print(f"点击了卡片: {self.title}")
        if self.window_class:
            self._window = self.window_class()  # 保存引用
            self._window.show()







class ScrollCardList(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("正经工具箱")
        self.resize(600, 800)
        self.setWindowIcon(QIcon(str(Path(__file__) .parent/ 'assets/icon/fill-shit-ac.svg')))

        # 主布局
        main_layout = QVBoxLayout(self)

        # 滚动区域设置
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 2px 0 2px 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 100, 100, 0.4);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(80, 80, 80, 0.6);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0 2px 0 2px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(100, 100, 100, 0.4);
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(80, 80, 80, 0.6);
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)


        # 卡片容器 Widget + 布局
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(10, 10, 10, 10)

        card_data = [
            {
                "svg_path": "计算.svg",
                "title": "校准工具",
                "description": "采用线性插值的方式实现数据校准",
                "window_class": CalibrationForm
            },
            {
                "svg_path": "分析统计.svg",
                "title": "数据回放",
                "description": "支持加载 CSV 文件并以图表形式回放历史数据，用户可以通过控制按钮实现播放、暂停、停止等操作",
                "window_class": None  # 暂时不绑定窗口
            },
            {
                "svg_path": "仪表盘.svg",
                "title": "实时曲线",
                "description": "实时接收来自串口、网络或其他传感器接口的数据流，并以图形化方式展示其变化趋势",
                "window_class": DataPlotForm  # 暂时不绑定窗口
            },
            {
                "svg_path": "文件文档.svg",
                "title": "日志查看",
                "description": "支持按日期查看历史日志以及按类型分类查看，支持选择对应期限的文件删除",
                "window_class": LogCheckForm  # 暂时不绑定窗口
            },
            {
                "svg_path": "灯泡主意创新.svg",
                "title": "状态监控",
                "description": "这是一个状态监控工具。",
                "window_class": BulbStateMonitor  # 暂时不绑定窗口
            },
            {
                "svg_path": "数据线.svg",
                "title": "总线数据解析",
                "description": "这是一个总线数据解析工具",
                "window_class": None  # 暂时不绑定窗口
            },
        ]
        
        for data in card_data:
            card = CardWidget(
                data["svg_path"],
                data["title"], 
                data["description"],
                data.get("window_class"))  # 传递窗口类)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            content_layout.addWidget(card)

        content_layout.addStretch()  # 防止最后一个卡片贴底部
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)








if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置现代风格样式
    #app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))  # 设置现代字体

    window = ScrollCardList()
    window.show()
    sys.exit(app.exec_())

