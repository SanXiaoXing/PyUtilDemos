#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：py-util-demos
@File    ：bulb_statemonitor_demo.py
@Author  ：SanXiaoXing
@Date    ：2025/7/12
@Description: 灯泡状态监控工具,本工具用于实时监控设备状态，通过彩色灯泡显示不同的设备状态。

数据输入接口说明：
===================

1. 界面输入方式：
   - 在界面的"数据报文"输入框中输入十六进制数据
   - 支持格式："ffff"、"ff 00"、"FF00" 等
   - 点击"发送数据"按钮或按回车键发送

2. 编程接口调用：
   ```python
   # 创建监控实例
   monitor = BulbStateMonitor()

   # 发送数据包
   monitor.send_data_packet("ffff")  # 发送两个字节
   monitor.send_data_packet("ff00")  # 发送 0xFF 和 0x00
   ```

3. 数据处理流程：
   - 输入的十六进制字符串会被转换为字节数组
   - 每个字节按位置（0, 1, 2...）分发给对应的设备组
   - 根据配置文件中的比特位设置更新设备状态

真实数据源接入说明：
===================

4. 需要接入真实数据源时，请按以下步骤操作：

5. 在 BulbStateMonitor 类中实现以下方法：
   - setup_real_data_source(): 配置真实数据源连接
   - start_real_data_source(): 启动数据接收
   - stop_real_data_source(): 停止数据接收

6. 数据接收后，调用 process_data(byte_pos, data) 方法处理数据
   - byte_pos: 字节位置 (int)
   - data: 字节数据 (bytes)

7. 支持的数据源类型：
   - 串口通信 (Serial)
   - 网络通信 (TCP/UDP)
   - 文件数据源
   - 其他自定义数据源
"""
import sys
import os
import re
from pathlib import Path
from typing import Dict
from functools import lru_cache

from PyQt5.QtSvg import QSvgWidget

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas未安装，将使用CSV格式配置文件")
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QGroupBox, QMessageBox, QLineEdit, QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon

# 预编译正则表达式用于十六进制验证
HEX_PATTERN = re.compile(r'^[0-9a-fA-F]*$')


class BulbWidget(QLabel):
    """
    灯泡控件类
    支持5种状态：正常运行(绿色)、错误状态(红色)、警告状态(黄色)、停止/离线(灰色)、未知状态(蓝色)
    """
    
    # 状态常量
    STATE_NORMAL = 0    # 正常运行 - 绿色
    STATE_ERROR = 1     # 错误状态 - 红色
    STATE_WARNING = 2   # 警告状态 - 黄色
    STATE_OFFLINE = 3   # 停止/离线 - 灰色
    STATE_FAULT = 4     # 故障状态 - 蓝色
    STATE_UNKNOWN = 5   # 未知状态 - 橙色
    
    # 状态颜色映射
    STATE_COLORS = {
        STATE_NORMAL: QColor(0, 255, 0),      # 绿色
        STATE_ERROR: QColor(255, 0, 0),       # 红色
        STATE_WARNING: QColor(255, 255, 0),   # 黄色
        STATE_OFFLINE: QColor(128, 128, 128), # 灰色
        STATE_FAULT: QColor(0, 0, 255),       # 蓝色
        STATE_UNKNOWN: QColor(255, 165, 0)    # 橙色
    }
    
    # 状态名称映射
    STATE_NAMES = {
        STATE_NORMAL: "正常运行",
        STATE_ERROR: "错误状态",
        STATE_WARNING: "警告状态",
        STATE_OFFLINE: "停止/离线",
        STATE_FAULT: "正常状态",
        STATE_UNKNOWN: "未知状态"
    }
    
    # 类级别的pixmap缓存，所有实例共享
    _pixmap_cache = {}
    
    # 信号定义
    stateChanged = pyqtSignal(int, int)  # 状态改变信号 (设备ID, 新状态)
    
    def __init__(self, device_id: int, device_name: str, initial_state: int = STATE_OFFLINE):
        super().__init__()
        self.device_id = device_id
        self.device_name = device_name
        self.current_state = initial_state
        self.bit_pos = 0
        self.has_fault = False  # 故障标记
        
        self.setFixedSize(24, 24)
        self.setScaledContents(True)
        self.setToolTip(f"{device_name} - {self.STATE_NAMES[initial_state]}")
        
        self.update_display()
    
    def set_position_info(self, bit_pos: int):
        """设置位置信息"""
        self.bit_pos = bit_pos
    
    def update_display(self):
        """更新显示"""
        # 检查缓存中是否已有该状态的pixmap
        if self.current_state not in self._pixmap_cache:
            # 创建彩色的圆形图标
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 设置颜色
            color = self.STATE_COLORS[self.current_state]
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            
            # 绘制圆形
            painter.drawEllipse(2, 2, 20, 20)
            painter.end()
            
            # 缓存pixmap
            self._pixmap_cache[self.current_state] = pixmap
        
        # 使用缓存的pixmap
        self.setPixmap(self._pixmap_cache[self.current_state])
        self.setToolTip(f"{self.device_name} - {self.STATE_NAMES[self.current_state]}")
    
    def set_state(self, state: int):
        """设置状态"""
        if state != self.current_state and state in self.STATE_COLORS:
            old_state = self.current_state
            self.current_state = state
            self.update_display()
            self.stateChanged.emit(self.device_id, state)
            
            # # 记录状态变化日志
            # print(f"设备 {self.device_name} 状态从 {self.STATE_NAMES[old_state]} 变更为 {self.STATE_NAMES[state]}")
    
    def get_state(self) -> int:
        """获取当前状态"""
        return self.current_state



class BulbStateMonitor(QWidget):
    """灯泡状态监控主窗口"""
    
    def __init__(self):
        super().__init__()
        self.devices = {}  # 设备字典 {device_id: BulbWidget}
        self.device_configs = {}  # 设备配置 {device_id: config_dict}
        self.byte_groups = {}  # 字节分组 {byte_pos: [device_ids]}
        self._config_cache = None  # 配置文件缓存
        self._config_mtime = None  # 配置文件修改时间
        
        # 性能统计
        self._cache_hits = 0
        self._cache_misses = 0
        self._state_updates = 0
        self._skipped_updates = 0
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("灯泡状态监控工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        window = QWidget()
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("设备状态监控")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c7dff;
                margin: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        # 设置应用图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "assets", "icon", "灯泡主意创新.svg")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置图标失败: {e}")
        
        # 滚动区域用于显示设备
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        
        main_layout.addWidget(self.scroll_area)
        
        # 数据输入区域
        input_layout = QHBoxLayout()
        
        input_label = QLabel("数据报文:")
        input_layout.addWidget(input_label)
        
        self.data_input = QLineEdit()
        self.data_input.setPlaceholderText("输入十六进制数据，如: ffff 或 ff00")
        self.data_input.returnPressed.connect(self.process_input_data)
        input_layout.addWidget(self.data_input)
        
        self.send_btn = QPushButton("发送数据")
        self.send_btn.clicked.connect(self.process_input_data)
        input_layout.addWidget(self.send_btn)
        
        main_layout.addLayout(input_layout)
        
        self.setLayout(main_layout)
    
    def load_config(self):
        """加载配置文件（带缓存机制）"""
        try:
            # 创建示例配置文件
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf.xlsx")
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf.csv")
            
            if not os.path.exists(config_path) and not os.path.exists(csv_path):
                raise FileNotFoundError("未找到配置文件")
            
            # 确定使用的配置文件路径
            active_config_path = config_path if (PANDAS_AVAILABLE and os.path.exists(config_path)) else csv_path
            
            # 检查文件修改时间，如果未变化则使用缓存
            current_mtime = os.path.getmtime(active_config_path)
            if self._config_cache is not None and self._config_mtime == current_mtime:
                df = self._config_cache
                self._cache_hits += 1
                print(f"配置缓存命中 (命中次数: {self._cache_hits})")
            else:
                self._cache_misses += 1
                # 读取配置文件
                if PANDAS_AVAILABLE and os.path.exists(config_path):
                    try:
                        df = pd.read_excel(config_path, engine='openpyxl')
                    except Exception:
                        # 如果openpyxl不可用，尝试其他引擎
                        try:
                            df = pd.read_excel(config_path, engine='xlrd')
                        except Exception:
                            df = pd.read_excel(config_path)
                elif os.path.exists(csv_path):
                    if PANDAS_AVAILABLE:
                        df = pd.read_csv(csv_path)
                    else:
                        # 手动解析CSV
                        import csv
                        data = []
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                data.append(row)
                        # 创建简单的DataFrame替代
                        class SimpleDataFrame:
                            def __init__(self, data):
                                self.data = data
                            def iterrows(self):
                                for i, row in enumerate(self.data):
                                    yield i, row
                        df = SimpleDataFrame(data)
                else:
                    raise FileNotFoundError("配置文件不存在")
                
                # 缓存配置数据和修改时间
                self._config_cache = df
                self._config_mtime = current_mtime
            
            # 清空现有设备
            self.clear_devices()
            
            # 按字节分组
            self.byte_groups = {}
            device_id = 0
            
            for _, row in df.iterrows():
                # 兼容不同的列名格式
                if 'BYTE' in df.columns:
                    # 英文列名格式
                    # 处理ActiveState和InactiveState的文本值
                    active_state_text = str(row['ActiveState'])
                    inactive_state_text = str(row['InactiveState'])
                    
                    # 检测故障关键词
                    fault_keywords = ['故障', '错误', 'fault', 'error', 'fail']
                    has_fault = any(keyword in active_state_text.lower() or keyword in inactive_state_text.lower() 
                                   for keyword in fault_keywords)
                    
                    active_state = 1 if active_state_text == '有效' else 0
                    inactive_state = 0 if inactive_state_text == '无效' else 1
                    
                    config = {
                        '字节位数': int(row['BYTE']),
                        '比特位数': int(row['BITE']),
                        '设备名称': str(row['SignalName']),
                        '活跃状态': active_state,
                        '失效状态': inactive_state,
                        '初始值': int(row['INIT']),
                        '有故障': has_fault
                    }
                else:
                    # 中文列名格式
                    active_state_text = str(row.get('活跃状态文本', ''))
                    inactive_state_text = str(row.get('失效状态文本', ''))
                    
                    # 检测故障关键词
                    fault_keywords = ['故障', '错误', 'fault', 'error', 'fail']
                    has_fault = any(keyword in active_state_text.lower() or keyword in inactive_state_text.lower() 
                                   for keyword in fault_keywords)
                    
                    config = {
                        '字节位数': int(row['字节位数']),
                        '比特位数': int(row['比特位数']),
                        '设备名称': str(row['设备名称']),
                        '活跃状态': int(row['活跃状态']),
                        '失效状态': int(row['失效状态']),
                        '初始值': int(row['初始值']),
                        '有故障': has_fault
                    }
                
                # 创建设备控件 - 根据INIT值确定初始状态
                init_value = config['初始值']
                active_value = config['活跃状态']
                inactive_value = config['失效状态']
                has_fault = config['有故障']
                
                if has_fault:
                    # 如果包含故障关键词，使用红灯表示错误状态
                    initial_state = BulbWidget.STATE_ERROR
                elif init_value == active_value:
                    # INIT值等于活跃状态值，显示绿灯
                    initial_state = BulbWidget.STATE_NORMAL
                elif init_value == inactive_value:
                    # INIT值等于失效状态值，显示灰灯
                    initial_state = BulbWidget.STATE_OFFLINE
                else:
                    # INIT值既不等于活跃也不等于失效，显示橙灯
                    initial_state = BulbWidget.STATE_UNKNOWN
                
                bulb = BulbWidget(device_id, config['设备名称'], initial_state)
                bulb.set_position_info(config['比特位数'])
                bulb.has_fault = has_fault  # 添加故障标记
                
                self.devices[device_id] = bulb
                self.device_configs[device_id] = config
                
                # 按字节分组
                byte_pos = config['字节位数']
                if byte_pos not in self.byte_groups:
                    self.byte_groups[byte_pos] = []
                self.byte_groups[byte_pos].append(device_id)
                
                device_id += 1
            
            self.create_device_layout()
            print(f"成功加载 {len(self.devices)} 个设备配置")
            
        except Exception as e:
            # raise(f"加载配置文件失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置文件失败:\n{e}")

    def create_device_layout(self):
        """创建设备布局"""
        # 清空现有布局
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)
        
        # 按字节分组显示
        for byte_pos in sorted(self.byte_groups.keys()):
            group_box = QGroupBox(f"字节 {byte_pos}")
            group_layout = QGridLayout()
            
            device_ids = self.byte_groups[byte_pos]
            row, col = 0, 0
            max_cols = 4  # 每行最多4个设备
            
            for device_id in device_ids:
                if device_id in self.devices:
                    bulb = self.devices[device_id]
                    
                    # 创建设备容器
                    device_frame = QFrame()
                    device_frame.setFrameStyle(QFrame.Box)
                    device_layout = QHBoxLayout(device_frame)
                    device_layout.setContentsMargins(5, 5, 5, 5)
                    
                    # 添加灯泡和名称
                    device_layout.addWidget(bulb)
                    
                    name_label = QLabel(bulb.device_name)
                    name_label.setStyleSheet("""
                        QLabel {
                            font-size: 12px;
                            font-family: 'Microsoft YaHei';
                            margin-left: 5px;
                        }
                    """)
                    device_layout.addWidget(name_label)
                    device_layout.addStretch()
                    
                    group_layout.addWidget(device_frame, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
            
            group_box.setLayout(group_layout)
            self.scroll_layout.addWidget(group_box)
        
        self.scroll_layout.addStretch()
    
    def clear_devices(self):
        """清空设备"""
        self.devices.clear()
        self.device_configs.clear()
        self.byte_groups.clear()
    
    def process_data(self, byte_pos: int, data: bytes):
        """处理接收到的数据（优化版本）"""
        if byte_pos not in self.byte_groups:
            return

        # 安全获取字节值
        byte_value = data[0] if data and len(data) > 0 else 0

        # 批量更新该字节对应的所有设备状态
        state_updates = []  # 收集状态更新
        
        for device_id in self.byte_groups[byte_pos]:
            if device_id not in self.devices:
                continue

            bulb = self.devices[device_id]

            # 获取当前 bit 的值
            bit_value = (byte_value >> bulb.bit_pos) & 1

            # 根据设备状态和 bit 值确定灯光状态
            new_state = self._determine_bulb_state(bulb, bit_value)
            
            # 只有状态真正改变时才更新
            if new_state != bulb.current_state:
                state_updates.append((bulb, new_state))
                self._state_updates += 1
            else:
                self._skipped_updates += 1
        
        # 批量执行状态更新
        for bulb, new_state in state_updates:
            bulb.set_state(new_state)


    @lru_cache(maxsize=128)
    def _determine_bulb_state_cached(self, has_fault: bool, bit_value: int) -> int:
        """根据设备状态和 bit 值决定灯光状态（缓存版本）"""
        if has_fault:
            if bit_value == 1:
                return BulbWidget.STATE_FAULT
            elif bit_value == 0:
                return BulbWidget.STATE_ERROR
        else:
            if bit_value == 1:
                return BulbWidget.STATE_NORMAL
            elif bit_value == 0:
                return BulbWidget.STATE_OFFLINE
        return BulbWidget.STATE_UNKNOWN
    
    def _determine_bulb_state(self, bulb, bit_value: int) -> int:
        """根据设备状态和 bit 值决定灯光状态"""
        has_fault = getattr(bulb, 'has_fault', False)
        return self._determine_bulb_state_cached(has_fault, bit_value)

    
    def process_input_data(self):
        """处理用户输入的数据报文"""
        try:
            # 获取输入的十六进制字符串
            hex_string = self.data_input.text().strip().replace(' ', '')
            
            if not hex_string:
                QMessageBox.warning(self, "警告", "请输入数据报文")
                return
            
            # 验证是否为有效的十六进制字符串（使用预编译正则表达式）
            if not HEX_PATTERN.match(hex_string):
                QMessageBox.warning(self, "警告", "请输入有效的十六进制数据")
                return
            
            # 确保字符串长度为偶数（每两个字符代表一个字节）
            if len(hex_string) % 2 != 0:
                hex_string = '0' + hex_string
            
            # 转换为字节数据
            byte_data = bytes.fromhex(hex_string)
            
            print(f"接收到数据报文: {hex_string.upper()}")
            print(f"字节数据: {[hex(b) for b in byte_data]}")
            
            # 按字节位置分发数据
            for byte_pos, byte_value in enumerate(byte_data):
                if byte_pos in self.byte_groups:
                    # 调用数据处理方法
                    self.process_data(byte_pos, bytes([byte_value]))
                    print(f"处理字节位置 {byte_pos}: 0x{byte_value:02X}")
            
            # 清空输入框
            self.data_input.clear()
            
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"数据格式错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理数据时发生错误: {e}")
    
    def send_data_packet(self, hex_data: str):
        """发送数据包的公共接口
        外部调用接口，用于发送十六进制数据包
        
        参数:
            hex_data (str): 十六进制字符串，如 "ffff" 或 "ff 00"
        
        示例:
            monitor.send_data_packet("ffff")  # 发送两个字节的数据
            monitor.send_data_packet("ff00")  # 发送 0xFF 和 0x00
        """
        try:
            # 清理输入字符串
            hex_string = hex_data.strip().replace(' ', '')
            
            # 验证十六进制格式（使用预编译正则表达式）
            if not HEX_PATTERN.match(hex_string):
                raise ValueError("无效的十六进制数据")
            
            # 确保偶数长度
            if len(hex_string) % 2 != 0:
                hex_string = '0' + hex_string
            
            # 转换为字节并处理
            byte_data = bytes.fromhex(hex_string)
            
            print(f"API调用 - 接收数据: {hex_string.upper()}")
            
            # 分发到各字节位置
            for byte_pos, byte_value in enumerate(byte_data):
                if byte_pos in self.byte_groups:
                    self.process_data(byte_pos, bytes([byte_value]))
                    
            return True
            
        except Exception as e:
            print(f"发送数据包失败: {e}")
            return False

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("灯泡状态监控工具")
    
    window = BulbStateMonitor()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()