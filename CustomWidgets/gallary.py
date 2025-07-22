'''
自定义控件集

Author: JIN && <jjyrealdeal@163.com>
Date: 2025-07-22 16:04:44 
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import json
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from CustomWidgets.Ui_FormGallery import *
from CustomWidgets.components.circular_dashborad import GaugeWidget as CircularDashboard
from CustomWidgets.components.sector_dashborad import GaugeWidget as SectorDashboard


class GallaryForm(QWidget, Ui_FormGallery): 
    def __init__(self):
        super(GallaryForm, self).__init__()
        self.setupUi(self)
        self.init_ui()  # 别忘了调用 init_ui()

    def init_ui(self):
        
        self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

        # 圆形仪表盘阈值设置
        circular_thresholds = [
            (210, (0, 128, 255, 120)),     # 蓝色：正常区
            (270, (255, 165, 0, 150)),     # 橙色：预警区
            (300, (255, 0, 0, 120)),       # 红色：告警区
        ]
        self.circular_dashboard = CircularDashboard(
            min_value=0,
            max_value=300,
            initial_value=120,
            unit="km/h",
            precision=0,
            thresholds=circular_thresholds
        )

        # 扇形仪表盘阈值设置
        sector_thresholds = [
            (10, (0, 128, 255, 120)),      # 蓝色：正常区
            (13, (255, 165, 0, 150)),      # 橙色：预警区
            (15, (255, 0, 0, 120)),        # 红色：告警区
        ]
        self.sector_dashboard = SectorDashboard(
            min_value=0,
            max_value=15,
            initial_value=8,
            unit="V",
            precision=2,
            thresholds=sector_thresholds
        )

        self.page_map={
            "圆形仪表盘":0,
            "扇形仪表盘":1
        }
        
        # 添加到堆叠窗口
        self.stackedWidget.insertWidget(0, self.circular_dashboard)  # 第0页
        self.stackedWidget.insertWidget(1, self.sector_dashboard)    # 第1页

        # 默认显示第一页
        self.stackedWidget.setCurrentIndex(0)  # 显示第0页



    def on_tree_item_clicked(self, item, column):
        """
        当 treeWidget 的某个节点被点击时触发
        :param item: 被点击的 QTreeWidgetItem
        :param column: 被点击的列号（一般为 0）
        """
        node_text = item.text(column)
        index = self.page_map.get(node_text)
        if index is not None:
            self.stackedWidget.setCurrentIndex(index)
        else:
            pass



if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = GallaryForm()
    tool.setWindowTitle("自定义仪表盘控件集")
    tool.resize(600, 400)
    tool.show()
    sys.exit(app.exec_())
