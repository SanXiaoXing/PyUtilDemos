'''
自定义控件集

Author: JIN && <jjyrealdeal@163.com>
Date: 2025-07-23 10:02:05
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.components.CustomWidgets.Ui_FormGallery import Ui_FormGallery

from PyQt5.QtWidgets import *

from src.components.CustomWidgets.components.dashboard.circular_dashboard import GaugeWidget as CircularDashboard
from src.components.CustomWidgets.components.dashboard.sector_dashboard import GaugeWidget as SectorDashboard
from src.components.CustomWidgets.components.conf2ui.input_spinbox import InputSpinxboForm
from src.components.CustomWidgets.components.conf2ui.switch_slider import SwitchSliderForm
from src.components.CustomWidgets.components.conf2ui.switch_checkbox import SwitchPanel


class GallaryForm(QWidget, Ui_FormGallery): 
    def __init__(self):
        super(GallaryForm, self).__init__()
        self.setupUi(self)
        self.init_ui()  
        self.init_treelist()


    def init_ui(self):
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

        self.input_spinbox = InputSpinxboForm()
        self.switch_slider = SwitchSliderForm()
        self.switch_checkbox=SwitchPanel()


        # 添加到堆叠窗口
        self.stackedWidget.insertWidget(0, self.circular_dashboard)  # 第0页
        self.stackedWidget.insertWidget(1, self.sector_dashboard)    # 第1页
        self.stackedWidget.insertWidget(2, self.input_spinbox)  
        self.stackedWidget.insertWidget(3, self.switch_slider)
        self.stackedWidget.insertWidget(4, self.switch_checkbox)

        # 默认显示第一页
        self.stackedWidget.setCurrentIndex(0)  # 显示第0页

    def init_treelist(self):
        data = {
            "仪表盘": {
                "圆形仪表盘": 0,
                "扇形仪表盘": 1
            },
            "批量控件生成": {
                "input_spinbox": 2,
                "switch_slider": 3,
                "switch_checkbox":4
            }
        }

        self.page_map = {}  # 用于存储页面名称和索引的映射

        # 隐藏 treeWidget 的列名（表头）
        self.treeWidget.header().setVisible(False)
        self.treeWidget.setColumnCount(1)  # 确保设置了一列
        self.treeWidget.setIndentation(20)  # 可选：设置缩进

        for top_key, sub_items in data.items():
            top_item = QTreeWidgetItem(self.treeWidget)
            top_item.setText(0, top_key)

            for sub_key, index in sub_items.items():
                sub_item = QTreeWidgetItem(top_item)
                sub_item.setText(0, sub_key)
                self.page_map[sub_key] = index  # 建立子项与页面索引的映射

        self.treeWidget.expandAll()  # 展开所有项
        self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)


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
