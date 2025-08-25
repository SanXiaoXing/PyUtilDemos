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
from src.components.BusDataMonitor.busdata_producer import RS422SimProducer
from src.components.BusDataMonitor.busdata_monitor import DataMonitor
from assets import ICON_TABLE,ICON_R,ICON_T

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
        self.btn_txshow = QAction(QIcon(ICON_T), "发送数据监控", self)
        self.btn_rxshow = QAction(QIcon(ICON_R), "采集数据监控", self)
        self.btn_layout=QAction(QIcon(ICON_TABLE), "默认布局", self)

        # 信号槽：显示 Dock 窗口
        self.btn_txshow.triggered.connect(self.show_tx_monitor)
        self.btn_rxshow.triggered.connect(self.show_rx_monitor) 
        self.btn_layout.triggered.connect(self.reset_layout)
        
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

    def reset_layout(self):
        """根据现有 dockwidget 数量恢复布局"""
        docks = []

        # 先收集存在的窗口
        if self.tx_dock:
            docks.append(self.tx_dock)
        if hasattr(self, "tx_parsed_dock") and self.tx_parsed_dock:
            docks.append(self.tx_parsed_dock)
        if self.rx_dock:
            docks.append(self.rx_dock)
        if hasattr(self, "rx_parsed_dock") and self.rx_parsed_dock:
            docks.append(self.rx_parsed_dock)

        count = len(docks)
        if count == 0:
            return  # 没有窗口，直接返回

        # 1个窗口：占满主界面
        if count == 1:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            self.tabifyDockWidget(docks[0], docks[0])  # 确保独占（无实际tab）
            return

        # 2个窗口：左右布局
        if count == 2:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            self.addDockWidget(Qt.RightDockWidgetArea, docks[1])
            return

        # 3个窗口：左中右布局
        if count == 3:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            self.addDockWidget(Qt.RightDockWidgetArea, docks[1])
            self.splitDockWidget(docks[0], docks[2], Qt.Horizontal)
            return

        # 4个窗口：强制 2x2 布局（固定顺序）
        # 左上: send窗口, 左下: send解析窗口
        # 右上: recv窗口, 右下: recv解析窗口
        if count == 4:
            # 保证引用存在，即使为空也不报错
            send = self.tx_dock
            send_parsed = getattr(self, "tx_parsed_dock", None)
            recv = self.rx_dock
            recv_parsed = getattr(self, "rx_parsed_dock", None)

            if not (send and recv and send_parsed and recv_parsed):
                # 如果4个窗口不全，就直接左右布局备用
                self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
                self.addDockWidget(Qt.RightDockWidgetArea, docks[1])
                if len(docks) > 2:
                    self.splitDockWidget(docks[0], docks[2], Qt.Horizontal)
                return

            # 左侧布局
            self.addDockWidget(Qt.LeftDockWidgetArea, send)
            self.splitDockWidget(send, send_parsed, Qt.Vertical)

            # 右侧布局
            self.addDockWidget(Qt.RightDockWidgetArea, recv)
            self.splitDockWidget(recv, recv_parsed, Qt.Vertical)


 


    def closeEvent(self, e: QCloseEvent):
        self.producer.stop()
        super().closeEvent(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = BusDataMonitorForm()
    tool.show()
    sys.exit(app.exec_())
