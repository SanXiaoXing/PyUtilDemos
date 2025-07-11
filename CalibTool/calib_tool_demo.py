'''
校准工具

Author: JIN && <jjyrealdeal@163.com>
Date: 2025-05-14 11:28:51
Copyright (c) 2025 by JIN, All Rights Reserved. 
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import json
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from CalibTool.Ui_CalibrationForm import *

 
CALIBCONF_PATH=str( Path(__file__).parent / 'calibconf.json')  # 插值表配置文件路径

cardinfo={
        "name":"card_1",
        "type":"模拟量",
        "ch":2,
        "mfr":"厂商_1",
        "desc":"描述_1"
    }

class CalibrationForm(QWidget,Ui_CalibrationForm): 
    def __init__(self):
        """
        :cardinfo: 待校准的板卡信息dict
        """
        super(CalibrationForm,self).__init__()
        self.setupUi(self)
        self.cardname=cardinfo['name']
        self.cardch=cardinfo['ch']
        self.init_ui()
        self.load_calibconf()
        self.load_cardinfo()
        


    def init_ui(self) -> None:
        """初始化界面"""
        self.setWindowTitle('校准工具')
        self.resize(800,500)
        self.label_info.setText('')
        self.tableWidget_cali.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) #QTableWidget设置整行选中
        self.tableWidget_cali.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        #self.tableWidget_cali.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tableWidget_cali.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableWidget_cali.setContextMenuPolicy(Qt.CustomContextMenu)  # 打开右键菜单的策略
        self.tableWidget_cali.customContextMenuRequested.connect(self.table_contextmenu_event)  # 绑定事件
        self.tableWidget_cali.setItemDelegateForColumn(1, NumericDelegate(self))
        self.pushButton_save.clicked.connect(self.save_calibconf)
        self.pushButton_clear.clicked.connect(self.delete_all)
        self.pushButton_ouput.clicked.connect(self.signal_output)
        self.comboBox_ch.currentIndexChanged.connect(self.load_calibdata)



    def load_calibconf(self) -> None:
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



    def load_cardinfo(self) -> None:
        """加载板卡信息"""
        self.comboBox_cardname.addItem(self.cardname)
        self.comboBox_ch.addItems([str(i) for i in range(0,self.cardch)])
        '''执行打开板卡获取板卡状态(略)'''
        self.label_cardstate.setText('已连接')
        self.comboBox_ch.setCurrentIndex(0)
        self.load_calibdata()


    
    def load_calibdata(self) -> None:
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
   


    def table_contextmenu_event(self,pos) -> None:
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



    def delete_all(self) -> None:
        """清空表格数据"""
        reply = QMessageBox.question(
            self,
            '确认',
            "确定要清空所有数据吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.tableWidget_cali.setRowCount(0)
            self.label_info.setText('')
        else:
            return



    def delete_row(self) -> None:
        """删除表格行"""
        self.label_info.setText('')
        selected_indexes = self.tableWidget_cali.selectedIndexes()
        if not selected_indexes:
            return
        selected_rows = sorted(set(index.row() for index in selected_indexes), reverse=True)
        for row in selected_rows:
            self.tableWidget_cali.removeRow(row)
        


    def signal_output(self) -> None:
        """信号激励（输出or采集）"""
        self.label_info.setText('')

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
    


    def get_column_values(self) -> list:
        """获取当前表格所有的标准值"""
        standvals = []
        for row in range(self.tableWidget_cali.rowCount()):
            item = self.tableWidget_cali.item(row, 0)
            standvals.append(item.text())
            
        return standvals
    


    def save_calibconf(self) -> bool:
        """保存插值表配置到文件，返回是否成功"""
        try:
            ch = str(self.comboBox_ch.currentText())
            
            if self.has_empty_measured_values():
                QMessageBox.warning(self, "警告", "检测到有未填写的实测值，请填写后再保存。")
                return False  # 停止保存，通知外部不要关闭

            # 初始化结构
            if self.cardname not in self.calibconf:
                self.calibconf[self.cardname] = {}
            self.calibconf[self.cardname][ch] = {}

            for row in range(self.tableWidget_cali.rowCount()):
                standard_item = self.tableWidget_cali.item(row, 0)
                measured_item = self.tableWidget_cali.item(row, 1)

                if standard_item and measured_item:
                    standard_value = standard_item.text()
                    measured_value = measured_item.text()
                    self.calibconf[self.cardname][ch][standard_value] = measured_value

            with open(CALIBCONF_PATH, 'w') as file:
                json.dump(self.calibconf, file, indent=4)

            self.label_info.setText('保存成功！')
            return True  # 成功保存

        except Exception as e:
            print(str(e))
            return False



    def has_config_changed(self) -> bool:
        """检查当前配置是否与原始配置不同"""
        return self.calibconf != self.original_calibconf
    


    def has_empty_measured_values(self) -> bool:
        """检查表格中实测值列（第2列）是否存在空值"""
        for row in range(self.tableWidget_cali.rowCount()):
            measured_item = self.tableWidget_cali.item(row, 1)
            if not measured_item or not measured_item.text().strip():
                return True  # 存在空值
        return False  # 没有空值



    def closeEvent(self, event):
        """关闭提示"""
        # 第一步：检查实测值列是否存在空值
        if self.has_empty_measured_values():
            # 提示用户还有未完成的编辑
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("检测到有未填写的实测值，\n直接退出将导致未保存的数据丢失。")
            btn_continue = msg_box.addButton("Edit", QMessageBox.YesRole)
            btn_exit = msg_box.addButton("Quit", QMessageBox.NoRole)
            msg_box.setDefaultButton(btn_continue)

            msg_box.exec_()

            if msg_box.clickedButton() == btn_continue:
                # 用户选择继续编辑，阻止关闭
                event.ignore()
                return
            elif msg_box.clickedButton() == btn_exit:
                # 用户选择直接退出，执行关闭
                event.accept()
                return

        # 第二步：没有空值，询问是否保存配置
        reply = QMessageBox.question(
            self,
            '关闭窗口',
            "是否保存校准数据?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            if self.save_calibconf():  # 只有保存成功才允许关闭
                event.accept()
            else:
                event.ignore()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()



class NumericDelegate(QStyledItemDelegate):
    """限制表格输入为数字或小数"""
    def createEditor(self, parent, option, index):
        editor = super(NumericDelegate, self).createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            reg_ex = QRegularExpression(r"^[0-9]+(\.[0-9]+)?$")  # 只允许数字和可选的小数点
            validator = QRegularExpressionValidator(reg_ex, editor)
            editor.setValidator(validator)
        return editor
 



if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = CalibrationForm()
    tool.show()
    sys.exit(app.exec_())