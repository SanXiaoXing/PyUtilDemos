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
from assets import ICON_BACKWARD




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
        self.all_data = {}
        self.curves=[]
        self.initUI()
        self.init_graph()
        self.init_connections()
        

    def initUI(self):
        self.setWindowTitle('数据回放')
        self.treeWidget_datafile.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeWidget_datafile.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pushButton_plot.setIcon(QIcon(ICON_BACKWARD))
   




    def init_graph(self):
        self.view_box = LimitedViewBox()
        self.plot_widget = pg.PlotWidget(viewBox=self.view_box)
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        self.gridLayout_plot.addWidget(self.plot_widget)

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
        CheckedAll = QAction('全选')
        CheckedAll.triggered.connect(self.SelectedAll)
        UncheckedAll = QAction('取消全选')
        UncheckedAll.triggered.connect(self.SelectedClear)
        OpenFile=QAction('添加文件')
        OpenFile.triggered.connect(self.load_csv)
        RemoveFIle=QAction('移除文件')
        RemoveFIle.triggered.connect(self.remove_file)
        ClearAll=QAction('清空列表')
        ClearAll.triggered.connect(self.clear_all_files)
        
        
        TreeMenu.addActions([OpenFile,
                             RemoveFIle,
                             CheckedAll, 
                             UncheckedAll,
                             ClearAll
                             ])
        
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
        self.column_mapping = {}  # (filename, col) -> original_col

        for path in paths:
            filename = os.path.basename(path)
            #  避免重复加载文件
            if filename in self.all_data:
                QMessageBox.information(self, "提示", f"{filename} 已被加载，请勿重复操作")
                continue

            df = pd.read_csv(path)

            date_col = df.columns[0]
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)

            self.all_data[filename] = df

            for col in df.columns:
                self.col_counter[col] = self.col_counter.get(col, 0) + 1
                self.column_mapping[(filename, col)] = col

        # TreeWidget 显示原始列名（不加后缀）
        for filename, df in self.all_data.items():
            exists = False
            for i in range(self.treeWidget_datafile.topLevelItemCount()):
                item = self.treeWidget_datafile.topLevelItem(i)
                if item.text(0) == filename:
                    exists = True
                    break
            if not exists:
                root = QTreeWidgetItem([filename])
                root.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsAutoTristate)
                root.setCheckState(0, Qt.Unchecked)
                for col in df.columns:
                    item = QTreeWidgetItem([col])
                    item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsAutoTristate)
                    item.setCheckState(0, Qt.Unchecked)
                    root.addChild(item)
                self.treeWidget_datafile.addTopLevelItem(root)
                root.setExpanded(True)

        if self.all_data:
            # 更新滑动条范围
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
                    if self.col_counter[col] > 1:
                        legend_name = f"{col} ({filename})"
                    else:
                        legend_name = col

                    # 添加到绘图数据
                    combined_df[legend_name] = df[col]
                    self.selected_columns.append((legend_name, legend_name))

        if combined_df.empty:
            return
        self.data = combined_df
        x_float = np.arange(len(combined_df))

        for i, (colname, legend_name) in enumerate(self.selected_columns):
            y = self.data[legend_name].to_numpy()
            color = QColor.fromHsv((i * 30) % 255, 200, 230)  # 通过 HSV 生成协调色
            curve = self.plot_widget.plot(x_float, y, pen=pg.mkPen(color=color, width=1), name=legend_name)
            curve.default_pen = pg.mkPen(color=color, width=1)  # 保存默认画笔
            self.curves.append((curve, x_float, y))

        

        x_min, x_max = x_float[0], x_float[-1]
        y_min, y_max = combined_df.min().min(), combined_df.max().max()
        x_range = x_max - x_min
        y_range = y_max - y_min

        vb = self.view_box  # 你自定义的ViewBox实例
        vb.setLimits(
            xMin=x_min,
            xMax=x_max,
            yMin=y_min,
            yMax=y_max,
            minXRange=x_range * 0.01,
            maxXRange=x_range,
            minYRange=y_range * 0.01,
            maxYRange=y_range
        )

        vb.setXRange(x_min, x_max, padding=0)
        vb.setYRange(y_min, y_max, padding=0)





    def scroll_plot(self, value):
        full_x = self.data.index
        if full_x.empty:
            return

        total_points = len(self.data)
        view_width = int(total_points * 0.1)
        start_index = int(total_points * (value / 100.0))
        end_index = start_index + view_width

        start_index = max(0, min(start_index, total_points - view_width))
        end_index = min(total_points, end_index)

        vb = self.plot_widget.getViewBox()
        vb.setXRange(start_index, end_index, padding=0)


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
            curve.setPen(pg.mkPen(color=curve.default_pen.color(), width=3))


    def restore_curve(self, curve):
        """恢复曲线原始样式"""
        if curve:
            curve.setPen(curve.default_pen)







if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Tool = DataReplayForm()
    Tool.show()
    sys.exit(app.exec())
