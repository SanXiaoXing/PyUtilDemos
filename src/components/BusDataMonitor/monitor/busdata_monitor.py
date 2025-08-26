import sys
import os

from  src.components.BusDataMonitor.monitor.Ui_DataTableForm import Ui_DataTableForm

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import queue
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from assets import ICON_PLAY, ICON_PAUSE, ICON_STOP

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000  # 设置最大行数限制
DEFAULT_REFRESH_MS = 300   # 默认刷新周期(ms)，与采集无关



# ===================== 监控窗口 =====================
class DataMonitor(QWidget, Ui_DataTableForm):
    row_double_clicked = pyqtSignal(str)
    def __init__(self, title="数据监控窗口", data_queue=None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        self.data_queue = data_queue or queue.Queue(maxsize=10000)
        self._max_rows = DEFAULT_MAX_ROWS
        self.frame_count = 0
        self.stop_tag=False


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
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.doubleClicked.connect(self.on_row_double_clicked)
        

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
        if self.stop_tag==True:
            self.model.removeRows(0, self.model.rowCount())
            self.frame_count = 0
            self.label_count.setText("数据量: 0") 
            self.stop_tag=False
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
        self.stop_tag=True
        

    def on_max_rows_changed(self, v):
        self._max_rows = v
        while self.model.rowCount() > self._max_rows:
            self.model.removeRow(0)

    def on_refresh_changed(self, v):
        if self.timer.isActive():
            self.timer.start(v)

    # 在类末尾添加：
    def on_row_double_clicked(self, index):
        # 第二列为数据内容
        hex_str = self.model.item(index.row(), 1).text()
        self.row_double_clicked.emit(hex_str)



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