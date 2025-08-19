import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import queue
import random
import time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from BusDataMonitor.Ui_BusDataMonitorForm import *
from BusDataMonitor.busdata_producer import RS422SimProducer  

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000  # 设置最大行数限制
DEFAULT_REFRESH_MS = 300   # 默认刷新周期(ms)，与采集无关


# ===================== 监控窗口 =====================
class RxMonitor(QWidget):
    def __init__(self, title="数据监控窗口", data_queue=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.data_queue = data_queue or queue.Queue(maxsize=10000)
        self._max_rows = DEFAULT_MAX_ROWS

        layout = QVBoxLayout(self)

        # 控制区
        ctrl = QHBoxLayout()
        self.btn_start = QPushButton("开始")
        self.btn_pause = QPushButton("暂停")
        self.btn_resume = QPushButton("恢复")
        self.btn_stop = QPushButton("停止")
        self.spin_max_rows = QSpinBox()
        self.spin_max_rows.setRange(50, MAX_ALLOWED_ROWS)
        self.spin_max_rows.setValue(DEFAULT_MAX_ROWS)
        self.spin_refresh = QSpinBox()
        self.spin_refresh.setRange(50, 2000)
        self.spin_refresh.setValue(DEFAULT_REFRESH_MS)
        ctrl.addWidget(self.btn_start)
        ctrl.addWidget(self.btn_pause)
        ctrl.addWidget(self.btn_resume)
        ctrl.addWidget(self.btn_stop)
        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel("最大行数"))
        ctrl.addWidget(self.spin_max_rows)
        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel("刷新周期(ms)"))
        ctrl.addWidget(self.spin_refresh)
        ctrl.addStretch(1)
        layout.addLayout(ctrl)

        # 表格
        self.tableView = QTableView(self)
        self.model = QStandardItemModel(0, 2, self)
        self.model.setHorizontalHeaderLabels(["时间戳", "数据内容"])
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tableView)

        # 定时器用于从队列拉取数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flush_data)

        # 信号槽
        self.btn_start.clicked.connect(self.on_start)
        self.btn_pause.clicked.connect(self.on_pause)
        self.btn_resume.clicked.connect(self.on_resume)
        self.btn_stop.clicked.connect(self.on_stop)
        self.spin_max_rows.valueChanged.connect(self.on_max_rows_changed)
        self.spin_refresh.valueChanged.connect(self.on_refresh_changed)

    def on_start(self):
        if not self.timer.isActive():
            self.timer.start(self.spin_refresh.value())

    def on_pause(self):
        if self.timer.isActive():
            self.timer.stop()

    def on_resume(self):
        if not self.timer.isActive():
            self.timer.start(self.spin_refresh.value())

    def on_stop(self):
        self.timer.stop()
        with self.data_queue.mutex:
            self.data_queue.queue.clear()  # 清空队列
        self.model.removeRows(0, self.model.rowCount())

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
        # 控制最大行数
        excess = self.model.rowCount() - self._max_rows
        if excess > 0:
            self.model.removeRows(0, excess)
        self.tableView.scrollToBottom()


# ===================== 主窗口 =====================
class BUsDataMonitorForm(QWidget, Ui_BusDataMonitorForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 创建共享队列（外部模块往里写数据）
        self.tx_queue = queue.Queue(maxsize=10000)
        self.rx_queue = queue.Queue(maxsize=10000)

        # 换成真实硬件时，只要切换这一行即可：
        self.producer = RS422SimProducer(self.tx_queue, self.rx_queue)
        # self.producer = RS422RealProducer(self.tx_queue, self.rx_queue, device_config=...)

        self.producer.start()

        self.pushButton_txshow.clicked.connect(self.show_tx_monitor)
        self.pushButton_rxshow.clicked.connect(self.show_rx_monitor)

        self.tx_monitor = None
        self.rx_monitor = None



    def show_tx_monitor(self):
        if self.tx_monitor is None:
            self.tx_monitor = RxMonitor("发送数据监控", data_queue=self.tx_queue)
            sub = self.mdiArea.addSubWindow(self.tx_monitor)
            sub.setWindowTitle("发送数据监控")
            sub.destroyed.connect(lambda: setattr(self, "tx_monitor", None))
            self.tx_monitor.show()
        else:
            self.tx_monitor.show()
            self.tx_monitor.raise_()

    def show_rx_monitor(self):
        if self.rx_monitor is None:
            self.rx_monitor = RxMonitor("采集数据监控", data_queue=self.rx_queue)
            sub = self.mdiArea.addSubWindow(self.rx_monitor)
            sub.setWindowTitle("采集数据监控")
            sub.destroyed.connect(lambda: setattr(self, "rx_monitor", None))
            self.rx_monitor.show()
        else:
            self.rx_monitor.show()
            self.rx_monitor.raise_()


    def closeEvent(self, e: QCloseEvent):
        self.producer.stop()
        super().closeEvent(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = BUsDataMonitorForm()
    tool.show()
    sys.exit(app.exec_())
