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
from BusDataMonitor.Ui_DataTableForm import *
from BusDataMonitor.busdata_producer import RS422SimProducer  
from BusDataMonitor.busdata_monitor import DataMonitor
from assets import ICON_PLAY, ICON_PAUSE, ICON_STOP

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000  # 设置最大行数限制
DEFAULT_REFRESH_MS = 300   # 默认刷新周期(ms)，与采集无关



# ===================== 主窗口（ =====================
class BusDataMonitorForm(QMainWindow):
    def __init__(self):  
        super().__init__()
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
        self.resize(1000, 800)
         # 创建工具栏
        self.toolBar = self.addToolBar("Main Toolbar")
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
            self.tx_monitor = DataMonitor("发送数据监控", data_queue=self.tx_queue)
            self.tx_dock = QDockWidget("发送数据监控", self)
            self.tx_dock.setWidget(self.tx_monitor)
            self.tx_dock.setObjectName("DockTx")
            self.tx_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                                     QDockWidget.DockWidgetClosable | 
                                     QDockWidget.DockWidgetFloatable)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.tx_dock)
            self.tx_dock.destroyed.connect(lambda: setattr(self, "tx_monitor", None))
            self.tx_dock.show()
        else:
            self.tx_dock.raise_()
            self.tx_dock.show()

    def show_rx_monitor(self):
        if self.rx_monitor is None:
            self.rx_monitor = DataMonitor("采集数据监控", data_queue=self.rx_queue)
            self.rx_dock = QDockWidget("采集数据监控", self)
            self.rx_dock.setWidget(self.rx_monitor)
            self.rx_dock.setObjectName("DockRx")
            self.rx_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                                     QDockWidget.DockWidgetClosable | 
                                     QDockWidget.DockWidgetFloatable)
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
    tool = BusDataMonitorForm()
    tool.show()
    sys.exit(app.exec_())
