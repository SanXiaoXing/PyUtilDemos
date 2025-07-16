'''
数据回放工具

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



def generate_color():
    return QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))



class LimitedViewBox(pg.ViewBox):
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
        self.horizontalSlider.valueChanged.connect(self.scroll_plot)
        self.pushButton_plot.clicked.connect(self.draw_plot)
        self.treeWidget_datafile.customContextMenuRequested.connect(self.TreeContextMenuEvent)

    def TreeContextMenuEvent(self, pos):
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
        iterator = QTreeWidgetItemIterator(self.treeWidget_datafile)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(0, Qt.Checked)
            iterator += 1

    def SelectedClear(self):
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
        paths, _ = QFileDialog.getOpenFileNames(self, "选择CSV文件", "", "*.csv")
        if not paths:
            return

        if not hasattr(self, "all_data"):
            self.all_data = {}
        self.col_counter = {}  # 统计所有列名出现次数
        self.column_mapping = {}  # (filename, name) -> (name, unit)

        for path in paths:
            filename = os.path.basename(path)

            # 避免重复加载
            if filename in self.all_data:
                QMessageBox.information(self, "提示", f"{filename} 已被加载，请勿重复操作")
                continue

            try:
                df = pd.read_csv(path, header=[0, 1])  # 两行标题（列名 + 单位）
            except Exception as e:
                QMessageBox.warning(self, "错误", f"读取文件失败：{filename}\n{str(e)}")
                continue

            date_col = df.columns[0][0]  # 第一个列名的第一部分是"时间戳"名称
            df.index = pd.to_datetime(df[df.columns[0]])  # 将时间戳列设为 index
            df.drop(columns=[df.columns[0]], inplace=True)  # 删除原时间列

            self.all_data[filename] = df

            for col in df.columns:
                name, unit = col
                self.col_counter[name] = self.col_counter.get(name, 0) + 1
                self.column_mapping[(filename, name)] = (name, unit)

        # TreeWidget 显示列名（不加单位），但内部保存完整映射
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

        if self.all_data:
            # 更新滑动条范围（取最后一个文件行数）
            last_df = list(self.all_data.values())[-1]
            self.horizontalSlider.setMaximum(len(last_df))




    def draw_plot(self):
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

        for i in range(self.treeWidget_datafile.topLevelItemCount()):
            file_item = self.treeWidget_datafile.topLevelItem(i)
            filename = file_item.text(0)
            df = self.all_data.get(filename)
            if df is None:
                continue

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
        self.timestamps = np.arange(len(combined_df))  # 或改为时间戳：combined_df.index.astype(np.int64) / 1e6
        self.window_width = max(10, int(len(self.timestamps) * 0.1))
        self.scroll_position = 0  # 初始起点

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

        vb = self.view_box
        vb.setLimits(
            xMin=0,
            xMax=len(self.timestamps),
            yMin=y_min,
            yMax=y_max,
            minXRange=10,
            maxXRange=len(self.timestamps),
            minYRange=y_range * 0.01,
            maxYRange=y_range
        )
        vb.setXRange(x_min, x_max, padding=0)
        vb.setYRange(y_min, y_max, padding=0)

        # 设置滑动条最大值为 100（百分比控制）
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setValue(0)


    def scroll_plot(self, value):
        if not hasattr(self, 'timestamps') or len(self.timestamps) == 0:
            return

        total_points = len(self.timestamps)
        if total_points <= self.window_width:
            return

        # 计算起始索引位置
        max_start = total_points - self.window_width
        self.scroll_position = int((value / 100.0) * max_start)
        self.scroll_position = max(0, min(self.scroll_position, max_start))

        vb = self.plot_widget.getViewBox()
        vb.setXRange(self.scroll_position,
                     self.scroll_position + self.window_width,
                     padding=0)


    def eventFilter(self, source, event):
        if source == self.horizontalSlider and event.type() == QEvent.HoverMove:
            pos = event.pos()
            val = self.horizontalSlider.minimum() + (
                (self.horizontalSlider.maximum() - self.horizontalSlider.minimum())
                * pos.x()
                / self.horizontalSlider.width()
            )
            index = int(len(self.data) * (val / 100.0))
            if 0 <= index < len(self.data):
                try:
                    timestamp = self.data.index[index]
                    if isinstance(timestamp, pd.Timestamp):
                        tip = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    else:
                        tip = str(timestamp)
                    # ✅ 修复：显示在 horizontalSlider 上方
                    QToolTip.showText(self.horizontalSlider.mapToGlobal(pos), tip)
                except Exception:
                    pass
        return super().eventFilter(source, event)




    def onMouseMoved(self, evt):
        pos = evt[0]
        view_rect = self.plot_widget.viewport().rect()
        global_pos = self.plot_widget.mapFromGlobal(QCursor.pos())

        if not view_rect.contains(global_pos):
            self.text_item.hide()
            self.hover_marker.clear()
            self.v_line.hide()
            self.h_line.hide()
            self.restore_curve(self.highlighted_curve)
            self.highlighted_curve = None
            return

        view_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        mouse_pixel_pos = pos.toPoint()

        pixel_threshold = 20

        closest_curve = None
        closest_idx = None
        closest_dist = float('inf')
        closest_x_data = None
        closest_y_data = None

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
        text = f"{closest_curve.name()}\nX: {int(x_val)}\nY: {y_val:.3f}"
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
