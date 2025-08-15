'''
数据回放工具
============

本工具专为回放和可视化CSV文件中的时间序列数据而设计。它提供了一个图形界面，用于加载、选择和绘制多个数据序列，并支持交互式导航。

功能特性：
- 同时加载和显示多个CSV文件
- 交互式数据可视化，支持缩放和平移功能
- 通过鼠标悬停实时检查数据点
- 使用滑动条控件进行基于时间的数据导航
- 支持多文件和多列数据选择

使用方法：
1. 右键点击左侧列表使用文件树中的上下文菜单添加CSV文件
2. 在树形结构中勾选想要绘制的数据列
3. 点击"回放"按钮可视化选中的数据
4. 使用滑动条在时间序列数据中导航
5. 在图表上悬停鼠标查看详细数据点信息

CSV格式要求：
- 第一行：列名
- 第二行：各列的单位
- 后续行：数据值

Author: JIN && <jjyrealdeal@163.com>
Date: 2025-7-16 08:43:14
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import numpy as np 
import pyqtgraph as pg
import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from DataReplay.Ui_DataReplay_Form import *
from assets import ICON_BACKWARD,ICON_PLUS,ICON_MINUS,ICON_ALLCHECK,ICON_ALLUNCHECK,ICON_BROOM




class LimitedViewBox(pg.ViewBox):
    """限制缩放范围的ViewBox"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._limits = None  # 存储缩放限制

    def setLimits(self, **kwargs):
        self._limits = kwargs
        super().setLimits(**kwargs)

    def wheelEvent(self, ev, axis=None):
        super().wheelEvent(ev, axis)

        if self._limits is None:
            return

        # 当前视图范围
        x_range = self.viewRange()[0]
        y_range = self.viewRange()[1]

        x_min, x_max = x_range
        y_min, y_max = y_range

        # 限制参数
        limits = self._limits

        # 限制x范围
        if 'xMin' in limits and x_min < limits['xMin']:
            x_min = limits['xMin']
        if 'xMax' in limits and x_max > limits['xMax']:
            x_max = limits['xMax']

        # 限制y范围
        if 'yMin' in limits and y_min < limits['yMin']:
            y_min = limits['yMin']
        if 'yMax' in limits and y_max > limits['yMax']:
            y_max = limits['yMax']

        # 限制x缩放窗口宽度
        if 'minXRange' in limits and (x_max - x_min) < limits['minXRange']:
            center_x = (x_min + x_max) / 2
            half = limits['minXRange'] / 2
            x_min = center_x - half
            x_max = center_x + half

        if 'maxXRange' in limits and (x_max - x_min) > limits['maxXRange']:
            center_x = (x_min + x_max) / 2
            half = limits['maxXRange'] / 2
            x_min = center_x - half
            x_max = center_x + half

        # 限制y缩放窗口高度
        if 'minYRange' in limits and (y_max - y_min) < limits['minYRange']:
            center_y = (y_min + y_max) / 2
            half = limits['minYRange'] / 2
            y_min = center_y - half
            y_max = center_y + half

        if 'maxYRange' in limits and (y_max - y_min) > limits['maxYRange']:
            center_y = (y_min + y_max) / 2
            half = limits['maxYRange'] / 2
            y_min = center_y - half
            y_max = center_y + half

        # 应用限制后的范围
        self.setXRange(x_min, x_max, padding=0)
        self.setYRange(y_min, y_max, padding=0)




class DataReplayForm(QWidget, Ui_DataReplay_Form):
    """数据回放窗体"""
    def __init__(self):
        super(DataReplayForm, self).__init__()
        self.setupUi(self)
        self.data = pd.DataFrame() 
        self.all_data = {}
        self.curves=[]
        self.timestamps = np.array([])       # x轴时间戳
        self.window_width = 0                # 当前窗口宽度
        self.scroll_position = 0             # 当前滚动起始位置

        self.initUI()
        self.init_graph()
        self.init_connections()
        

    def initUI(self):
        self.setWindowTitle('数据回放')
        self.treeWidget_datafile.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeWidget_datafile.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pushButton_plot.setIcon(QIcon(ICON_BACKWARD))
        self.horizontalSlider.setAttribute(Qt.WA_Hover, True)
        self.horizontalSlider.installEventFilter(self)


    def init_graph(self):
        """
        初始化绘图相关组件和界面元素。

        该函数完成以下主要工作：
        1. 创建并配置绘图控件（PlotWidget）及相关视图组件；
        2. 设置图表标题、坐标轴标签及网格线；
        3. 添加图例、鼠标交互事件监听器；
        4. 初始化用于交互提示的文本框、高亮标记点及十字参考线等图形元素。

        """
        self.view_box = LimitedViewBox()
        self.plot_widget = pg.PlotWidget(viewBox=self.view_box)
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        self.gridLayout_plot.addWidget(self.plot_widget)

        # 设置标题和坐标轴标签
        self.plot_widget.getPlotItem().setTitle(" ", color='k', size='15pt')
        self.plot_widget.getPlotItem().setLabel('left', " ", units='', **{'color': 'black', 'font-size': '12pt'})
        self.plot_widget.getPlotItem().setLabel('bottom', "时间", units='ms', **{'color': 'black', 'font-size': '12pt'})

        # 绑定鼠标移动事件（监听整个plot区域）
        self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.onMouseMoved)
        self.highlighted_curve = None
        self.text_item = pg.TextItem(anchor=(0,1), border='w', fill=(0, 0, 0, 100))
        self.text_item.setZValue(11)
        self.plot_widget.addItem(self.text_item)
        self.text_item.hide()

        # 实心小圆点
        self.hover_marker = pg.ScatterPlotItem(
            size=8,
            pen=pg.mkPen('k'),
            brush=pg.mkBrush('y'),
            symbol='o'
        )
        self.hover_marker.setZValue(10)
        self.plot_widget.addItem(self.hover_marker)

        # 虚线十字线
        dash_pen = pg.mkPen(color='gray', width=1, style=Qt.DashLine)
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=dash_pen)
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=dash_pen)
        self.v_line.setZValue(9)
        self.h_line.setZValue(9)
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        # 悬浮数据文本框
        self.text_item = pg.TextItem(anchor=(0,1), border='w', fill=(0, 0, 0, 100))
        self.text_item.setZValue(11)
        self.plot_widget.addItem(self.text_item)
        self.text_item.hide()


    def init_connections(self):
        """初始化信号槽连接"""
        self.horizontalSlider.valueChanged.connect(self.scroll_plot)
        self.pushButton_plot.clicked.connect(self.draw_plot)
        self.treeWidget_datafile.customContextMenuRequested.connect(self.TreeContextMenuEvent)

    def TreeContextMenuEvent(self, pos):
        """右键菜单事件"""
        self.item = self.treeWidget_datafile.itemAt(pos)
        TreeMenu = QMenu(parent=self.treeWidget_datafile)

        # 文件操作类 
        OpenFile = QAction('添加文件', self)
        OpenFile.setIcon(QIcon(ICON_PLUS))
        RemoveFile = QAction('移除文件', self)
        RemoveFile.setIcon(QIcon(ICON_MINUS))
        TreeMenu.addAction(OpenFile)
        TreeMenu.addAction(RemoveFile)
        TreeMenu.addSeparator()  # ──────────────

        # 选择操作类
        CheckedAll = QAction('全选', self)
        CheckedAll.setIcon(QIcon(ICON_ALLCHECK))
        UncheckedAll = QAction('取消全选', self)
        UncheckedAll.setIcon(QIcon(ICON_ALLUNCHECK))
        TreeMenu.addAction(CheckedAll)
        TreeMenu.addAction(UncheckedAll)
        TreeMenu.addSeparator()  # ──────────────

        # 其他操作类
        ClearAll = QAction('清空列表', self)
        ClearAll.setIcon(QIcon(ICON_BROOM))
        TreeMenu.addAction(ClearAll)

        # 绑定信号
        OpenFile.triggered.connect(self.load_csv)
        RemoveFile.triggered.connect(self.remove_file)
        CheckedAll.triggered.connect(self.SelectedAll)
        UncheckedAll.triggered.connect(self.SelectedClear)
        ClearAll.triggered.connect(self.clear_all_files)

        # 显示菜单
        TreeMenu.exec_(self.treeWidget_datafile.mapToGlobal(pos))


    def SelectedAll(self):
        """全选"""
        iterator = QTreeWidgetItemIterator(self.treeWidget_datafile)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(0, Qt.Checked)
            iterator += 1


    def SelectedClear(self):
        """取消全选"""
        iterator = QTreeWidgetItemIterator(self.treeWidget_datafile)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(0, Qt.Unchecked)
            iterator += 1

    
    def clear_all_files(self):
        """清空数据列表并清空图表"""
        self.treeWidget_datafile.clear()
        self.plot_widget.clear()

        # 清理内部变量
        self.all_data = {}
        self.curves = []
        self.selected_columns = []
        self.data = pd.DataFrame() 

    
    def remove_file(self):
        """移除所选文件并且刷新文件列表以及图表"""
        selected_items = self.treeWidget_datafile.selectedItems()
        
        if not selected_items:
            return  # 没有选中项，直接返回

        for item in selected_items:
            # 确保是顶层节点（即文件）
            if item.parent() is None:
                filename = item.text(0)
                del self.all_data[filename]  # 从数据中删除
                index = self.treeWidget_datafile.indexOfTopLevelItem(item)
                self.treeWidget_datafile.takeTopLevelItem(index)  # 从树中删除

        # 刷新列计数器和映射
        self.col_counter = {}
        self.column_mapping = {}

        for filename, df in self.all_data.items():
            for col in df.columns:
                self.col_counter[col] = self.col_counter.get(col, 0) + 1
                self.column_mapping[(filename, col)] = col

        # 重新绘图
        self.draw_plot()



    def load_csv(self):
        """
        加载CSV文件到程序中，支持多个文件的批量加载。
        CSV格式要求：首行为列名，第二行为单位，后续为数据行。

        返回值:
            无返回值。加载的数据存储在 self.all_data 中，并更新界面组件。

        功能说明：
            - 使用文件对话框选择一个或多个CSV文件；
            - 每个文件解析为带多级列名（名称+单位）的DataFrame；
            - 时间戳列作为索引处理；
            - 避免重复加载同一文件；
            - 在TreeWidget中展示文件结构和列信息；
            - 更新滑动条的最大值以匹配最新加载文件的数据长度。
        """
        # 打开文件选择对话框，允许选择多个CSV文件
        paths, _ = QFileDialog.getOpenFileNames(self, "选择CSV文件", "", "*.csv")
        if not paths:
            return

        # 初始化数据存储结构
        if not hasattr(self, "all_data"):
            self.all_data = {}
        self.col_counter = {}  # 统计所有列名出现次数
        self.column_mapping = {}  # (filename, name) -> (name, unit)

        # 遍历选中的每个文件路径进行处理
        for path in paths:
            filename = os.path.basename(path)

            # 避免重复加载相同文件名的文件
            if filename in self.all_data:
                QMessageBox.information(self, "提示", f"{filename} 已被加载，请勿重复操作")
                continue

            # 尝试读取CSV文件，前两行为标题行（列名+单位）
            try:
                df = pd.read_csv(path, header=[0, 1])  # 两行标题（列名 + 单位）
            except Exception as e:
                QMessageBox.warning(self, "错误", f"读取文件失败：{filename}\n{str(e)}")
                continue

            # 设置时间戳列为索引并删除原时间列
            df.index = pd.to_datetime(df[df.columns[0]])  # 将时间戳列设为 index
            df.drop(columns=[df.columns[0]], inplace=True)  # 删除原时间列

            # 存储解析后的DataFrame
            self.all_data[filename] = df

            # 统计列名出现次数并记录完整映射关系
            for col in df.columns:
                name, unit = col
                self.col_counter[name] = self.col_counter.get(name, 0) + 1
                self.column_mapping[(filename, name)] = (name, unit)

        # 更新TreeWidget显示内容：展示文件及其列信息（仅显示列名）
        for filename, df in self.all_data.items():
            exists = False
            for i in range(self.treeWidget_datafile.topLevelItemCount()):
                item = self.treeWidget_datafile.topLevelItem(i)
                if item.text(0) == filename:
                    exists = True
                    break
            if not exists:
                root = QTreeWidgetItem([filename])
                root.setToolTip(0, path)
                root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
                root.setCheckState(0, Qt.Unchecked)
                for name, unit in df.columns:
                    item = QTreeWidgetItem([name])  # 显示列名
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
                    item.setCheckState(0, Qt.Unchecked)
                    item.setToolTip(0, f"单位: {unit}")
                    root.addChild(item)
                self.treeWidget_datafile.addTopLevelItem(root)
                root.setExpanded(True)

        # 如果成功加载了数据，则更新滑动条最大值为最后一个文件的行数
        if self.all_data:
            last_df = list(self.all_data.values())[-1]
            self.horizontalSlider.setMaximum(len(last_df))



    def draw_plot(self):
        """
        根据当前选择的文件和列，绘制对应的图表。

        该方法会：
        - 清除当前绘图区域并保留必要的交互元素；
        - 遍历所有文件及其选中的列，构建绘图数据；
        - 绘制每条曲线，并设置颜色和图例；
        - 设置坐标轴范围和滑动条参数，以支持数据浏览。

        """
        # 清除绘图但保留交互元素
        self.plot_widget.clear()
        self.plot_widget.addItem(self.text_item)
        self.plot_widget.addItem(self.hover_marker)
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)
        self.text_item.hide()
        self.highlighted_curve = None
        self.curves = []  # 保存所有PlotDataItem
        combined_df = pd.DataFrame()
        self.selected_columns = []

        # 遍历所有文件
        for i in range(self.treeWidget_datafile.topLevelItemCount()):
            file_item = self.treeWidget_datafile.topLevelItem(i)
            filename = file_item.text(0)
            df = self.all_data.get(filename)
            if df is None:
                continue

            # 遍历文件中的所有列
            for j in range(file_item.childCount()):
                col_item = file_item.child(j)
                if col_item.checkState(0) == Qt.Checked:
                    col = col_item.text(0)  # 原始列名
                    unit= col_item.toolTip(0).split("单位: ")[1]
                    if self.col_counter[col] > 1:
                        legend_name = f"{col} {unit} ({filename})"
                    else:
                        legend_name = f'{col} {unit}'

                    # 添加到绘图数据
                    combined_df[legend_name] = df[col]
                    self.selected_columns.append((legend_name, legend_name))

        if combined_df.empty:
            return
        
        self.data = combined_df
        self.timestamps = np.arange(len(combined_df))  
        self.window_width = max(100, int(len(self.timestamps) * 0.1))
        self.scroll_position = 0  # 初始起点

        # 遍历所有选中的列
        for i, (colname, legend_name) in enumerate(self.selected_columns):
            y = self.data[legend_name].to_numpy()
            color = QColor.fromHsv((i * 30) % 255, 200, 230)
            curve = self.plot_widget.plot(self.timestamps, y, pen=pg.mkPen(color=color, width=1), name=legend_name)
            curve.default_pen = pg.mkPen(color=color, width=1)
            self.curves.append((curve, self.timestamps, y))

        x_min = self.scroll_position
        x_max = self.scroll_position + self.window_width
        y_min, y_max = combined_df.min().min(), combined_df.max().max()

        y_range = y_max - y_min
        # 添加 5% 的上下留白
        padding = y_range * 0.05
        y_min -= padding
        y_max += padding

        vb = self.view_box
        vb.setLimits(
            xMin=0,
            xMax=len(self.timestamps),
            yMin=y_min,
            yMax=y_max,
            minXRange=10,
            maxXRange=len(self.timestamps),
            minYRange=y_range * 0.01,
            maxYRange=y_range * 1.1
        )
        vb.setXRange(x_min, x_max, padding=0)
        vb.setYRange(y_min, y_max, padding=0)

        # 设置滑动条最大值为 100（百分比控制）
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setValue(0)


    def scroll_plot(self, value):
        """
        根据滑动条位置滚动图表显示区域
        
        参数:
            value (int): 滑动条的当前位置值，范围通常为0-100
            
        返回值:
            None: 无返回值，直接修改图表显示区域
        """
        # 如果没有时间戳或者时间戳长度为0，则直接返回
        if not hasattr(self, 'timestamps') or len(self.timestamps) == 0:
            return

        # 获取时间戳的总数
        total_points = len(self.timestamps)
        # 如果时间戳总数小于等于窗口宽度，则直接返回
        if total_points <= self.window_width:
            return

        # 计算起始索引位置
        max_start = total_points - self.window_width
        # 根据滑动条位置计算滚动位置
        self.scroll_position = int((value / 100.0) * max_start)
        # 确保滚动位置在有效范围内
        self.scroll_position = max(0, min(self.scroll_position, max_start))

        # 获取图表的视图框
        vb = self.plot_widget.getViewBox()
        # 设置X轴范围，从滚动位置开始，到滚动位置加上窗口宽度结束，不填充
        vb.setXRange(self.scroll_position,
                     self.scroll_position + self.window_width,
                     padding=0)


    def eventFilter(self, source, event):
        """
        自定义事件过滤器，用于处理水平滑动条的悬停事件并显示对应数据的时间戳提示
        
        参数:
            source: 事件来源对象
            event: 事件对象
            
        返回值:
            bool: 返回父类事件过滤器的处理结果
        """
        # 如果事件源是水平滑动条，并且事件类型是悬停移动
        if source == self.horizontalSlider and event.type() == QEvent.HoverMove:
            # 获取鼠标位置
            pos = event.pos()
            # 计算滑动条的值
            val = self.horizontalSlider.minimum() + (
                (self.horizontalSlider.maximum() - self.horizontalSlider.minimum())
                * pos.x()
                / self.horizontalSlider.width()
            )
            # 计算索引
            index = int(len(self.data) * (val / 100.0))
            # 如果索引在数据范围内
            if 0 <= index < len(self.data):
                try:
                    # 获取时间戳
                    timestamp = self.data.index[index]
                    # 如果时间戳是pd.Timestamp类型
                    if isinstance(timestamp, pd.Timestamp):
                        # 格式化时间戳
                        tip = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    else:
                        # 否则直接转换为字符串
                        tip = str(timestamp)
                    # 显示提示信息
                    QToolTip.showText(self.horizontalSlider.mapToGlobal(pos), tip)
                except Exception:
                    pass
        # 返回父类的事件过滤器
        return super().eventFilter(source, event)




    def onMouseMoved(self, evt):
        """
        鼠标移动事件处理函数
        
        当鼠标在绘图区域移动时，本函数被调用，以实现动态显示数据浮窗、高亮曲线、绘制十字线等功能
        
        参数:
        evt: 事件对象，包含鼠标位置等信息
        """
        # 获取鼠标位置
        pos = evt[0]
        # 获取视口矩形
        view_rect = self.plot_widget.viewport().rect()
        # 获取全局坐标系下的鼠标位置
        global_pos = self.plot_widget.mapFromGlobal(QCursor.pos())

        # 如果鼠标位置不在视口矩形内，则隐藏相关显示元素并返回
        if not view_rect.contains(global_pos):
            self.text_item.hide()
            self.hover_marker.clear()
            self.v_line.hide()
            self.h_line.hide()
            self.restore_curve(self.highlighted_curve)
            self.highlighted_curve = None
            return

        # 将鼠标位置映射到视图坐标
        view_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        # 获取鼠标在像素坐标系下的位置
        mouse_pixel_pos = pos.toPoint()

        # 设置像素阈值
        pixel_threshold = 20

        # 初始化最近的曲线及相关信息
        closest_curve = None
        closest_idx = None
        closest_dist = float('inf')
        closest_x_data = None
        closest_y_data = None

        # 遍历所有曲线，寻找最近的点
        for curve, x_data, y_data in self.curves:
            if len(x_data) == 0:
                continue

            for i in range(len(x_data)):
                pt_data = QPointF(x_data[i], y_data[i])
                pt_pixel = self.plot_widget.plotItem.vb.mapViewToScene(pt_data).toPoint()
                dist = (pt_pixel - mouse_pixel_pos).manhattanLength()

                if dist < pixel_threshold and dist < closest_dist:
                    closest_dist = dist
                    closest_curve = curve
                    closest_idx = i
                    closest_x_data = x_data
                    closest_y_data = y_data

        # 如果没有找到最近的曲线，则隐藏相关显示元素并返回
        if closest_curve is None:
            self.text_item.hide()
            self.hover_marker.clear()
            self.v_line.hide()
            self.h_line.hide()
            self.restore_curve(self.highlighted_curve)
            self.highlighted_curve = None
            return

        # 恢复其他曲线原色
        if self.highlighted_curve is not None and self.highlighted_curve != closest_curve:
            self.highlighted_curve.setPen(self.highlighted_curve.default_pen)

        # 高亮当前曲线
        self.highlight_curve(closest_curve)
        self.highlighted_curve = closest_curve

        # 获取命中点坐标
        x_val = closest_x_data[closest_idx]
        y_val = closest_y_data[closest_idx]

        # 显示小圆点
        self.hover_marker.setData([x_val], [y_val])

        # 显示十字线
        self.v_line.setPos(x_val)
        self.h_line.setPos(y_val)
        self.v_line.show()
        self.h_line.show()

        # 显示数据浮窗
        text = f'{closest_curve.name()}\nX: {int(x_val)}\nY: {y_val:.3f}\nMIN: {min(closest_y_data):.3f}\nMAX: {max(closest_y_data):.3f}\nAVG: {np.mean(closest_y_data):.3f}\n'
        self.text_item.setText(text)
        self.text_item.setPos(view_pos.x(), view_pos.y())
        self.text_item.show()


    def highlight_curve(self, curve):
        """将曲线加粗高亮显示"""
        if curve:
            curve.setPen(pg.mkPen(color=curve.default_pen.color(), width=2))


    def restore_curve(self, curve):
        """恢复曲线原始样式"""
        if curve:
            curve.setPen(curve.default_pen)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Tool = DataReplayForm()
    Tool.show()
    sys.exit(app.exec())
