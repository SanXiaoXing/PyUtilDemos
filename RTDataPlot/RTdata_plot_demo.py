import sys
import json
import math
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from Ui_Form_RTdata_plot import *
from Ui_Dialog_Select import *


_CONF_PATH = Path(__file__).parent / 'rtdataconf.json'


class DataThread(QThread):
    data_updated = pyqtSignal(dict, int)

    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._is_paused = False
        self.config = {}
        self.data_buffer = {}

    def load_config(self, config_path):
        with open(config_path, encoding='utf-8') as f:
            self.config = json.load(f)
            for key in self.config:
                self.data_buffer[key] = []

    def run(self):
        xtime = 0
        while True:
            self._mutex.lock()
            if self._is_paused:
                self._condition.wait(self._mutex)
            self._mutex.unlock()

            # 模拟数据生成逻辑
            new_data = {}
            for key, params in self.config.items():
                if params['visible']:
                    new_data[key] = 50 + 30 * math.sin(0.1 * xtime)
            
            self.data_updated.emit(new_data, xtime)
            xtime += 1
            self.msleep(100)

class CurveDialog(QDialog, Ui_Dialog_Select):
    config_updated = pyqtSignal(dict)

    def __init__(self):
        super(CurveDialog,self).__init__()
        self.setupUi(self)
        self.init_ui()

    def init_ui(self):
        pass

    

class DataPlotForm(QWidget, Ui_RTDataPlotForm):
    def __init__(self):
        super(DataPlotForm,self).__init__()
        self.setupUi(self)
        self.curvedialog=CurveDialog()
        self.init_system()

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
        self.init_connections()
        self.load_config()


    def init_connections(self):
        self.pushButton_select.clicked.connect(self.show_curve_selector)
        self.pushButton_screenshot.clicked.connect(self.save_screenshot)

    def load_config(self):
        self.data_thread.load_config(_CONF_PATH)
        self.init_curves()



    def init_curves(self):
        for key, params in self.data_thread.config.items():
            color_str = params.get('color', '#FF0000')
            color = QColor(color_str)
            self.curves[key] = self.plot_widget.plot(
                pen=pg.mkPen(color, width=2),
                name=params['name']
            )



    def update_plot(self, data, xtime):
        xdata = list(range(max(0, xtime-100), xtime))
        for key, curve in self.curves.items():
            if key in data:
                self.data_thread.data_buffer[key].append(data[key])
                ydata = self.data_thread.data_buffer[key][-100:]
                curve.setData(xdata[-len(ydata):], ydata)

        # 自动调整Y轴
        visible_data = [v for k, v in data.items() 
                      if self.data_thread.config[k]['visible']]
        if visible_data:
            min_val = min(visible_data)
            max_val = max(visible_data)
            self.plot_widget.setYRange(min_val*0.9, max_val*1.1)


    def show_curve_selector(self):
        self.curvedialog.show()


    def save_screenshot(self):
        pass







if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataPlotForm()
    window.show()
    sys.exit(app.exec_())