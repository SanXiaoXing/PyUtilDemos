import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from DataReplay.Ui_DataReplay_Form import *
import pandas as pd
import pyqtgraph as pg



colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', '#FFA500', '#800080', '#00CED1']




class DataReplayForm(QWidget, Ui_DataReplay_Form):
    def __init__(self):
        super(DataReplayForm, self).__init__()
        self.setupUi(self)
        self.initUI()
        self.init_graph()
        self.init_connections()

    def initUI(self):
        self.setWindowTitle('数据回放')
        self.treeWidget_datafile.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeWidget_datafile.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget_datafile.customContextMenuRequested.connect(self.TreeContextMenuEvent)
        self.pushButton_selectfile.clicked.connect(self.load_csv)
        self.pushButton_plot.setFixedSize(50, 50)
        self.pushButton_plot.clicked.connect(self.draw_plot)


    def init_graph(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        self.gridLayout_plot.addWidget(self.plot_widget)



    def init_connections(self):
        self.horizontalSlider.valueChanged.connect(self.scroll_plot)
      

    def TreeContextMenuEvent(self, pos):
        self.item = self.treeWidget_datafile.itemAt(pos)
        TreeMenu = QMenu(parent=self.treeWidget_datafile)
        CheckedAll = QAction('全选')
        UncheckedAll = QAction('取消全选')
        CheckedAll.triggered.connect(self.SelectedAll)
        UncheckedAll.triggered.connect(self.SelectedClear)
        TreeMenu.addActions([CheckedAll, UncheckedAll])
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

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择CSV文件", "", "*.csv")
        if not path:
            return
        self.data = pd.read_csv(path)
        date_col = self.data.columns[0]
        self.data[date_col] = pd.to_datetime(self.data[date_col])
        self.data.set_index(date_col, inplace=True)
        self.treeWidget_datafile.clear()
        for col in self.data.columns:
            item = QTreeWidgetItem([col])
            item.setCheckState(0, Qt.Checked)
            self.treeWidget_datafile.addTopLevelItem(item)
        self.horizontalSlider.setMaximum(len(self.data))


    def draw_plot(self):
        self.selected_columns = [
            self.treeWidget_datafile.topLevelItem(i).text(0)
            for i in range(self.treeWidget_datafile.topLevelItemCount())
            if self.treeWidget_datafile.topLevelItem(i).checkState(0) == Qt.Checked
        ]

        self.plot_widget.clear()  # 清除旧曲线

        x = self.data.index.to_numpy()
        for i, colname in enumerate(self.selected_columns):
            color = colors[i % len(colors)]
            y = self.data[colname].to_numpy()
            self.plot_widget.plot(x, y, pen=pg.mkPen(color=color, width=1), name=colname)



        





    def scroll_plot(self, value):
        full_x = self.data.index
        if full_x.empty:
            return

        total_range = full_x[-1].timestamp() - full_x[0].timestamp()
        view_width = total_range * 0.1  # 可视区域为10%
        x_min = full_x[0].timestamp() + total_range * (value / 100.0)
        x_max = x_min + view_width
        vb = self.plot_widget.getViewBox()
        vb.setXRange(x_min, x_max, padding=0)




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Tool = DataReplayForm()
    Tool.showMaximized()
    sys.exit(app.exec())
