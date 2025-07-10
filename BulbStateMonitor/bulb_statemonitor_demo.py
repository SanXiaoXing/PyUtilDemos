
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas未安装，将使用CSV格式配置文件")
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QGroupBox, QMenu, QAction, QMessageBox, QDialog, QFormLayout, 
    QLineEdit, QComboBox, QPushButton, QDialogButtonBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QContextMenuEvent, QIcon
from PyQt5.QtSvg import QSvgRenderer

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    STATE_UNKNOWN = 4   # 未知状态 - 蓝色
    
    # 状态颜色映射
    STATE_COLORS = {
        STATE_NORMAL: QColor(0, 255, 0),    # 绿色
        STATE_ERROR: QColor(255, 0, 0),     # 红色
        STATE_WARNING: QColor(255, 255, 0), # 黄色
        STATE_OFFLINE: QColor(128, 128, 128), # 灰色
        STATE_UNKNOWN: QColor(0, 0, 255)    # 蓝色
    }
    
    # 状态名称映射
    STATE_NAMES = {
        STATE_NORMAL: "正常运行",
        STATE_ERROR: "错误状态",
        STATE_WARNING: "警告状态",
        STATE_OFFLINE: "停止/离线",
        STATE_UNKNOWN: "未知状态"
    }
    
    # 信号定义
    stateChanged = pyqtSignal(int, int)  # 状态改变信号 (设备ID, 新状态)
    doubleClicked = pyqtSignal(int)      # 双击信号
    
    def __init__(self, device_id: int, device_name: str, initial_state: int = STATE_OFFLINE):
        super().__init__()
        self.device_id = device_id
        self.device_name = device_name
        self.current_state = initial_state
        self.byte_pos = 0
        self.bit_pos = 0
        self.active_value = 1
        self.inactive_value = 0
        
        self.setFixedSize(24, 24)
        self.setScaledContents(True)
        self.setToolTip(f"{device_name} - {self.STATE_NAMES[initial_state]}")
        
        # 加载SVG渲染器
        svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "assets", "icon", "circle.svg")
        self.svg_renderer = QSvgRenderer(svg_path)
        
        self.update_display()
    
    def set_position_info(self, byte_pos: int, bit_pos: int, active_value: int, inactive_value: int):
        """设置位置信息"""
        self.byte_pos = byte_pos
        self.bit_pos = bit_pos
        self.active_value = active_value
        self.inactive_value = inactive_value
    
    def update_display(self):
        """更新显示"""
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
        
        self.setPixmap(pixmap)
        self.setToolTip(f"{self.device_name} - {self.STATE_NAMES[self.current_state]}")
    
    def set_state(self, state: int):
        """设置状态"""
        if state != self.current_state and state in self.STATE_COLORS:
            old_state = self.current_state
            self.current_state = state
            self.update_display()
            self.stateChanged.emit(self.device_id, state)
            
            # 记录状态变化日志
            print(f"设备 {self.device_name} 状态从 {self.STATE_NAMES[old_state]} 变更为 {self.STATE_NAMES[state]}")
    
    def get_state(self) -> int:
        """获取当前状态"""
        return self.current_state


class DeviceEditDialog(QDialog):
    """设备编辑对话框"""
    
    def __init__(self, device_info: Dict = None, parent=None):
        super().__init__(parent)
        self.device_info = device_info or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑设备信息")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 表单布局
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit(self.device_info.get('设备名称', ''))
        form_layout.addRow("设备名称:", self.name_edit)
        
        self.byte_edit = QLineEdit(str(self.device_info.get('字节位数', 0)))
        form_layout.addRow("字节位数:", self.byte_edit)
        
        self.bit_edit = QLineEdit(str(self.device_info.get('比特位数', 0)))
        form_layout.addRow("比特位数:", self.bit_edit)
        
        self.active_edit = QLineEdit(str(self.device_info.get('活跃状态', 1)))
        form_layout.addRow("活跃状态:", self.active_edit)
        
        self.inactive_edit = QLineEdit(str(self.device_info.get('失效状态', 0)))
        form_layout.addRow("失效状态:", self.inactive_edit)
        
        self.initial_edit = QLineEdit(str(self.device_info.get('初始值', 0)))
        form_layout.addRow("初始值:", self.initial_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_device_info(self) -> Dict:
        """获取设备信息"""
        return {
            '设备名称': self.name_edit.text(),
            '字节位数': int(self.byte_edit.text() or 0),
            '比特位数': int(self.bit_edit.text() or 0),
            '活跃状态': int(self.active_edit.text() or 1),
            '失效状态': int(self.inactive_edit.text() or 0),
            '初始值': int(self.initial_edit.text() or 0)
        }


class DataSimulator(QThread):
    """数据模拟器 - 模拟外部数据源"""
    
    dataReceived = pyqtSignal(int, bytes)  # 数据接收信号 (字节位置, 数据)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.mutex = QMutex()
        self.data_buffer = {}
    
    def start_simulation(self):
        """开始模拟"""
        self.running = True
        self.start()
    
    def stop_simulation(self):
        """停止模拟"""
        self.running = False
        self.wait()
    
    def run(self):
        """运行模拟"""
        import random
        import time
        
        while self.running:
            # 模拟数据变化
            for byte_pos in range(2):  # 模拟2个字节的数据
                # 随机生成字节数据
                byte_data = random.randint(0, 255)
                self.dataReceived.emit(byte_pos, bytes([byte_data]))
                print(f"模拟数据: 字节位置 {byte_pos}, 数据 {byte_data}")
            
            time.sleep(2)  # 每2秒更新一次


class BulbStateMonitor(QWidget):
    """灯泡状态监控主窗口"""
    
    def __init__(self):
        super().__init__()
        self.devices = {}  # 设备字典 {device_id: BulbWidget}
        self.device_configs = {}  # 设备配置 {device_id: config_dict}
        self.byte_groups = {}  # 字节分组 {byte_pos: [device_ids]}
        self.data_simulator = DataSimulator()
        
        self.init_ui()
        self.load_config()
        self.setup_data_simulator()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("灯泡状态监控工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
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
        
        # 滚动区域用于显示设备
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        
        main_layout.addWidget(self.scroll_area)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止监控")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.reload_btn = QPushButton("重新加载配置")
        self.reload_btn.clicked.connect(self.reload_config)
        button_layout.addWidget(self.reload_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    
    def setup_data_simulator(self):
        """设置数据模拟器"""
        self.data_simulator.dataReceived.connect(self.process_data)
    
    def load_config(self):
        """加载配置文件"""
        try:
            # 创建示例配置文件
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf.xlsx")
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf.csv")
            
            if not os.path.exists(config_path) and not os.path.exists(csv_path):
                raise FileNotFoundError("未找到配置文件")
            
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
                    active_state = 1 if str(row['ActiveState']) == '有效' else 0
                    inactive_state = 0 if str(row['InactiveState']) == '无效' else 1
                    
                    config = {
                        '字节位数': int(row['BYTE']),
                        '比特位数': int(row['BITE']),
                        '设备名称': str(row['SignalName']),
                        '活跃状态': active_state,
                        '失效状态': inactive_state,
                        '初始值': int(row['INIT'])
                    }
                else:
                    # 中文列名格式
                    config = {
                        '字节位数': int(row['字节位数']),
                        '比特位数': int(row['比特位数']),
                        '设备名称': str(row['设备名称']),
                        '活跃状态': int(row['活跃状态']),
                        '失效状态': int(row['失效状态']),
                        '初始值': int(row['初始值'])
                    }
                
                # 创建设备控件
                initial_state = BulbWidget.STATE_NORMAL if config['初始值'] == config['活跃状态'] else BulbWidget.STATE_OFFLINE
                bulb = BulbWidget(device_id, config['设备名称'], initial_state)
                bulb.set_position_info(config['字节位数'], config['比特位数'], 
                                        config['活跃状态'], config['失效状态'])
                
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
        """处理接收到的数据"""
        if byte_pos in self.byte_groups:
            byte_value = data[0] if data else 0
            
            # 更新该字节对应的所有设备状态
            for device_id in self.byte_groups[byte_pos]:
                if device_id in self.devices:
                    bulb = self.devices[device_id]
                    bit_value = (byte_value >> bulb.bit_pos) & 1
                    
                    # 根据比特值确定状态
                    if bit_value == bulb.active_value:
                        new_state = BulbWidget.STATE_NORMAL
                    elif bit_value == bulb.inactive_value:
                        new_state = BulbWidget.STATE_OFFLINE
                    else:
                        new_state = BulbWidget.STATE_UNKNOWN
                    
                    bulb.set_state(new_state)
    
    def start_monitoring(self):
        """开始监控"""
        self.data_simulator.start_simulation()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        print("开始监控")
    
    def stop_monitoring(self):
        """停止监控"""
        self.data_simulator.stop_simulation()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("停止监控")
    
    def reload_config(self):
        """重新加载配置"""
        self.stop_monitoring()
        self.load_config()
        QMessageBox.information(self, "信息", "配置已重新加载")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("灯泡状态监控工具")
    
    # 设置应用图标
    try:
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "assets", "icon", "circle.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except:
        raise Exception("图标文件不存在")
    
    window = BulbStateMonitor()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()