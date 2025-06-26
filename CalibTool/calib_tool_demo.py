"""
计量校准工具
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import json
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from Ui_CalibrationForm import *

 
CALIBCONF_PATH=str( Path(__file__).parent / 'calibconf.json')  # 插值表配置文件路径


class CalibrationForm(QWidget,Ui_CalibrationForm): 
    def __init__(self,cardinfo):
        super(CalibrationForm,self).__init__()
        self.setupUi(self)
        self.cardname=cardinfo['name']
        self.cardch=cardinfo['ch']
        self.init_ui()
        self.load_calibconf()
        self.load_cardinfo()
        

    def init_ui(self):
        self.setWindowTitle('校准工具')
        self.resize(800,500)
        self.tableWidget_cali.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) #QTableWidget设置整行选中
        self.tableWidget_cali.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        #self.tableWidget_cali.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tableWidget_cali.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget_cali.setContextMenuPolicy(Qt.CustomContextMenu)  # 打开右键菜单的策略
        self.tableWidget_cali.customContextMenuRequested.connect(self.table_contextmenu_event)  # 绑定事件
        self.pushButton_save.clicked.connect(self.save_calibconf)
        self.pushButton_clear.clicked.connect(self.delete_all)
        self.pushButton_ouput.clicked.connect(self.signal_output)
        self.comboBox_ch.currentIndexChanged.connect(self.load_calibdata)


    def load_calibconf(self):
        """加载插值表"""
        try:
            with open(CALIBCONF_PATH, 'r') as file:
                self.calibconf = json.load(file)
        except json.JSONDecodeError:
            self.calibconf = {} 
        if self.cardname not in self.calibconf:
            self.calibconf[self.cardname] = {}
            for i in range(0, self.cardch): 
                self.calibconf[self.cardname][str(i)] = {}
        with open(CALIBCONF_PATH, 'w') as file:
            json.dump(self.calibconf, file, indent=4)


    def load_cardinfo(self):
        """加载板卡信息"""
        self.comboBox_cardname.addItem(self.cardname)
        self.comboBox_ch.addItems([str(i) for i in range(0,self.cardch)])
        '''执行打开板卡获取板卡状态(略)'''
        self.label_cardstate.setText('已连接')
        self.comboBox_ch.setCurrentIndex(0)
        self.load_calibdata()

    
    def load_calibdata(self):
        """加载标定信息并显示在表格中"""
        currch = self.comboBox_ch.currentText()

        # 清空当前表格
        self.tableWidget_cali.setRowCount(0)

        # 获取当前通道的校准数据
        ch_data = self.calibconf.get(self.cardname, {}).get(currch, {})

        if not ch_data:
            print(f"通道 {currch} 的校准数据为空")
            return

        # 遍历并插入到表格（按标准值排序）
        for row, (standard_value, measured_value) in enumerate(sorted(ch_data.items(), key=lambda x: float(x[0]))):
            self.tableWidget_cali.insertRow(row)

            # 标准值（不可编辑）
            std_item = QTableWidgetItem(str(standard_value))
            std_item.setFlags(std_item.flags() & ~Qt.ItemIsEditable)  # 禁止编辑

            # 实测值（允许编辑）
            meas_item = QTableWidgetItem(str(measured_value))

            # 插入到表格
            self.tableWidget_cali.setItem(row, 0, std_item)
            self.tableWidget_cali.setItem(row, 1, meas_item)
   
                    

    def table_contextmenu_event(self,pos):
        """设置右键菜单列表"""
        item = self.tableWidget_cali.itemAt(pos)
        TreeMenu=QMenu(parent=self.tableWidget_cali)
        #创建action
        DeleteRow=QAction('删除')
        #绑定action与函数
        DeleteRow.triggered.connect(self.delete_row)
        #设置右键菜单列表的显示项
        TreeMenu.addActions([DeleteRow])
        TreeMenu.exec_(self.tableWidget_cali.mapToGlobal(pos))  # 显示右键菜单


    def delete_all(self):
        """清空表格数据"""
        self.tableWidget_cali.setRowCount(0)


    def delete_row(self):
        """删除表格行"""
        selected_indexes = self.tableWidget_cali.selectedIndexes()
        if not selected_indexes:
            return
        selected_rows = sorted(set(index.row() for index in selected_indexes), reverse=True)
        for row in selected_rows:
            self.tableWidget_cali.removeRow(row)


    def signal_output(self):
        """信号激励（输出or采集）"""
        val=self.doubleSpinBox_val.value()
        ch=int(self.comboBox_ch.currentText())

        '''执行信号激励（输出or采集）(略)'''
        print(f'通道{ch}激励信号为{val}')

        # 获取标准值列的所有值
        standvals = self.get_column_values()
        if not standvals:
            # 如果表格为空，直接插入第0行
            row_count = 0
            self.tableWidget_cali.insertRow(row_count)
            item = QTableWidgetItem(str(val))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget_cali.setItem(row_count, 0, item)
            return
    
        # 将 standvals 转换为 float 并排序
        sorted_vals = np.sort(np.array(standvals, dtype=float))
        index = np.searchsorted(sorted_vals, val)
        if val not in map(float, standvals):
            # 插入新行
            row_count = index
            self.tableWidget_cali.insertRow(row_count)
            item = QTableWidgetItem(str(val))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget_cali.setItem(row_count, 0, item)
            # 选中新插入的行
            self.tableWidget_cali.selectRow(row_count)
        else:
            # 选中已存在的那一行
            for row in range(self.tableWidget_cali.rowCount()):
                item = self.tableWidget_cali.item(row, 0)
                if item and float(item.text()) == float(val):
                    self.tableWidget_cali.selectRow(row)
                    break
    

    def get_column_values(self):
        """获取当前表格所有的标准值"""
        standvals = []
        for row in range(self.tableWidget_cali.rowCount()):
            item = self.tableWidget_cali.item(row, 0)
            standvals.append(item.text())
            
        return standvals
    

    def save_calibconf(self):
        """保存插值表配置到文件"""
        ch = str(self.comboBox_ch.currentText())  # 当前通道号转为字符串 key
        # 初始化目标字典结构
        if self.cardname not in self.calibconf:
            self.calibconf[self.cardname] = {}
        self.calibconf[self.cardname][ch] = {}

        for row in range(self.tableWidget_cali.rowCount()):
            standard_item = self.tableWidget_cali.item(row, 0)  # 标准值列
            measured_item = self.tableWidget_cali.item(row, 1)   # 实测值列

            if standard_item and measured_item:
                standard_value = standard_item.text()
                measured_value = measured_item.text()

                # 存入字典
                self.calibconf[self.cardname][ch][standard_value] = measured_value
                
        with open(CALIBCONF_PATH, 'w') as file:
            json.dump(self.calibconf, file, indent=4)


    def closeEvent(self, event):
        """关闭提示"""
        reply = QMessageBox.question(
            self,
            '关闭窗口',
            "是否保存校准数据?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            self.save_calibconf()  
            event.accept()  
        elif reply == QMessageBox.No:
            event.accept()  
        else:
            event.ignore()  
 

if __name__ == '__main__':
    cardinfo={
        "card_1":{
            "name":"card_1",
            "type":"模拟量",
            "ch":2,
            "mfr":"厂商_1",
            "desc":"描述_1"
        },
        "card_2":{
            "name":"card_2",
            "type":"模拟量",
            "ch":4,
            "mfr":"厂商_2",
            "desc":"描述_2"
        }
    }

    app = QApplication(sys.argv)
    tool = CalibrationForm(cardinfo['card_1'])
    tool.show()
    sys.exit(app.exec_())