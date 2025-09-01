import sys
import os
import queue
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.components.BusDataMonitor.monitor.busdata_producer import RS422Manager
from src.components.BusDataMonitor.monitor.dock_monitor import DataMonitor
from src.components.BusDataMonitor.monitor.dock_parser import DockParser
from src.components.BusDataMonitor.config import channel_config
from assets import ICON_TABLE

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000
DEFAULT_REFRESH_MS = 300


class BusDataMonitorForm(QMainWindow):
    def __init__(self):  
        super().__init__()
        self.init_ui()
        self.channel_config=channel_config
        # >>> 使用 RS422Manager 创建所有 producer/queue
        self.manager = RS422Manager(self.channel_config, use_sim=True)
        self.manager.start_all()

        # 动态保存 dock monitor 引用
        self.dock_monitors = {}  # key = ch_id , value = dock widget

        # 根据配置动态创建 toolbar action
        self.create_channel_actions()
        self.init_toolbtn()

    def init_ui(self):
        self.setWindowTitle("总线数据监控")
        self.resize(1000, 800)
        self.toolBar = self.addToolBar("Main Toolbar")  
        self.toolBar.setMovable(False)
        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)


    def init_toolbtn(self):
        # 创建占位 widget
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolBar.addWidget(spacer)  # 添加到 toolbar 中，前面的按钮会被推到左边

        # 然后再添加你的右侧按钮
        self.btn_layout = QAction(QIcon(ICON_TABLE), "默认布局", self)
        self.btn_layout.triggered.connect(self.reset_layout)
        self.toolBar.addAction(self.btn_layout)


    def create_channel_actions(self):
        """遍历 manager.producers，为每个通道动态添加按钮"""
        for ch_id, producers in self.manager.producers.items():
            # 创建一个按钮：标题为通道ID
            act = QAction(f"通道 {ch_id}", self)
            act.triggered.connect(lambda _, cid=ch_id: self.show_channel_monitor(cid))
            self.toolBar.addAction(act)

    def show_channel_monitor(self, ch_id):
        """显示对应通道的 DataMonitor dock"""
        if ch_id in self.dock_monitors:
            dock = self.dock_monitors[ch_id]
            dock.raise_()
            dock.show()
            return

        # >>> 取对应队列
        q = self.manager.queues[ch_id]

        # 创建 DataMonitor
        monitor = DataMonitor(f"通道 {ch_id} 数据监控", data_queue=q, channel_id=ch_id)
        dock = QDockWidget(f"通道 {ch_id} 数据监控", self)
        dock.setWidget(monitor)
        dock.setObjectName(f"Dock_{ch_id}")
        dock.setFeatures(QDockWidget.DockWidgetMovable | 
                         QDockWidget.DockWidgetClosable | 
                         QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.dock_monitors[ch_id] = dock

        # 双击行显示解析窗口
        monitor.row_double_clicked.connect(self.show_parsed_dock)
        dock.show()


    def show_parsed_dock(self, hex_str, protocol, index, source):
        parser = DockParser(protocol, index, self)
        dock = QDockWidget(f"{source.upper()} 解析", self)
        dock.setWidget(parser)
        dock.setFeatures(QDockWidget.DockWidgetMovable | 
                         QDockWidget.DockWidgetClosable | 
                         QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        dock.update_data(hex_str)
        dock.show()


    def reset_layout(self):
        """恢复 Dock 布局"""
        docks = list(self.dock_monitors.values())
        if not docks:
            return
        for d in docks:
            d.setFloating(False)
        if len(docks) == 1:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            return
        if len(docks) == 2:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            self.addDockWidget(Qt.RightDockWidgetArea, docks[1])
            return
        # 超过2个 → 强制2×2布局
        left_col, right_col = [], []
        for i, dock in enumerate(docks):
            (left_col if i % 2 == 0 else right_col).append(dock)
        if left_col:
            self.addDockWidget(Qt.LeftDockWidgetArea, left_col[0])
            for d in left_col[1:]:
                self.splitDockWidget(left_col[0], d, Qt.Vertical)
        if right_col:
            self.addDockWidget(Qt.RightDockWidgetArea, right_col[0])
            for d in right_col[1:]:
                self.splitDockWidget(right_col[0], d, Qt.Vertical)


    def closeEvent(self, e: QCloseEvent):
        self.manager.stop_all()
        super().closeEvent(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = BusDataMonitorForm()
    tool.show()
    sys.exit(app.exec_())
