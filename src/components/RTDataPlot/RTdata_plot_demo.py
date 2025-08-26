'''
曲线实时绘制模块
===============

功能：
- 可设置X轴(固定/滚动)和Y轴(固定/自动)模式
- 可选择是否保存曲线数据
- 可对待绘制数据进行选择并进行颜色配置
- 可进行数据存储

使用方法：
- 该工具具有独立可运行的界面， 也可以将其作为模块嵌入到其他界面中
- 数据源为实时数据，数据格式为字典，包含多个键值对，每个键值对表示一条曲线的数据
- DataThread类为数据获取线程,负责从数据源获取数据并传递给主线程进行绘制,可在DataThread中替换真实数据源


Author: JIN && <jjyrealdeal@163.com>
Date: 2025-07-14 11:55:30
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.components.RTDataPlot.Ui_Dialog_Select import Ui_Dialog_Select
import json
import math
import csv
import datetime
from collections import deque
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from src.components.RTDataPlot.Ui_Form_RTdata_plot import *
from assets import ICON_PLAY,ICON_PAUSE,ICON_STOP


_CONF_PATH = Path(__file__).parent / 'rtdataconf.json' #  配置文件路径
_BASE_PATH= Path(__file__).parent  # 项目路径




def load_config(confpath):
    """加载曲线配置文件"""
    try:
        with open(confpath, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"加载配置失败: {str(e)}")
        config = {}

    return config


def save_config():
    """保存曲线配置文件"""
    try:
        with open(_CONF_PATH, 'w', encoding='utf-8') as f:
            json.dump(_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print( f"保存配置失败: {str(e)}")
        

_CONFIG=load_config( _CONF_PATH) # 加载配置文件


class DataThread(QThread):
    """数据获取线程"""
    data_updated = pyqtSignal(dict, int) # 数据更新信号，传递数据字典和x轴时间

    def __init__(self):
        super().__init__()
        self._mutex = QMutex() # 互斥锁
        self._condition = QWaitCondition() # 条件变量
        self._is_paused = False # 暂停标志
        self._is_running = True  # 运行标志
        self._is_stopped = False  # 新增停止标志
        self.xtime = 0  # 将 xtime 移到类级别以便重置

    def run(self):
        xtime = 0
        keys = [k for k in _CONFIG.keys()]
        while self._is_running:
            self._mutex.lock()
            if self._is_paused and not self._is_stopped:
                self._condition.wait(self._mutex)
            elif self._is_stopped:
                self.xtime = 0
                self._is_stopped = False  # 重置停止标志
            self._mutex.unlock()

            # 判断退出标志，避免唤醒后继续执行
            if not self._is_running:
                break
            
            """ 生成模拟数据（此处可替换为真实数据源）"""
            combined_data = {}
            for i, key in enumerate(keys):
                angle = xtime * 0.1 
                combined_data[key] = math.sin(angle)+i

            self.data_updated.emit(combined_data, xtime) # 发送数据更新信号
            xtime += 1
            self.msleep(100)


    def pause(self):
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()


    def resume(self):
        self._mutex.lock()
        self._is_paused = False
        self._condition.wakeAll()
        self._mutex.unlock()


    def stop(self):
        self._mutex.lock() # 获取锁
        self._is_running = False # 停止运行
        self._is_stopped = True # 设置停止标志
        self._condition.wakeAll() # 唤醒所有等待的线程
        self._mutex.unlock() # 释放锁



class CurveDialog(QDialog, Ui_Dialog_Select):
    """曲线选择与颜色设置对话框"""
    config_updated = pyqtSignal(dict)

    def __init__(self,parent=None):
        super(CurveDialog,self).__init__(parent)
        self.setupUi(self)
        self.data_keys = list(_CONFIG.keys())
        self.checked_count = 0
        self.max_checked = 8   # 设置最多显示8条曲线
        self.init_ui()
        self.init_data()
        self.update_checkbox_enabled_state()


    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('选择数据')
        self.tableWidget_data.setColumnCount(3)
        self.tableWidget_data.setHorizontalHeaderLabels(['启用', '名称', '颜色'])
        self.tableWidget_data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget_data.setSelectionMode(QAbstractItemView.NoSelection)
        self.tableWidget_data.setColumnWidth(0, 60)
        self.tableWidget_data.setColumnWidth(1, 200)
        self.tableWidget_data.setColumnWidth(2, 60)

        header = self.tableWidget_data.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

        self.buttonBox.accepted.connect(self.on_ok_clicked)

        

    def init_data(self):
        """初始化数据"""
        # 填充数据
        self.tableWidget_data.setRowCount(len(_CONFIG))
        for row, key in enumerate(self.data_keys):
            config = _CONFIG[key]

            # 第一列：checkbox
            checkbox = QCheckBox()
            is_checked = config.get("visible", False)
            checkbox.setChecked(is_checked)
            if is_checked:
                self.checked_count += 1

            checkbox.stateChanged.connect(self.generate_checkbox_handler(row, key))

            #  包装成居中的 QWidget
            center_widget = QWidget()
            layout = QHBoxLayout(center_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)

            self.tableWidget_data.setCellWidget(row, 0, center_widget)

            # 第二列：name
            item = QTableWidgetItem(config.get("name", ""))
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.tableWidget_data.setItem(row, 1, item)

            # 第三列：颜色按钮
            color = QColor(config.get("color", "#000000"))
            color_btn = QPushButton()
            color_btn.setIcon(self.colored_icon(color))
            color_btn.setIconSize(QSize(24, 24))
            color_btn.clicked.connect(self.generate_color_button_handler(row, key))
            self.tableWidget_data.setCellWidget(row, 2, color_btn)

     

    def generate_checkbox_handler(self, row, key):
        """
        生成checkbox事件处理函数
        
        :param row: 行号，用于定位表格中的checkbox控件
        :param key: 配置项的键值，用于更新对应的配置状态
        :return: 返回一个处理checkbox状态变化的闭包函数
        """
        def handler(state):
            # 获取指定行和列的单元格控件，并查找其中的checkbox
            cell_widget = self.tableWidget_data.cellWidget(row, 0)
            checkbox = cell_widget.findChild(QCheckBox) if cell_widget else None

            # 处理checkbox选中状态的变化
            if state == Qt.Checked:
                # 检查是否超过最大选中数量限制
                if self.checked_count >= self.max_checked:
                    # 超过限制时，阻止信号并取消选中状态
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                    return
                self.checked_count += 1
            else:
                # 取消选中时减少计数
                self.checked_count -= 1

            # 更新配置文件中对应项的可见性设置
            _CONFIG[key]["visible"] = (state == Qt.Checked)
            save_config()

            # 更新所有checkbox的可用状态
            self.update_checkbox_enabled_state()

        return handler
    

    def update_checkbox_enabled_state(self):
        """更新所有 checkbox 的可用状态"""
        for row, key in enumerate(self.data_keys):
            cell_widget = self.tableWidget_data.cellWidget(row, 0)
            checkbox = cell_widget.findChild(QCheckBox) if cell_widget else None
            if checkbox:
                if not checkbox.isChecked():
                    checkbox.setEnabled(self.checked_count < self.max_checked)



    def generate_color_button_handler(self, row, key):
        """
        生成颜色按钮事件处理函数
        
        该函数创建一个闭包，用于处理颜色选择按钮的点击事件。当按钮被点击时，
        会打开颜色选择对话框，允许用户选择新的颜色。如果用户选择了有效颜色，
        则更新配置文件中的颜色值，更新按钮图标，并保存配置。
        
        参数:
            row (int): 表格中的行号，用于定位需要更新的按钮控件
            key (str): 配置字典中的键名，用于访问和更新对应的配置项
            
        返回:
            function: 返回一个无参的事件处理函数，该函数捕获row和key参数形成闭包
        """
        def handler():
            # 获取当前配置的颜色值，如果不存在则使用默认黑色
            current_color = QColor(_CONFIG[key].get("color", "#000000"))
            # 打开颜色选择对话框，让用户选择新颜色
            new_color = QColorDialog.getColor(initial=current_color)
            # 如果用户选择了有效颜色，则更新配置和界面
            if new_color.isValid():
                _CONFIG[key]["color"] = new_color.name()
                btn = self.tableWidget_data.cellWidget(row, 2)
                btn.setIcon(self.colored_icon(new_color))
                save_config()
        return handler



    def colored_icon(self, color: QColor):
        """生成一个带有颜色的图标"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.black)
        painter.drawEllipse(2, 2, 20, 20)
        painter.end()
        return QIcon(pixmap)


    def on_ok_clicked(self):
        """保存配置并关闭对话框"""
        self.config_updated.emit(_CONFIG)  # 发送配置更新信号
        self.accept()  # 关闭对话框


class DataPlotForm(QWidget, Ui_RTDataPlotForm):
    """运行时数据曲线显示窗体"""
    def __init__(self):
        super(DataPlotForm,self).__init__()
        self.setupUi(self)
        self.setWindowTitle('数据采集')
        self.data_buffer = {}  
        self.auto_y_scale = False  # 默认固定
        self.scroll_x_mode = False  # 默认固定
        self.should_save_data = False
        self.is_stopped = True
        self.saved_rows = []
        self.init_plot_system()
        self.init_connections()


    def init_plot_system(self):
        """初始化绘图系统"""
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('white')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.5)  # 显示网格
        self.plot_widget.setLabel('left', '数值')
        self.plot_widget.setLabel('bottom', '时间')
        self.gridLayout_plot.addWidget(self.plot_widget)


        # 初始化组件
        self.curves = {}
        self.data_thread = DataThread()
        self.init_curves()
        self.init_dataview()



    def init_connections(self):
        """初始化连接"""
        self.pushButton_select.clicked.connect(self.show_curve_selector)
        self.pushButton_control.setIcon(QIcon(ICON_PLAY))
        self.pushButton_control.clicked.connect(self.plot_control)
        self.pushButton_stop.setIcon(QIcon(ICON_STOP))
        self.pushButton_stop.clicked.connect(self.stop_plotting)
        self.data_thread.data_updated.connect(self.update_plot)
        self.horizontalSlider_X.valueChanged.connect(self.toggle_x_mode)
        self.horizontalSlider_Y.valueChanged.connect(self.toggle_y_autoscale)
        self.checkBox_savedata.stateChanged.connect(self.toggle_save_data)



    def clear_curves(self):
        """清空所有曲线"""
        # 从 plot_widget 中移除所有已有曲线
        for curve in self.curves.values():
            self.plot_widget.removeItem(curve)
        self.curves.clear()
        # 清空 data_buffer 中所有不可见的 key
        for key in list(self.data_buffer.keys()):
            if not _CONFIG.get(key, {}).get("visible", False):
                del self.data_buffer[key]


    def toggle_y_autoscale(self,value):
        """切换Y轴缩放模式"""
        if value == 0:  # 固定模式
            self.auto_y_scale=False
        elif value == 1:  # 自动模式
           self.auto_y_scale=True

        


    def toggle_x_mode(self,value):
        """切换X轴模式"""
        if value == 0:  # 固定模式
            self.scroll_x_mode=False
        elif value == 1:  # 滚动模式
           self.scroll_x_mode=True


    
    def toggle_save_data(self,state):
        """启用保存数据"""
        if state == Qt.Checked:  # 启用保存数据
            self.data_thread.save_data = True
        else:  # 禁用保存数据
            self.data_thread.save_data = False
    


    def init_curves(self):
        """初始化曲线"""
        self.clear_curves()
        # 初始化新的可见曲线
        for key, params in _CONFIG.items():
            if not params.get("visible", False):
                continue

            color_str = params.get('color', '#FF0000')
            color = QColor(color_str)
            
            # 初始化曲线，并将实时数据添加到name中
            curve = self.plot_widget.plot(
                pen=pg.mkPen(color, width=2),
                name = params.get('name', key),
                color = params.get('color', '#FF0000')
            )
            self.curves[key] = curve



    def init_dataview(self):
        """初始化数据视图"""
        # 清空原布局
        while self.gridLayout_dataview.count():
            item = self.gridLayout_dataview.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # 重新添加可见参数的 label + spinbox
        row = 0
        for key, params in _CONFIG.items():
            if not params.get("visible", False):
                continue

            label = QLabel(params['name'])
            label.setObjectName(f'label_{key}')

            spinbox = QDoubleSpinBox()
            spinbox.setDecimals(3)
            spinbox.setRange(-1e6, 1e6)
            spinbox.setReadOnly(True)
            spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
            spinbox.setObjectName(f'doublespinbox_{key}')

            self.gridLayout_dataview.addWidget(label, row, 0)
            self.gridLayout_dataview.addWidget(spinbox, row, 1)
            row += 1

        # 添加一个 vertical spacer 占据剩余空间，使控件靠上排列
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.gridLayout_dataview.addItem(spacer, row, 0, 1, 2)



    def update_plot(self, data, xtime):
        """
        更新 PyQtGraph 图表显示内容，包括曲线数据和相关控件状态。

        参数:
            data (dict): 包含各曲线键值对的字典，用于更新图表数据。
            xtime (int): 当前时间戳，作为 X 轴最新数据点的时间基准。

        返回值:
            无
        """
        # 如果需要保存数据，则将数据添加到 saved_rows 中
        if self.should_save_data:
            row = []
            for key in _CONFIG:
                row.append(data.get(key, ""))
            self.saved_rows.append(row)

        # 遍历 curves 字典，更新每个曲线的数据
        for key, curve in self.curves.items():
            # 如果数据中包含该键，并且该键在 _CONFIG 中可见，则更新曲线数据
            if key in data and _CONFIG.get(key, {}).get("visible", False):
                # 如果该键不在 data_buffer 中，则创建一个 deque，最大长度为10000
                if key not in self.data_buffer:
                    self.data_buffer[key] = deque(maxlen=10000) 

                # 将数据添加到 data_buffer 中
                self.data_buffer[key].append(data[key])
                ydata_full = list(self.data_buffer[key])

                # 构建完整 x 轴（以当前 xtime 为尾部）
                start_xtime = xtime - len(ydata_full) + 1
                xdata_full = list(range(start_xtime, xtime + 1))

                # 决定显示区域
                if self.scroll_x_mode:
                    # 滚动模式：仅显示最近100个点
                    ydata = ydata_full[-100:]
                    xdata = xdata_full[-100:]
                    self.plot_widget.setXRange(xdata[0], xdata[-1], padding=0)
                else:
                    # 固定模式：显示全部历史
                    ydata = ydata_full
                    xdata = xdata_full
                    self.plot_widget.enableAutoRange(axis='x', enable=True)  # 可选：自动扩展X轴

                # 如果 xdata 和 ydata 长度相同，则更新曲线数据
                if len(xdata) == len(ydata):
                    curve.setData(x=xdata, y=ydata)
                    #  更新 SpinBox 的值
                    spinbox = self.findChild(QDoubleSpinBox, f'doublespinbox_{key}')
                    if spinbox:
                        spinbox.setValue(ydata[-1])


        # 自动 Y 轴缩放
        if self.auto_y_scale:
            # 获取所有可见数据的最小值和最大值
            visible_data = [data[k] for k in data if _CONFIG.get(k, {}).get("visible", False)]
            if visible_data:
                min_val = min(visible_data)
                max_val = max(visible_data)
                # 设置 Y 轴范围，最小值为最小值的0.9倍，最大值为最大值的1.1倍
                self.plot_widget.setYRange(min_val * 0.9, max_val * 1.1)


    def plot_control(self):
        """控制图表显示模式"""
        if self.pushButton_control.text() == "开始":
            self.start_plotting()
        elif self.pushButton_control.text() == "暂停":
            self.pause_plotting()



    def start_plotting(self):
        """
        开始绘图功能
        
        该函数负责启动数据采集和绘图显示功能。如果当前处于停止状态，
        则会清理历史数据并重新初始化绘图组件，然后启动数据采集线程；
        如果当前处于暂停状态，则恢复数据采集线程的运行。
        """
        self.should_save_data = self.checkBox_savedata.isChecked()

        # 如果当前处于停止状态，需要重新初始化绘图环境
        if self.is_stopped:
            self.saved_rows.clear()
            self.data_buffer.clear()

            for curve in self.curves.values():
                curve.clear()

            self.plot_widget.clear()
            self.init_curves()  # 重新加上 legend

            self.plot_widget.enableAutoRange(axis='x', enable=False)
            self.plot_widget.setXRange(0, 100, padding=0)

            # 启动新线程进行数据采集
            self.data_thread = DataThread()
            self.data_thread.data_updated.connect(self.update_plot)
            self.data_thread.start()

            self.is_stopped = False  # 标记为非停止
        else:
            # 当前处于暂停状态，恢复数据采集线程
            self.data_thread.resume()

        self.pushButton_control.setText("暂停")
        self.pushButton_control.setIcon(QIcon(ICON_PAUSE))




    def pause_plotting(self):
        """暂停绘图"""
        self.data_thread.pause()
        self.pushButton_control.setText("开始")
        self.pushButton_control.setIcon(QIcon(ICON_PLAY))



    def stop_plotting(self):
        """
        停止数据采集和绘图，并保存已收集的数据到CSV文件
        
        该函数执行以下操作：
        1. 停止数据采集线程
        2. 更新控制按钮状态为"开始"
        3. 设置停止标志
        4. 如果需要保存数据且存在已收集数据，则将数据保存到CSV文件
        """
        self.data_thread.stop()
        self.pushButton_control.setText("开始")
        self.pushButton_control.setIcon(QIcon(ICON_PLAY))
        self.is_stopped = True

        # 如果需要保存数据且存在已收集的数据，则保存到CSV文件
        if self.should_save_data and self.saved_rows:
            # 生成带时间戳的文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"试验数据_{timestamp}.csv"
            save_path = _BASE_PATH / f'saveddata/{filename}'

            # 写入 CSV 文件
            with open(save_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # 写表头
                header = ["时间戳"]+[v["name"] for k, v in _CONFIG.items()]
                writer.writerow(header)

                # 单位行（第2行）：单位
                unit_row = ["ms"] + [v.get("unit", "") for k, v in _CONFIG.items()]
                writer.writerow(unit_row)

                # 写数据（为每行加时间戳）
                start_time = datetime.datetime.now()
                for i, row in enumerate(self.saved_rows):
                    row_time = start_time + datetime.timedelta(milliseconds=100 * i)  # 假设每100ms一条
                    timestr = row_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 精确到毫秒
                    writer.writerow([timestr] + row)

            print(f"数据已保存至：{save_path}")
            self.saved_rows = []  # 清空旧数据



    def show_curve_selector(self):
        """显示曲线选择对话框"""
        dialog = CurveDialog(self)  # 传入 parent，便于定位窗口
        dialog.setModal(True)
        dialog.config_updated.connect(self.on_config_updated)  # Connect the signal
        dialog.exec_()


    def on_config_updated(self, updated_config):
        """
        当配置更新时的回调函数，用于同步数据缓冲区并重新初始化曲线显示
        
        :param updated_config: 更新后的配置字典，包含各个曲线的配置信息
        """
        # 同步数据缓冲区与更新后的配置
        for key in list(self.data_buffer.keys()):
            if not updated_config.get(key, {}).get("visible", False):
                del self.data_buffer[key]  # 移除隐藏曲线的数据缓冲区
            else:
                self.data_buffer.setdefault(key, [])  # 确保可见曲线拥有数据缓冲区

        self.init_curves()  # 根据新配置重新初始化曲线
        self.init_dataview()  # 重新初始化数据视图


    def closeEvent(self, event):
        # 停止线程安全退出
        self.data_thread.stop()
        self.data_thread.wait()
        super().closeEvent(event)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataPlotForm()
    window.show()
    sys.exit(app.exec_())