'''
总线数据监控及解析工具
=======

Author: JIN && <jjyrealdeal@163.com>
Date: 2025-08-19 16:28:46
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import queue
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from src.components.BusDataMonitor.monitor.busdata_producer import RS422SimProducer
from src.components.BusDataMonitor.monitor.dock_monitor import DataMonitor
from src.components.BusDataMonitor.monitor.dock_parser import DockParser
from assets import ICON_TABLE,ICON_R,ICON_T

DEFAULT_MAX_ROWS = 500
MAX_ALLOWED_ROWS = 200000  # 设置最大行数限制
DEFAULT_REFRESH_MS = 300   # 默认刷新周期(ms)，与采集无关
TX_CHANNEL_ID = 0
RX_CHANNEL_ID = 1



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
        self.tx_parsed_dock = None
        self.rx_parsed_dock = None

        # 初始显示发送+接收窗口
        self.show_tx_monitor()
        self.show_rx_monitor()
        self.reset_layout()

    
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
    

    def add_or_restore_dock(self, dock, area):
        """如果dock已存在，则只raise；否则添加到指定区域"""
        if dock.isHidden():
            dock.show()
        if dock.parent() is None:  # 未被添加
            self.addDockWidget(area, dock)
        dock.raise_()


    def show_tx_monitor(self):
        if self.tx_monitor is None:
            self.tx_monitor = DataMonitor("发送数据监控", data_queue=self.tx_queue, channel_id=TX_CHANNEL_ID)
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

        if self.tx_monitor:
            self.tx_monitor.row_double_clicked.connect(self.show_parsed_dock)

    def show_rx_monitor(self):
        if self.rx_monitor is None:
            self.rx_monitor = DataMonitor("采集数据监控", data_queue=self.rx_queue, channel_id=RX_CHANNEL_ID)
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

        if self.rx_monitor:
            self.rx_monitor.row_double_clicked.connect(self.show_parsed_dock)
        


    def show_parsed_dock(self, hex_str, protocol,index,source):
        # source 参数可传 "tx" 或 "rx"
        parser = DockParser(protocol, index,self)
        self.parserdock = QDockWidget(f"{source.upper()} 解析", self)
        self.parserdock.setWidget(parser)
        self.parserdock.setFeatures(QDockWidget.DockWidgetMovable | 
                                     QDockWidget.DockWidgetClosable | 
                                     QDockWidget.DockWidgetFloatable)
        if source == "tx":
            self.tx_parsed_dock = self.parserdock
        else:
            self.rx_parsed_dock = self.parserdock
        
        self.addDockWidget(Qt.BottomDockWidgetArea, self.parserdock)
        
        self.parserdock.update_data(hex_str)
        self.parserdock.show()

  
    

    def reset_layout(self):
        """恢复 Dock 窗口布局：
        2 个窗口 → 左右布局
        3 或 4 个窗口 → 2×2 布局（左2个，右2个）
        """
        # 收集现有的 dock（保持顺序）
        docks = []
        if self.tx_dock: docks.append(self.tx_dock)
        if self.tx_parsed_dock: docks.append(self.tx_parsed_dock)
        if self.rx_dock: docks.append(self.rx_dock)
        if self.rx_parsed_dock: docks.append(self.rx_parsed_dock)

        if not docks:
            return  # 没有任何窗口

        # 先都放回主窗口并取消浮动
        for d in docks:
            d.setFloating(False)

        # 只有1个 → 占满
        if len(docks) == 1:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            return

        # 只有2个 → 左右布局
        if len(docks) == 2:
            self.addDockWidget(Qt.LeftDockWidgetArea, docks[0])
            self.addDockWidget(Qt.RightDockWidgetArea, docks[1])
            return

        # 3或4个 → 强制 2×2 布局
        # 分成左右两列
        left_col = []
        right_col = []
        for i, dock in enumerate(docks):
            (left_col if i % 2 == 0 else right_col).append(dock)

        # 左列
        if left_col:
            self.addDockWidget(Qt.LeftDockWidgetArea, left_col[0])
            for d in left_col[1:]:
                self.splitDockWidget(left_col[0], d, Qt.Vertical)

        # 右列
        if right_col:
            self.addDockWidget(Qt.RightDockWidgetArea, right_col[0])
            for d in right_col[1:]:
                self.splitDockWidget(right_col[0], d, Qt.Vertical)


 


    def closeEvent(self, e: QCloseEvent):
        self.producer.stop()
        super().closeEvent(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = BusDataMonitorForm()
    tool.show()
    sys.exit(app.exec_())
