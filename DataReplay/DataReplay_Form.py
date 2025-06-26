import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from reuse_page.Ui_DataReplay_Form import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
import pandas as pd
from common.Comm_Function import CommFunciton as comm
from common.Comm_Function import Image_Def as image


class DataReplayForm(QWidget,Ui_DataReplay_Form):
    
    def __init__(self):
        super(DataReplayForm,self).__init__()
        self.setupUi(self)

        self.Load_qss()
        self.InitUI()
        



    def InitUI(self):
        self.setWindowTitle('数据回放')
        
        plt.rcParams['font.sans-serif'] = ['SimSun']  # 设置默认字体为宋体
        plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
        self.Replayfig = plt.figure()
        self.Replaycanvas=FigureCanvas(self.Replayfig)
        self.gridLayout_plot.addWidget(self.Replaycanvas)
        self.ax=None
        

        self.treeWidget_datafile.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeWidget_datafile.setContextMenuPolicy(Qt.CustomContextMenu)  # 打开右键菜单的策略
        self.treeWidget_datafile.customContextMenuRequested.connect(self.TreeContextMenuEvent)  # 绑定事件


        self.pushButton_selectfile.clicked.connect(self.selectfile)
        self.pushButton_plot.setIcon(QIcon(image.startIcon_path))
        self.pushButton_plot.setIconSize(QSize(30,30))
        self.pushButton_plot.setFixedSize(50, 50)
        self.pushButton_plot.clicked.connect(self.PlotData)


    def TreeContextMenuEvent(self,pos):
        ''' 设置右键菜单列表'''
        self.item = self.treeWidget_datafile.itemAt(pos)
        TreeMenu=QMenu(parent=self.treeWidget_datafile)
        #创建action
        CheckedAll=QAction('全选')
        UncheckedAll=QAction('取消全选')

         #绑定action与函数
        CheckedAll.triggered.connect(self.SelectedAll)
        UncheckedAll.triggered.connect(self.SelectedClear)

        #设置右键菜单列表的显示项
        TreeMenu.addActions([CheckedAll,UncheckedAll])
        TreeMenu.exec_(self.treeWidget_datafile.mapToGlobal(pos))  # 显示右键菜单


    def SelectedAll(self):
        '''全选treewidget'''
        iterator=QTreeWidgetItemIterator(self.treeWidget_datafile)
        while iterator.value():
            item=iterator.value()
            item.setCheckState(0,Qt.Checked)
            iterator +=1

  
    def SelectedClear(self):
        '''全不选treewidget'''
        iterator=QTreeWidgetItemIterator(self.treeWidget_datafile)
        while iterator.value():
            item=iterator.value()
            item.setCheckState(0,Qt.Unchecked)
            iterator +=1


    def selectfile(self):
        filePath=QFileDialog.getOpenFileName(self, "选择文件", "", "Text Files (*.csv)")[0]
        if filePath=='':
            return
        else:
            self.lineEdit_filepath.setText(filePath)
            self.AddTestDataToTree(filePath)
            

    
    def AddTestDataToTree(self,filePath):
        self.TestDict={}
        filename=os.path.basename(filePath)
        self.treeWidget_datafile.clear()
        Test_Data=pd.read_csv(filePath,index_col="time",parse_dates=True)
        columns=list(Test_Data)
        root=QTreeWidgetItem(self.treeWidget_datafile)
        root.setText(0,filename)
        root.setCheckState(0,Qt.Unchecked)
        # Define a custom role for storing the file path
        root.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsAutoTristate)
    
        for i in columns:
            child=QTreeWidgetItem(root)
            child.setText(0,i)
            child.setCheckState(0,Qt.Checked)
            child.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsAutoTristate)
        root.setExpanded(True)

        self.TestDict.update({filename:Test_Data})



    def AddDataToPlotList(self):
        self.PlotDataDF= pd.DataFrame()
        # Qt.MatchContains：模糊匹配
        # Qt.MatchRecursive：递归方式搜素
        items = self.treeWidget_datafile.findItems('', Qt.MatchContains|Qt.MatchRecursive, 0)
        for item in items:
            if item.parent() and not item.childCount() and item.checkState(0)==2: #底层项目中复选框被选中的item
                testname=item.parent().text(0)
                paraname=item.text(0)
                #add to dataframe
                oneS=self.TestDict[testname][paraname]
                self.PlotDataDF[paraname]=oneS



     #画图
    def PlotData(self):
        self.AddDataToPlotList()
        
        if not self.PlotDataDF.empty:
            if self.ax is None:
                self.ax = self.Replayfig.add_subplot(111) 
            else:
                self.ax.clear()
            self.PlotDataDF.plot(kind='line',grid=True,ax=self.ax)
            self.Replaycanvas.draw()
        


    



    def Load_qss(self):
        qssfile=comm.get_path('resources\qss\style.qss')
        with open(qssfile, 'r') as f:
            self.setStyleSheet(f.read())




if __name__ == "__main__":
    app =QtWidgets.QApplication(sys.argv)
    Tool = DataReplayForm()
    Tool.showMaximized()
    sys.exit(app.exec())