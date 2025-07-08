import sys
import json
import math
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgRenderer
import pyqtgraph as pg
from Ui_Form_RTdata_plot import *
from Ui_Dialog_Select import *


_CONF_PATH = Path(__file__).parent / 'rtdataconf.json'
# 创建svg图标
# 将 SVG 数据写入临时文件或使用 QSvgRenderer 直接渲染
renderer = QSvgRenderer(QByteArray(f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
<path d="M0 96C0 60.7 28.7 32 64 32H384c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96z"/>
</svg>'''.encode()))


def load_config(self, confpath):
    try:
        with open(confpath, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
        config = {}

    return config


def save_config(self):
    try:
        with open(_CONF_PATH, 'w', encoding='utf-8') as f:
            json.dump(_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
        

_CONFIG=load_config(None, _CONF_PATH)




class DataThread(QThread):
    data_updated = pyqtSignal(dict, int)


    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._is_paused = False



    def run(self):
        xtime = 0
        while True:
            self._mutex.lock()
            if self._is_paused:
                self._mutex.unlock()
                self._condition.wait(self._mutex)  # 等待唤醒
                continue
            self._mutex.unlock()

            combined_data = {}
            self.data_updated.emit(combined_data, xtime)
            xtime += 1
            self.msleep(100)



class CurveDialog(QDialog, Ui_Dialog_Select):
    config_updated = pyqtSignal(dict)

    def __init__(self,parent=None):
        super(CurveDialog,self).__init__(parent)
        self.setupUi(self)
        self.init_ui()


    def init_ui(self):
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

        # 填充数据
        self.tableWidget_data.setRowCount(len(_CONFIG))
        for row, (key, info) in enumerate(_CONFIG.items()):
            # 第一列：QCheckBox
            checkbox = QCheckBox()
            checkbox.setChecked(info.get("visible", False))
            checkbox.stateChanged.connect(self.on_check_state_changed)

            # 使用 QWidget 容器包裹控件，并设置居中布局
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)

            self.tableWidget_data.setCellWidget(row, 0, widget)
            # 第二列：名称
            name_item = QTableWidgetItem(f"{info.get('name', key)} ({key})")
            name_item.setFlags(Qt.ItemIsEnabled)
            self.tableWidget_data.setItem(row, 1, name_item)

           
            # 第三列：颜色图标按钮
            color_button = QPushButton()
            color_button.setFixedSize(24, 24)  # 设置为 24x24 正方形
            color_button.setStyleSheet("QPushButton { border: none; padding: 0px; }")  # 去除边框和内边距
            self._set_color_icon(color_button, QColor(info.get('color', '#FF0000')))
            color_button.setObjectName(f"colorBtn_{key}")
            color_button.clicked.connect(lambda _, k=key: self.pick_color(k))

            # 使用 QWidget 容器包裹按钮，并设置居中布局
            widget_color = QWidget()
            layout_color = QHBoxLayout(widget_color)
            layout_color.addWidget(color_button)
            layout_color.setAlignment(Qt.AlignCenter)
            layout_color.setContentsMargins(0, 0, 0, 0)

            self.tableWidget_data.setCellWidget(row, 2, widget_color)

     


    def _set_color_icon(self, button, color):
        svg_image = QImage(24, 24, QImage.Format_ARGB32)
        svg_image.fill(Qt.transparent)
        painter = QPainter(svg_image)
        renderer.render(painter)
        painter.fillRect(svg_image.rect(), color)
        painter.end()
        icon = QIcon(QPixmap.fromImage(svg_image))
        button.setIcon(icon)
        button.setIconSize(QSize(24, 24))


    def pick_color(self, key):
        current_color = QColor(_CONFIG[key]['color'])
        color = QColorDialog.getColor(current_color, self, "选择颜色")
        if color.isValid():
            _CONFIG[key]['color'] = color.name()
            # 更新按钮图标
            for row in range(self.tableWidget_data.rowCount()):
                item_key = self.tableWidget_data.item(row, 1).text().split('(')[-1].strip(')')
                if item_key == key:
                    # 获取容器 widget_color
                    widget_color = self.tableWidget_data.cellWidget(row, 2)
                    # 从容器中找到 QPushButton 按钮
                    color_button = widget_color.findChild(QPushButton)
                    if color_button:
                        self._set_color_icon(color_button, color)
            save_config(self)


    def on_check_state_changed(self):
        checkbox = self.sender()  # 获取触发信号的 QCheckBox
        if not isinstance(checkbox, QCheckBox):
            return
        
        checked_count = 0
        for r in range(self.tableWidget_data.rowCount()):
            widget = self.tableWidget_data.cellWidget(r, 0)
            if widget:
                cb = widget.findChild(QCheckBox)
                if cb and cb.isChecked():
                    checked_count += 1

        if checked_count > 8:
            checkbox.setChecked(False)
            QMessageBox.warning(self, "提示", "最多只能显示8条曲线")

        row = -1
        for r in range(self.tableWidget_data.rowCount()):
            widget = self.tableWidget_data.cellWidget(r, 0)
            if widget and checkbox in widget.children():
                row = r
                break

        if row == -1:
            return

        # 获取 key
        name_item = self.tableWidget_data.item(row, 1)
        if not name_item:
            return
        key = name_item.text().split('(')[-1].strip(')')
        

        # 更新配置
        _CONFIG[key]['visible'] = checkbox.isChecked()
        save_config(self)

        






    
    def on_ok_clicked(self):
        save_config(self)
        self.config_updated.emit(_CONFIG)
        self.accept()  # 关闭对话框






    

    

class DataPlotForm(QWidget, Ui_RTDataPlotForm):
    def __init__(self):
        super(DataPlotForm,self).__init__()
        self.setupUi(self)
        self.data_buffer = {}  
        self.init_system()
        self.init_connections()

    def init_system(self):
        # 初始化绘图区域
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('white')
        self.plot_widget.addLegend()
        self.plot_widget.setLabel('left', '数值')
        self.plot_widget.setLabel('bottom', '时间')
        self.horizontalLayout_plot.addWidget(self.plot_widget)

        # 初始化组件
        self.curves = {}
        self.data_thread = DataThread()
        self.init_curves()



    def init_connections(self):
        self.pushButton_select.clicked.connect(self.show_curve_selector)
        self.pushButton_screenshot.clicked.connect(self.save_screenshot)
        self.pushButton_control.clicked.connect(self.plot_control)
        self.data_thread.data_updated.connect(self.update_plot)


    def clear_curves(self):
        # 1. 从 plot_widget 中移除所有已有曲线
        for curve in self.curves.values():
            self.plot_widget.removeItem(curve)
        self.curves.clear()
        for key in list(self.data_buffer.keys()):
            if not _CONFIG.get(key, {}).get("visible", False):
                del self.data_buffer[key]
        
        # 清空 gridLayout_data 中的所有控件
        self.clear_grid_layout(self.gridLayout_data)


    def clear_grid_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clear_grid_layout(item.layout())  # 递归清除子布局



    def init_curves(self):
        self.clear_curves()
        # 3. 初始化新的可见曲线
        for key, params in _CONFIG.items():
            if not params.get("visible", False):
                continue

            color_str = params.get('color', '#FF0000')
            color = QColor(color_str)
            curve = self.plot_widget.plot(
                pen=pg.mkPen(color, width=2),
                name=params['name']
            )
            self.curves[key] = curve

            

    def init_dataview(self):
        for key, params in _CONFIG.items():
            if not params.get("visible", False):
                continue
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            

            # 添加 label 和 spinbox
            label = QLabel(params['name'])
            label.setObjectName(f'label_{key}')
            doublespinbox = QDoubleSpinBox()
            doublespinbox.setObjectName(f'doublespinbox_{key}')

            layout.addWidget(label, 1)
            layout.addWidget(doublespinbox, 1)









    def update_plot(self, data, xtime):
        xdata = list(range(max(0, xtime - 100), xtime))
    
        for key, curve in self.curves.items():
            if key in data and _CONFIG.get(key, {}).get("visible", False):
                self.data_buffer[key].append(data[key])
                ydata = self.data_buffer[key][-100:]
                curve.setData(xdata[-len(ydata):], ydata)

        # 自动调整Y轴
        visible_data = []
        for key, value in data.items():
            if _CONFIG.get(key, {}).get("visible", False):
                visible_data.append(value)

        if visible_data:
            min_val = min(visible_data)
            max_val = max(visible_data)
            self.plot_widget.setYRange(min_val * 0.9, max_val * 1.1)



    def plot_control(self):
        if self.pushButton_control.text() == "开始":
            self.start_plotting()
        else:
            self.stop_plotting()



    def start_plotting(self):
        if not self.data_thread.isRunning():
            self.data_thread.start()  # 只有不在运行时才启动
        self.data_thread._mutex.lock()
        self.data_thread._is_paused = False
        self.data_thread._condition.wakeAll()  # 唤醒线程继续执行
        self.data_thread._mutex.unlock()
        self.pushButton_control.setText("停止")



    def stop_plotting(self):
        self.data_thread._mutex.lock()
        self.data_thread._is_paused = True
        self.data_thread._mutex.unlock()
        self.pushButton_control.setText("开始")



    def show_curve_selector(self):
        dialog = CurveDialog(self)  # 传入 parent，便于定位窗口
        dialog.setModal(True)
        dialog.config_updated.connect(self.on_config_updated)  # Connect the signal
        dialog.exec_()


    def on_config_updated(self, updated_config):
        global _CONFIG
        _CONFIG = updated_config  # Update the global config

        # Synchronize data_buffer with the updated configuration
        for key in list(self.data_buffer.keys()):
            if not _CONFIG.get(key, {}).get("visible", False):
                del self.data_buffer[key]  # Remove hidden curve's data buffer
            else:
                self.data_buffer.setdefault(key, [])  # Ensure visible curves have a buffer

        self.init_curves()  # Reinitialize curves based on the new config

    def save_screenshot(self):
        pass



    def closeEvent(self, event):
        self.data_thread._is_paused = True
        self.data_thread._condition.wakeAll()  # 唤醒线程以便退出循环
        self.data_thread.quit()
        self.data_thread.wait()
        super().closeEvent(event)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataPlotForm()
    window.show()
    sys.exit(app.exec_())