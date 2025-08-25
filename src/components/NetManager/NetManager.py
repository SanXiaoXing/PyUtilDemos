#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Project ：631_ZHCLTest 
@File    ：NetManager.py
@Author  ：SanXiaoXing
@Date    ：2025/8/16
@Description: 网络设备管理器 - 读取 NetDevice.json 并直接扫描 IP 地址状态/名称/IP/MAC
"""
import os
import platform
import subprocess
import sys
import json
from datetime import datetime
from ipaddress import ip_address
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QHeaderView, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout, QMenu, QStyledItemDelegate, QStyleOptionViewItem

from Ui_NetManager import Ui_NetManager  # 包内导入

# 允许直接运行该文件时，添加项目根目录到 sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# 在选中行时仍然保持单元格自身的前景色（用于状态列）
class StatusColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        brush = index.data(Qt.ForegroundRole)
        if brush is not None:
            # 同时设置普通文本与选中文本颜色，避免被选中高亮覆盖
            opt.palette.setBrush(QPalette.Text, brush)
            opt.palette.setBrush(QPalette.HighlightedText, brush)
        super().paint(painter, opt, index)


class ScanWorker(QThread):
    progress = pyqtSignal(int, int)  # done, total
    finished_scan = pyqtSignal(dict)  # alive_map

    def __init__(self, ip_list, parent=None):
        super().__init__(parent)
        self.ip_list = list(ip_list)

    def run(self):
        total = len(self.ip_list)
        done = 0
        alive_map = {}
        
        def ping_ip(ip: str, timeout: int = 1) -> bool:
            try:
                system = platform.system().lower()
                if system == "windows":
                    cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
                else:
                    cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
                return result.returncode == 0
            except Exception:
                return False

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ip = {executor.submit(ping_ip, ip): ip for ip in self.ip_list}
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    online = future.result()
                    if online:
                        alive_map[ip] = ""
                except Exception:
                    pass
                finally:
                    done += 1
                    self.progress.emit(done, total)
        self.finished_scan.emit(alive_map)

# ------------------ 增加设备对话框 ------------------
class AddDeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("增加设备")
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        # 使用表单布局确保标签与输入框对齐
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        lbl_ip = QLabel("IP 地址:")
        self.edit_ip = QLineEdit()
        self.edit_ip.setPlaceholderText("例如 192.168.1.100")
        self.edit_ip.setInputMask("000.000.000.000;_")
        self.edit_ip.setClearButtonEnabled(True)
        form.addRow(lbl_ip, self.edit_ip)
        
        lbl_name = QLabel("设备名称:")
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("请输入设备名称")
        self.edit_name.setClearButtonEnabled(True)
        form.addRow(lbl_name, self.edit_name)
        
        layout.addLayout(form)
        
        # 底部按钮行靠右
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_cancel = QPushButton("取消")
        self.btn_ok = QPushButton("确定")
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.on_ok)
        self.edit_ip.setFocus()
    
    def on_ok(self):
        ip = self.edit_ip.text().strip()
        name = self.edit_name.text().strip()
        if not ip or not name:
            QMessageBox.warning(self, "提示", "IP 地址和设备名称均不能为空！")
            return
        # 使用标准库进行 IP 合法性校验
        try:
            ip_address(ip)
        except Exception:
            QMessageBox.warning(self, "提示", "请输入有效的 IPv4 地址！")
            return
        self.accept()

    def get_values(self):
        return self.edit_ip.text().strip(), self.edit_name.text().strip()

class NetManager(QWidget):
    def __init__(self, parent=None, json_path: str = None):
        super().__init__(parent)
        self.ui = Ui_NetManager()
        self.ui.setupUi(self)

        # 数据
        # self.json_path = json_path or os.path.join(CURRENT_DIR, 'NetDevice.json')             # 当前文件夹内文件
        self.json_path = json_path or os.path.join(CURRENT_DIR, 'NetDevice.json')         # 根目录文件
        self.device_map = {}  # ip -> name
        self.alive_map = {}   # ip -> mac (仅在线)
        self.last_scan_time = None
        self.scanning = False  # 防止重复扫描

        # 初始化表格
        header = self.ui.table_devices.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        # 让第0列（状态）在选中时也保持自身颜色
        self.ui.table_devices.setItemDelegateForColumn(0, StatusColorDelegate(self.ui.table_devices))
        
        # 设置右键菜单
        self.ui.table_devices.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.table_devices.customContextMenuRequested.connect(self.show_context_menu)

        # 信号
        self.ui.btn_refresh.clicked.connect(self.refresh)
        self.ui.btn_add_device.clicked.connect(self.open_add_device_dialog)
        self.ui.edit_filter.textChanged.connect(self.apply_filter)
        self.ui.combo_status_filter.currentIndexChanged.connect(self.apply_filter)

        # 启动：先显示空表，再后台加载JSON并扫描
        QTimer.singleShot(0, self._initialize)

    def _initialize(self):
        """初始化：加载配置并开始扫描"""
        # 显示进度条：阶段1 读取配置
        self.ui.label_progress.setText("正在读取配置...")
        self.ui.progress_bar.setVisible(True)
        self.ui.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 加载JSON配置
        self.load_json()
        
        # 开始扫描
        self.ui.progress_bar.setRange(0, 1)
        self.ui.progress_bar.setValue(0)
        self.start_scan()

    # ------------------ 数据加载 ------------------
    def load_json(self):
        """读取 NetDevice.json -> device_map"""
        self.device_map = {}
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for ip, name in data.items():
                    self.device_map[str(ip).strip()] = str(name).strip()
        except Exception as e:
            print(f"[NetManager] 加载JSON失败: {e}")
            self.device_map = {}

    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.ui.btn_refresh.setEnabled(False)
        # 扫描期间禁用增加设备，避免并发写 JSON
        self.ui.btn_add_device.setEnabled(False)

        ip_list = list(self.device_map.keys())
        # 初始化进度条
        self.ui.label_progress.setText("正在扫描设备...")
        self.ui.progress_bar.setVisible(True)
        self.ui.progress_bar.setRange(0, max(1, len(ip_list)))
        self.ui.progress_bar.setValue(0)

        # 启动工作线程
        self.worker = ScanWorker(ip_list, self)
        self.worker.progress.connect(self.on_scan_progress)
        self.worker.finished_scan.connect(self.on_scan_finished)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self):
        # 恢复按钮
        self.scanning = False
        self.ui.btn_refresh.setEnabled(True)
        self.ui.btn_add_device.setEnabled(True)

    def on_scan_progress(self, done: int, total: int):
        # 更新进度条
        self.ui.progress_bar.setRange(0, max(1, total))
        self.ui.progress_bar.setValue(done)
        self.ui.label_progress.setText(f"正在扫描设备... {done}/{total}")

    def on_scan_finished(self, alive_map: dict):
        # 隐藏进度条并刷新表格
        self.alive_map = alive_map
        self.last_scan_time = datetime.now()
        self.refresh_table()
        self.ui.progress_bar.setVisible(False)
        self.ui.label_progress.setText("")

    def refresh_table(self):
        """刷新表格显示"""
        rows = []
        # 构建设备信息行数据，包含在线状态、设备名称和IP地址
        for ip, name in self.device_map.items():
            online = ip in self.alive_map
            rows.append((online, name, ip))

        # 统计设备总数、在线数和离线数
        total = len(rows)
        online_count = sum(1 for r in rows if r[0])
        offline_count = total - online_count

        # 清空表格并重置排序状态，防止排序后刷新导致数据重复
        self.ui.table_devices.clearContents()
        self.ui.table_devices.setSortingEnabled(False)
        
        # 设置表格行数并填充数据
        self.ui.table_devices.setRowCount(len(rows))
        for row_idx, (online, name, ip) in enumerate(rows):
            # 设置状态列（在线/离线）及其样式
            status_text = '● 在线' if online else '● 离线'
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(0, 170, 0) if online else QColor(200, 0, 0))

            # 设置设备名称和IP地址列
            name_item = QTableWidgetItem(name)
            ip_item = QTableWidgetItem(ip)

            # 设置最后扫描时间列
            ts = self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else '—'
            time_item = QTableWidgetItem(ts)
            time_item.setTextAlignment(Qt.AlignCenter)

            # 将各项数据添加到表格对应位置
            self.ui.table_devices.setItem(row_idx, 0, status_item)
            self.ui.table_devices.setItem(row_idx, 1, name_item)
            self.ui.table_devices.setItem(row_idx, 2, ip_item)
            self.ui.table_devices.setItem(row_idx, 3, time_item)

        # 调整表格列宽以适应内容
        self.ui.table_devices.resizeColumnsToContents()
        
        # 重新启用排序功能
        self.ui.table_devices.setSortingEnabled(True)

        # 更新状态标签显示设备统计信息
        self.ui.label_status.setText(f"设备总数: {total} | 在线: {online_count} | 离线: {offline_count}")

        # 更新最后扫描时间标签
        last_scan_str = self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else '未执行'
        self.ui.label_last_scan.setText(f"最后扫描: {last_scan_str}")

        # 应用当前的过滤条件
        self.apply_filter()


    def apply_filter(self):
        keyword = self.ui.edit_filter.text().strip().lower()
        status_filter = self.ui.combo_status_filter.currentText()
        row_count = self.ui.table_devices.rowCount()

        for row in range(row_count):
            name = self.ui.table_devices.item(row, 1).text().lower() if self.ui.table_devices.item(row, 1) else ''
            ip = self.ui.table_devices.item(row, 2).text().lower() if self.ui.table_devices.item(row, 2) else ''
            status_text = self.ui.table_devices.item(row, 0).text() if self.ui.table_devices.item(row, 0) else ''

            visible = True
            if keyword:
                visible = (keyword in name) or (keyword in ip)
            if visible and status_filter != '全部':
                if status_filter == '在线' and ('在线' not in status_text):
                    visible = False
                elif status_filter == '离线' and ('离线' not in status_text):
                    visible = False

            self.ui.table_devices.setRowHidden(row, not visible)


    def refresh(self):
        # 重新扫描（异步），界面立即响应
        self.start_scan()

    def open_add_device_dialog(self):
        """打开增加设备对话框"""
        if self.scanning:
            QMessageBox.information(self, "提示", "正在扫描中，请稍后再添加设备。")
            return
        dlg = AddDeviceDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            ip, name = dlg.get_values()
            if self.add_or_update_device(ip, name):
                self._refresh_after_device_change()

    def _refresh_after_device_change(self):
        """设备变更后的刷新操作"""
        self.load_json()
        self.refresh_table()
        self.start_scan()

    def add_or_update_device(self, ip: str, name: str) -> bool:
        """添加或更新设备到JSON文件"""
        data = {}
        # 读取现有 JSON
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # 若文件不存在，确保上级目录存在
                os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取配置失败:\n{e}")
            return False
        # 冲突处理：若 IP 已存在，确认是否覆盖名称
        if ip in data and data[ip] != name:
            ret = QMessageBox.question(
                self,
                "确认",
                f"IP {ip} 已存在，是否将名称从 ‘{data[ip]}’ 覆盖为 ‘{name}’？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if ret != QMessageBox.Yes:
                return False
        data[ip] = name
        # 写回 JSON
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"写入配置失败:\n{e}")
            return False


    def show_context_menu(self, position):
        # 获取点击的行
        item = self.ui.table_devices.itemAt(position)
        if item is None:
            return
        
        row = item.row()
        if row < 0:
            return
            
        # 获取选中行的设备信息
        ip_item = self.ui.table_devices.item(row, 2)
        name_item = self.ui.table_devices.item(row, 1)
        if not ip_item or not name_item:
            return
            
        ip = ip_item.text()
        name = name_item.text()
        
        # 创建上下文菜单
        menu = QMenu(self)
        
        # 添加编辑动作
        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(lambda: self.edit_device(ip, name))
        
        # 添加删除动作
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.delete_device(ip, name))
        
        # 在鼠标位置显示菜单
        menu.exec_(self.ui.table_devices.mapToGlobal(position))
    
    def edit_device(self, ip: str, name: str):
        """编辑设备信息"""
        if self.scanning:
            QMessageBox.information(self, "提示", "正在扫描中，请稍后再编辑设备。")
            return
            
        dlg = AddDeviceDialog(self)
        dlg.setWindowTitle("编辑设备")
        # 预填充当前设备信息
        dlg.edit_ip.setText(ip)
        dlg.edit_name.setText(name)
        # 编辑时允许修改IP地址
        dlg.edit_ip.setReadOnly(False)
        
        if dlg.exec_() == QDialog.Accepted:
            new_ip, new_name = dlg.get_values()
            # 检查是否有变化
            if new_ip == ip and new_name == name:
                return  # 没有变化，直接返回
            
            # 如果IP地址发生变化，需要先删除旧记录
            if new_ip != ip:
                # 检查新IP是否已存在
                if new_ip in self.device_map and new_ip != ip:
                    ret = QMessageBox.question(
                        self,
                        "IP冲突",
                        f"IP地址 {new_ip} 已被设备 '{self.device_map[new_ip]}' 使用。\n是否要覆盖该设备？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if ret != QMessageBox.Yes:
                        return
                
                # 删除旧IP记录
                if self.remove_device(ip):
                    # 添加新IP记录
                    if self.add_or_update_device(new_ip, new_name):
                        self._refresh_after_device_change()
                        QMessageBox.information(self, "成功", f"设备已从 {ip} 更新为 {new_ip}")
            else:
                # 只是名称变化
                if self.add_or_update_device(new_ip, new_name):
                    self._refresh_after_device_change()
    
    def delete_device(self, ip: str, name: str):
        if self.scanning:
            QMessageBox.information(self, "提示", "正在扫描中，请稍后再删除设备。")
            return
            
        # 确认删除
        ret = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除设备 '{name}' ({ip}) 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if ret == QMessageBox.Yes:
            if self.remove_device(ip):
                self._refresh_after_device_change()
    
    def remove_device(self, ip: str) -> bool:
        """从JSON文件中删除设备"""
        try:
            data = {}
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            if ip in data:
                del data[ip]
                
                # 写回JSON
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            else:
                QMessageBox.warning(self, "警告", f"设备 {ip} 不存在于配置中。")
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除设备失败:\n{e}")
            return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = NetManager()
    w.show()
    sys.exit(app.exec_())