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
from DataReplay.data_replay_demo import DataReplayForm
from CustomWidgets.gallary import GallaryForm
from ResourceQuery.ResourceQueryTool import ResourceQueryTool


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
    # 用于跟踪已打开的窗口实例
    _open_windows = {}
    
    def __init__(self, svg_path: str, title: str, description: str, window_class=None, parent=None):
        super().__init__()
        self.title = title
        self.window_class = window_class

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)

        # 左侧 SVG 图标
        svg_path = str(Path(__file__).parent / f'assets/icon/{svg_path}')
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
            # 检查该窗口类是否已经有实例打开
            window_class_name = self.window_class.__name__
            
            if window_class_name in self._open_windows:
                existing_window = self._open_windows[window_class_name]
                # 检查窗口是否仍然存在且有效
                try:
                    # 尝试访问窗口属性来检查窗口是否仍然有效
                    if existing_window and existing_window.isVisible():
                        # 如果窗口已存在且可见，将其置于前台并激活
                        existing_window.raise_()
                        existing_window.activateWindow()
                        print(f"{self.title} 窗口已经打开，将其置于前台")
                        return
                    elif existing_window and not existing_window.isVisible():
                        existing_window.show()
                        existing_window.raise_()
                        existing_window.activateWindow()
                        print(f"{self.title} 窗口已恢复显示")
                        return
                except RuntimeError:
                    # 窗口对象已被删除，从字典中移除
                    del self._open_windows[window_class_name]
                    print(f"{self.title} 窗口对象已失效，将创建新窗口")
            
            # 创建新的窗口实例
            new_window = self.window_class()
            self._open_windows[window_class_name] = new_window
            
            # 连接窗口关闭信号，以便在窗口关闭时从字典中移除
            def on_window_closed():
                try:
                    if window_class_name in self._open_windows:
                        del self._open_windows[window_class_name]
                        print(f"{self.title} 窗口已关闭并从管理器中移除")
                except:
                    pass
            
            # 连接多个信号以确保窗口关闭时能被正确检测
            if hasattr(new_window, 'destroyed'):
                new_window.destroyed.connect(on_window_closed)
            if hasattr(new_window, 'finished'):
                new_window.finished.connect(on_window_closed)
            if hasattr(new_window, 'closeEvent'):
                # 重写closeEvent来确保窗口关闭时清理引用
                original_close_event = new_window.closeEvent
                def custom_close_event(event):
                    on_window_closed()
                    original_close_event(event)
                new_window.closeEvent = custom_close_event
            
            new_window.show()
            print(f"打开了新的 {self.title} 窗口")


class ScrollCardList(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("正经工具箱")
        self.resize(600, 800)
        self.setWindowIcon(QIcon(str(Path(__file__).parent / 'assets/icon/fill-shit-ac.svg')))

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
                "description": "支持加载 CSV 文件并以图表形式回放历史数据",
                "window_class": DataReplayForm  
            },
            {
                "svg_path": "仪表盘.svg",
                "title": "实时曲线",
                "description": "实时接收来自串口、网络或其他传感器接口的数据流，并以图形化方式展示其变化趋势",
                "window_class": DataPlotForm  
            },
            {
                "svg_path": "文件文档.svg",
                "title": "日志查看",
                "description": "支持按日期查看历史日志以及按类型分类查看，支持选择对应期限的文件删除",
                "window_class": LogCheckForm  
            },
            {
                "svg_path": "灯泡主意创新.svg",
                "title": "状态监控",
                "description": "这是一个状态监控工具。",
                "window_class": BulbStateMonitor  
            },
            {
                "svg_path": "数据线.svg",
                "title": "总线数据解析",
                "description": "这是一个总线数据解析工具",
                "window_class": None  # 暂时不绑定窗口
            },
            {
                "svg_path": "中央处理器.svg",
                "title": "资源索引查询",
                "description": "多维度测试资源索引查询",
                "window_class": ResourceQueryTool
            },
            {
                "svg_path": "草稿便签编辑.svg",
                "title": "自定义控件",
                "description": "这是一个自定义绘制的控件集，有仪表盘等控件",
                "window_class": GallaryForm  
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
    # app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))  # 设置现代字体

    window = ScrollCardList()
    window.show()
    sys.exit(app.exec_())
