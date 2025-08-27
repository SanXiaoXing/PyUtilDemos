import queue
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from src.components.BusDataMonitor.monitor.Ui_dock_monitor import Ui_dockmonitor
from src.components.BusDataMonitor.monitor.dialog_setting import ChannelConfigDialog
from src.components.BusDataMonitor.config import channel_config
from assets import ICON_PLAY, ICON_PAUSE, ICON_STOP

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000  # 设置最大行数限制
DEFAULT_REFRESH_MS = 300   # 默认刷新周期(ms)，与采集无关



# ===================== 监控窗口 =====================
class DataMonitor(QWidget, Ui_dockmonitor):
    row_double_clicked = pyqtSignal(str,str,int)
    def __init__(self, title="数据监控窗口", data_queue=None, channel_id=0,parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        self.data_queue = data_queue or queue.Queue(maxsize=10000)
        self.channel_id = channel_id
        self._max_rows = DEFAULT_MAX_ROWS
        self.frame_count = 0
        self.protocol_file = channel_config[str(channel_id)]["protocol"]
        self.TorR=channel_config[str(channel_id)]["TorR"]
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

        # 状态栏
        self.label_protocol.setText(f"协议文件:{self.protocol_file}")
        self.label_ch.setText(f"通道号:{self.channel_id}")
        self.label_TR.setText(f"传输方向:{self.TorR}")
        
        
        # 表格
        self.model = QStandardItemModel(0, 2, self)
        self.model.setHorizontalHeaderLabels(["时间戳", "传输方向","数据内容"])
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.tableView.doubleClicked.connect(self.on_row_double_clicked)
        

        # 定时器用于从队列拉取数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flush_data)

        # 信号槽
        self.btn_start.clicked.connect(self.start_ctrl)
        self.btn_stop.clicked.connect(self.on_stop)
        self.spin_max_rows.valueChanged.connect(self.on_max_rows_changed)
        self.spin_refresh.valueChanged.connect(self.on_refresh_changed)
        self.btn_conf.clicked.connect(self.show_settings)

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


    def flush_data(self): 
        """从队列拉数据批量刷新"""
        rows_to_add = []
        while not self.data_queue.empty():
            try:
                rows_to_add.append(self.data_queue.get_nowait())
            except queue.Empty:
                break

        for ts, tor,hex_str in rows_to_add:
            self.model.appendRow([QStandardItem(ts), QStandardItem(tor),QStandardItem(hex_str)])
        
        # 更新计数
        self.frame_count += len(rows_to_add)
        self.label_count.setText(f"数据量: {self.frame_count}")

        # 控制最大行数
        excess = self.model.rowCount() - self._max_rows
        if excess > 0:
            self.model.removeRows(0, excess)
        self.tableView.scrollToBottom()


    # def on_row_double_clicked(self, index):
    #     # 第二列为数据内容
    #     hex_str = self.model.item(index.row(), 1).text()
    #     self.row_double_clicked.emit(hex_str,self.protocol_file,index)


    def show_settings(self):
        # 创建并显示通道配置对话框
        dlg = ChannelConfigDialog(channel_id=self.channel_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            # 对话框点击“确定”会自动写回 channel_config.json
            # 此处可根据需要更新界面显示，例如：
            new_protocol = dlg.get_selected_protocol()
            self.label_protocol.setText(f"协议文件: {new_protocol}")
            self.protocol_file = new_protocol

    
    