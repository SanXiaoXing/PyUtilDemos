import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QStackedWidget, QHBoxLayout, QWidget, QLabel,QListWidgetItem
from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 主界面示例")
        self.setGeometry(100, 100, 800, 600)

        # 创建主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 创建左侧侧边栏
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        self.sidebar.setIconSize(self.sidebar.iconSize())
        main_layout.addWidget(self.sidebar)

        # 创建右侧堆叠窗口
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 添加页面
        self.add_page("页面1", "page1.png", "这是页面1的内容")
        self.add_page("页面2", "page2.png", "这是页面2的内容")
        self.add_page("页面3", "page3.png", "这是页面3的内容")

        # 连接点击事件
        self.sidebar.currentRowChanged.connect(self.change_page)

    def add_page(self, name, icon_path, content):
        # 添加侧边栏项
        item = QListWidgetItem(QIcon(icon_path), name)
        self.sidebar.addItem(item)

        # 添加页面内容
        label = QLabel(content)
        self.stacked_widget.addWidget(label)

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())