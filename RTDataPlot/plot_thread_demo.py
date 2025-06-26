"""demo:曲线动态显示"""


import time
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import random






class PlotThread(QThread):
    # 定义信号，用于数据到 UI
    update_signal = pyqtSignal(int, int)
    

    def __init__(self):
        super().__init__()
        self._is_paused = False  # 暂停标志
        self._is_stopped = False  # 停止标志
        self._condition=QWaitCondition()
        self._mutex=QMutex()
        self.xtime=0
        self.plot_data = None
     
    #TIps 外部调用该函数向线程中传递参数
    def set_data(self,data):
        """设置数据"""
        with QMutexLocker(self._mutex):
            self.plot_data = data


    def run(self):
        """线程启动则自动执行run中的函数"""
        while self.isRunning():
            # 检查是否需要停止线程
            self._mutex.lock()
            if self._is_stopped:
                self._mutex.unlock()
                break
            while self._is_paused:  # 线程暂停
                self._condition.wait(self._mutex)
            self._mutex.unlock()
            self.plot_data = random.randint(0, 100)   # 模拟数据
            if self.plot_data:
                self.xtime=self.xtime+1
                self.update_signal.emit(self.plot_data,self.xtime)
            else:
                print("Plot Data:No data to emit.")  # Debug output
            QThread.msleep(500)


    def stop(self):
        """停止线程"""
        self._mutex.lock()
        self._is_stopped = True
        self._is_paused = False  # 确保不会卡在暂停状态
        self._condition.wakeAll()  # 让 wait() 退出
        self._mutex.unlock()

    def pause(self):
        """暂停线程执行"""
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()

    def resume(self):
        """恢复线程执行"""
        self._mutex.lock()
        self._is_paused = False
        self._condition.wakeAll()  # 让 wait() 退出
        self._mutex.unlock()


    def reset(self):
        """ 重新启动前重置状态 """
        self._mutex.lock()
        self._is_stopped = False
        self._is_paused = False
        self._mutex.unlock()






 



class MainFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Test')
        
        screen = QApplication.desktop().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        # 窗口尺寸
        window_width =  800
        window_height = 600
        # 计算窗口起始坐标
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)
    
        # 创建matplotlib图形和画布
        self.plot_layout = QVBoxLayout()
        self.plot_fig = plt.figure(facecolor='#F5F5F5')

        # 启用blitting以提高性能
        self.plot_fig.canvas.draw()
        self.plot_ax=self.plot_fig.add_subplot(111,facecolor='#F5F5F5')
        self.plot_ax.grid()
        self.canvas = FigureCanvas(self.plot_fig)
        self.plot_layout.addWidget(self.canvas)

        # 创建一个新的水平布局来放置按钮
        button_layout = QHBoxLayout()

        self.btn_start = QPushButton('Start', self)
        self.btn_start.setGeometry(50, 50, 100, 30)
        self.btn_start.clicked.connect(self.Plot_data)
        button_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton('Stop', self)
        self.btn_stop.setGeometry(150, 50, 100, 30)
        self.btn_stop.clicked.connect(self.stopThread)
        button_layout.addWidget(self.btn_stop)

        self.btn_pause = QPushButton('Pause', self)
        self.btn_pause.setGeometry(50, 100, 100, 30)
        self.btn_pause.clicked.connect(self.pauseThread)
        button_layout.addWidget(self.btn_pause)

        self.btn_resume = QPushButton('Resume', self)
        self.btn_resume.setGeometry(150, 100, 100, 30)
        self.btn_resume.clicked.connect(self.resumeThread)
        button_layout.addWidget(self.btn_resume)

        # 将按钮布局添加到主布局中
        self.plot_layout.addLayout(button_layout)
        self.setLayout(self.plot_layout)
        self.plot_worker = PlotThread()
        self.plot_worker.update_signal.connect(self.update_plot)

        # 初始化数据
        self.xdata=[]
        self.ydata=[]
        self.line,=self.plot_ax.plot([],[],lw=1,color='blue')

    
    def stopThread(self):
        """停止线程"""
        if self.plot_worker and self.plot_worker.isRunning():
            self.plot_worker.stop()
            self.xdata.clear()
            self.ydata.clear()
            self.line.set_data([],[])
            self.canvas.draw()

    def pauseThread(self):
        """暂停线程"""
        if self.plot_worker and self.plot_worker.isRunning():
            self.plot_worker.pause()

    def resumeThread(self): 
        """恢复线程"""
        if self.plot_worker and self.plot_worker.isRunning():
            self.plot_worker.resume()

    def Plot_data(self):
        """初始化matplotlib图形"""
        self.plot_ax.clear()
        self.plot_ax.grid()
        self.xdata.clear()
        self.ydata.clear()
        self.line,=self.plot_ax.plot([],[],lw=1,color='blue')
        # 设置初始显示范围
        self.plot_ax.set_ylim(-1.1, 1.1)
        self.plot_ax.set_xlim(0, 100)
        self.canvas.draw()

        if self.plot_worker:
            self.plot_worker.stop()
            self.plot_worker.wait()

        #print("Creating and starting PlotWorker...")  # Debug output
        self.plot_worker = PlotThread()  # 创建新的工作线程
        self.plot_worker.update_signal.connect(self.update_plot)
        self.plot_worker.start()


    def _adjust_plot_limits(self):
        """根据当前数据调整matplotlib图形的显示范围"""
        if len(self.xdata) > 100:
            self.plot_ax.set_xlim(self.xdata[-100],self.xdata[-1]) # 设置 x 轴显示范围为最后 100 个数据点
        ymin = min(self.ydata)
        ymax = max(self.ydata)
        padding = (ymax - ymin) * 0.1
        self.plot_ax.set_ylim(ymin - padding, ymax + padding) # 设置 y 轴显示范围
        
   
    def update_plot(self, data,xtime):
        """更新matplotlib图形"""
        self.xdata.append(xtime) # 更新x轴数据
        self.ydata.append(data) # 更新y轴数据
        self.line.set_data(self.xdata[-100:],self.ydata[-100:]) ## 自动调整坐标轴
        self._adjust_plot_limits() # 自动调整坐标轴
        self.canvas.draw() # 刷新画布






if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainFrame()
    ex.show()
    sys.exit(app.exec_())