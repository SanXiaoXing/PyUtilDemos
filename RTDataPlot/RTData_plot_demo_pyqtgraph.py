import sys
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg


class PlotThread(QThread):
    update_signal = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._is_paused = False
        self._is_stopped = False
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self.xtime = 0

    def run(self):
        frequency = 0.02  # 控制正弦波频率
        amplitude = 50    # 幅值
        offset = 50       # 中心偏移量

        while True:
            self._mutex.lock()
            if self._is_stopped:
                self._mutex.unlock()
                break
            while self._is_paused:
                self._condition.wait(self._mutex)
            self._mutex.unlock()

            # 使用正弦函数生成模拟数据
            data = int(offset + amplitude * math.sin(frequency * self.xtime))
            self.xtime += 1
            self.update_signal.emit(data, self.xtime)
            QThread.msleep(100)

    def stop(self):
        self._mutex.lock()
        self._is_stopped = True
        self._is_paused = False
        self._condition.wakeAll()
        self._mutex.unlock()

    def pause(self):
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()

    def resume(self):
        self._mutex.lock()
        self._is_paused = False
        self._condition.wakeAll()
        self._mutex.unlock()

    def reset(self):
        self._mutex.lock()
        self._is_stopped = False
        self._is_paused = False
        self.xtime = 0
        self._mutex.unlock()


class MainFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('RTDataPlot - PyQtGraph')
        screen = QApplication.desktop().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        window_width = 800
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        # 创建 PyQtGraph 图形控件
        # 创建 PyQtGraph 图形控件
        self.plot_widget = pg.PlotWidget(title="实时曲线")
        self.plot_widget.setLabel('left', '值')
        self.plot_widget.setLabel('bottom', '时间')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        self.plot_widget.setBackground('w')  # 设置背景为白色

        # 初始化曲线
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='b', width=1), name='信号')

        # 按钮布局
        button_layout = QHBoxLayout()
        self.btn_start = QPushButton('Start', self)
        self.btn_stop = QPushButton('Stop', self)
        self.btn_pause = QPushButton('Pause', self)
        self.btn_resume = QPushButton('Resume', self)

        for btn in [self.btn_start, self.btn_stop, self.btn_pause, self.btn_resume]:
            button_layout.addWidget(btn)

        self.btn_start.clicked.connect(self.start_plotting)
        self.btn_stop.clicked.connect(self.stop_plotting)
        self.btn_pause.clicked.connect(self.pause_plotting)
        self.btn_resume.clicked.connect(self.resume_plotting)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.plot_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # 数据初始化
        self.xdata = []
        self.ydata = []

        # 线程初始化
        self.plot_worker = PlotThread()
        self.plot_worker.update_signal.connect(self.update_plot)

    def start_plotting(self):
        """开始绘图"""
        if self.plot_worker.isRunning():
            self.plot_worker.stop()
            self.plot_worker.wait()

        self.xdata.clear()
        self.ydata.clear()
        self.curve.clear()

        self.plot_worker.reset()
        self.plot_worker.start()

    def stop_plotting(self):
        """停止线程并清空数据"""
        if self.plot_worker.isRunning():
            self.plot_worker.stop()
            self.plot_worker.wait()
        self.xdata.clear()
        self.ydata.clear()
        self.curve.clear()

    def pause_plotting(self):
        """暂停线程"""
        if self.plot_worker.isRunning():
            self.plot_worker.pause()

    def resume_plotting(self):
        """恢复线程"""
        if self.plot_worker.isRunning():
            self.plot_worker.resume()

    def update_plot(self, data, xtime):
        """更新 PyQtGraph 图表"""
        self.xdata.append(xtime)
        self.ydata.append(data)

        # 只显示最近100个点
        self.xdata = self.xdata[-100:]
        self.ydata = self.ydata[-100:]

        self.curve.setData(self.xdata, self.ydata)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainFrame()
    ex.show()
    sys.exit(app.exec_())