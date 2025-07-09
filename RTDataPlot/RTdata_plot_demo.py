import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
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
from assets import ICON_SQUARE


_CONF_PATH = Path(__file__).parent / 'rtdataconf.json'



# 创建svg图标
renderer = QSvgRenderer(ICON_SQUARE)


def load_config(confpath):
    try:
        with open(confpath, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"加载配置失败: {str(e)}")
        config = {}

    return config


def save_config():
    try:
        with open(_CONF_PATH, 'w', encoding='utf-8') as f:
            json.dump(_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print( f"保存配置失败: {str(e)}")
        

_CONFIG=load_config( _CONF_PATH)




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
        self.data_keys = list(_CONFIG.keys())
        self.checked_count = 0
        self.max_checked = 8
        self.init_ui()
        self.init_data()
        self.update_checkbox_enabled_state()


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

        self.buttonBox.accepted.connect(self.on_ok_clicked)

        

    def init_data(self):
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

            # ✅ 包装成居中的 QWidget
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
        def handler(state):
            cell_widget = self.tableWidget_data.cellWidget(row, 0)
            checkbox = cell_widget.findChild(QCheckBox) if cell_widget else None

            if state == Qt.Checked:
                # print(self.checked_count)
                if self.checked_count >= self.max_checked:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                    return
                self.checked_count += 1
            else:
                self.checked_count -= 1
            print(self.checked_count)

            _CONFIG[key]["visible"] = (state == Qt.Checked)
            save_config()

            # 更新所有 checkbox 的可用状态
            self.update_checkbox_enabled_state()

        return handler
    

    def update_checkbox_enabled_state(self):
        for row, key in enumerate(self.data_keys):
            cell_widget = self.tableWidget_data.cellWidget(row, 0)
            checkbox = cell_widget.findChild(QCheckBox) if cell_widget else None
            if checkbox:
                if not checkbox.isChecked():
                    checkbox.setEnabled(self.checked_count < self.max_checked)



    def generate_color_button_handler(self, row, key):
        def handler():
            current_color = QColor(_CONFIG[key].get("color", "#000000"))
            new_color = QColorDialog.getColor(initial=current_color)
            if new_color.isValid():
                _CONFIG[key]["color"] = new_color.name()
                btn = self.tableWidget_data.cellWidget(row, 2)
                btn.setIcon(self.colored_icon(new_color))
                save_config()
        return handler



    def colored_icon(self, color: QColor):
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
        self.clear_grid_layout(self.gridLayout_dataview)
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
        # Synchronize data_buffer with the updated configuration
        for key in list(self.data_buffer.keys()):
            if not updated_config.get(key, {}).get("visible", False):
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