'''
总线数据监控及解析工具
=======

Author: JIN && <jjyrealdeal@163.com>
Date: 2025-08-19 16:28:46
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import queue
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from BusDataMonitor.Ui_BusDataMonitor import *
from BusDataMonitor.Ui_DataTableForm import *
from BusDataMonitor.busdata_producer import RS422SimProducer  
from assets import ICON_PLAY, ICON_PAUSE, ICON_STOP

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000  # 设置最大行数限制
DEFAULT_REFRESH_MS = 300   # 默认刷新周期(ms)，与采集无关

DOCK_QSS="""
QDockWidget {
    border: 2px solid #666666;
}
"""

# ===================== 监控窗口 =====================
class RxMonitor(QWidget, Ui_DataTableForm):
    def __init__(self, title="数据监控窗口", data_queue=None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        self.data_queue = data_queue or queue.Queue(maxsize=10000)
        self._max_rows = DEFAULT_MAX_ROWS
        self.frame_count = 0

        # 控制区
        self.spin_max_rows.setRange(50, MAX_ALLOWED_ROWS)
        self.spin_max_rows.setValue(DEFAULT_MAX_ROWS)
        self.spin_refresh.setRange(50, 2000)
        self.spin_refresh.setValue(DEFAULT_REFRESH_MS)
        self.ctrl_area.addSpacing(20)
        self.ctrl_area.addStretch(1)
        self.btn_start.setIcon(QIcon(ICON_PLAY))
        self.btn_stop.setIcon(QIcon(ICON_STOP))

        # 表格
        self.model = QStandardItemModel(0, 2, self)
        self.model.setHorizontalHeaderLabels(["时间戳", "数据内容"])
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 定时器用于从队列拉取数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flush_data)

        # 信号槽
        self.btn_start.clicked.connect(self.start_ctrl)
        self.btn_stop.clicked.connect(self.on_stop)
        self.spin_max_rows.valueChanged.connect(self.on_max_rows_changed)
        self.spin_refresh.valueChanged.connect(self.on_refresh_changed)


    def start_ctrl(self):
        if self.btn_start.text() == "开始":
            self.on_start()
        elif self.btn_start.text() == "暂停":
            self.on_pause()

    def on_start(self):  
        if not self.timer.isActive():  
            self.timer.start(self.spin_refresh.value())  
            self.btn_start.setText("暂停")  
            self.btn_start.setIcon(QIcon(ICON_PAUSE))

    def on_pause(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_start.setText("开始")
            self.btn_start.setIcon(QIcon(ICON_PLAY))

    def on_stop(self):
        self.timer.stop()
        with self.data_queue.mutex:
            self.data_queue.queue.clear()  # 清空队列
        self.btn_start.setText("开始")
        self.btn_start.setIcon(QIcon(ICON_PLAY))
        self.model.removeRows(0, self.model.rowCount())
        self.frame_count = 0
        self.label_count.setText("数据量: 0")

    def on_max_rows_changed(self, v):
        self._max_rows = v
        while self.model.rowCount() > self._max_rows:
            self.model.removeRow(0)

    def on_refresh_changed(self, v):
        if self.timer.isActive():
            self.timer.start(v)

    def flush_data(self):
        """从队列拉数据批量刷新"""
        rows_to_add = []
        while not self.data_queue.empty():
            try:
                rows_to_add.append(self.data_queue.get_nowait())
            except queue.Empty:
                break

        for ts, hex_str in rows_to_add:
            self.model.appendRow([QStandardItem(ts), QStandardItem(hex_str)])
        
        # 更新计数
        self.frame_count += len(rows_to_add)
        self.label_count.setText(f"数据量: {self.frame_count}")

        # 控制最大行数
        excess = self.model.rowCount() - self._max_rows
        if excess > 0:
            self.model.removeRows(0, excess)
        self.tableView.scrollToBottom()


# ===================== 主窗口（改为 QMainWindow） =====================
class BUsDataMonitorForm(QMainWindow, Ui_BusDataMonitor):
    def __init__(self):  
        super().__init__()
        self.setupUi(self)
        self.init_ui()

        # 创建共享队列（外部模块往里写数据）
        self.tx_queue = queue.Queue(maxsize=10000)
        self.rx_queue = queue.Queue(maxsize=10000)
        # 换成真实硬件时，只要切换这一行即可：
        self.producer = RS422SimProducer(self.tx_queue, self.rx_queue)
        # self.producer = RS422RealProducer(self.tx_queue, self.rx_queue, device_config=...)
        self.producer.start()

        # 窗口引用
        self.tx_monitor = None
        self.rx_monitor = None
        self.tx_dock = None
        self.rx_dock = None

    
    def init_ui(self):
        self.setWindowTitle("总线数据监控")

        self.toolBar.setMovable(False)  # 不允许拖动
        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        # 添加按钮（QAction）
        self.btn_txshow = QAction(QIcon(ICON_PLAY), "发送数据监控", self)
        self.btn_rxshow = QAction(QIcon(ICON_PLAY), "采集数据监控", self)
        self.btn_layout=QAction(QIcon(ICON_PLAY), "默认布局", self)

        # 信号槽：显示 Dock 窗口
        self.btn_txshow.triggered.connect(self.show_tx_monitor)
        self.btn_rxshow.triggered.connect(self.show_rx_monitor) 
        
        self.toolBar.addActions([self.btn_txshow, self.btn_rxshow, self.btn_layout])
        




    def show_tx_monitor(self):
        if self.tx_monitor is None:
            self.tx_monitor = RxMonitor("发送数据监控", data_queue=self.tx_queue)
            self.tx_dock = QDockWidget("发送数据监控", self)
            self.tx_dock.setWidget(self.tx_monitor)
            self.tx_dock.setObjectName("DockTx")
            self.tx_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                                     QDockWidget.DockWidgetClosable | 
                                     QDockWidget.DockWidgetFloatable)
            self.tx_dock.setStyleSheet(DOCK_QSS)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.tx_dock)
            self.tx_dock.destroyed.connect(lambda: setattr(self, "tx_monitor", None))
            self.tx_dock.show()
        else:
            self.tx_dock.raise_()
            self.tx_dock.show()

    def show_rx_monitor(self):
        if self.rx_monitor is None:
            self.rx_monitor = RxMonitor("采集数据监控", data_queue=self.rx_queue)
            self.rx_dock = QDockWidget("采集数据监控", self)
            self.rx_dock.setWidget(self.rx_monitor)
            self.rx_dock.setObjectName("DockRx")
            self.rx_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                                     QDockWidget.DockWidgetClosable | 
                                     QDockWidget.DockWidgetFloatable)
            self.rx_dock.setStyleSheet(DOCK_QSS)
            self.addDockWidget(Qt.RightDockWidgetArea, self.rx_dock)
            self.rx_dock.destroyed.connect(lambda: setattr(self, "rx_monitor", None))
            self.rx_dock.show()
        else:
            self.rx_dock.raise_()
            self.rx_dock.show()


    def closeEvent(self, e: QCloseEvent):
        self.producer.stop()
        super().closeEvent(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = BUsDataMonitorForm()
    tool.show()
    sys.exit(app.exec_())
