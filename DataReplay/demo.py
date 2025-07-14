import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTreeWidget, QVBoxLayout, QTreeWidgetItem, 
    QPushButton, QFileDialog, QHBoxLayout, QSlider, QLabel, QAbstractItemView
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class CSVPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV数据回放（PyQtGraph）")

        self.data = None
        self.selected_columns = []
        self.plot_mode = "single"  # "single" or "multi"

        # 左侧TreeWidget + 按钮
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["字段"])
        self.tree.setSelectionMode(QAbstractItemView.MultiSelection)

        self.load_btn = QPushButton("加载CSV")
        self.plot_btn = QPushButton("绘图")

        # Plot区域
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_items = []  # 存储多个plotItem

        # 滑动条
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.scroll_plot)

        # 布局
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.load_btn)
        left_layout.addWidget(self.plot_btn)
        left_layout.addWidget(self.tree)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.plot_widget)
        right_layout.addWidget(self.slider)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 4)
        self.setLayout(main_layout)

        # 信号绑定
        self.load_btn.clicked.connect(self.load_csv)
        self.plot_btn.clicked.connect(self.draw_plot)


        
    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择CSV文件", "", "*.csv")
        if not path:
            return
         # Read CSV and automatically parse the first column as datetime
        self.data = pd.read_csv(path)
        
        # Convert the first column to datetime and set as index
        date_col = self.data.columns[0]
        self.data[date_col] = pd.to_datetime(self.data[date_col])
        self.data.set_index(date_col, inplace=True)

        self.tree.clear()
        for col in self.data.columns:
            item = QTreeWidgetItem([col])
            item.setCheckState(0, Qt.Checked)
            self.tree.addTopLevelItem(item)
        self.slider.setMaximum(len(self.data))



    def draw_plot(self):
        self.selected_columns = [
            self.tree.topLevelItem(i).text(0)
            for i in range(self.tree.topLevelItemCount())
            if self.tree.topLevelItem(i).checkState(0) == Qt.Checked
        ]

        self.plot_widget.clear()
        self.plot_items.clear()

        if self.plot_mode == "single":
            p = self.plot_widget.addPlot()
            for col in self.selected_columns:
                p.plot(self.data.index.to_numpy(), self.data[col].to_numpy(), pen=pg.mkPen(width=1), name=col)
            self.plot_items.append(p)
        else:
            for col in self.selected_columns:
                p = self.plot_widget.addPlot(row=len(self.plot_items), col=0)
                p.plot(self.data.index.to_numpy(), self.data[col].to_numpy(), pen=pg.mkPen(width=1), name=col)
                self.plot_items.append(p)

    def scroll_plot(self, val):
        """滑动时控制图像左右移动"""
        for p in self.plot_items:
            x_range = p.viewRange()[0]
            width = x_range[1] - x_range[0]
            new_x_min = self.data.index[val]
            new_x_max = new_x_min + pd.Timedelta(seconds=width)
            p.setXRange(new_x_min.timestamp(), new_x_max.timestamp(), padding=0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CSVPlotter()
    w.showMaximized()
    sys.exit(app.exec())
