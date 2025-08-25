"""
开关面板控件模块
===============

该模块提供了一个基于QCheckBox的开关控制面板组件，具有以下特点：
- 支持从JSON配置文件动态加载开关配置
- 自动布局管理，可配置每行显示的开关数量
- 支持为每个开关设置自定义标签和状态文本
- 提供开关状态改变事件回调机制


适用场景：设备控制面板、系统设置界面、功能开关管理等需要布尔型控制的场合。
"""


import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QCheckBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

_CONFIG_PATH = Path(__file__).parent / "config.json"

class SwitchPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("开关面板")
        self.switch_widgets = {}      # signame -> checkbox
        self.status_labels = {}       # signame -> 状态 QLabel
        self.items_per_row = 2  # 每行控件组数

        # 设置 checkbox QSS 样式
        self.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #8f8f8f;
                border-radius: 4px;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                background-color: #4caf50;
                border: 2px solid #388e3c;
            }

            QCheckBox::indicator:unchecked:hover {
                background-color: #f0f0f0;
            }

            QCheckBox::indicator:checked:hover {
                background-color: #66bb6a;
            }

            QCheckBox {
                spacing: 8px;
            }
        """)

        layout = QVBoxLayout()
        config = self.load_config()
        if config:
            group_box = self.create_switches(config)
            layout.addWidget(group_box)
        self.setLayout(layout)

    def load_config(self):
        """从 JSON 文件加载配置"""
        try:
            with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载配置文件：\n{e}")
            return None

    def create_switches(self, config):
        """根据配置创建开关按钮并放入 GroupBox 中"""
        group_box = QGroupBox("开关设置")
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        for idx, item in enumerate(config.get("switch_area", [])):
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(4)  # 比 0 稍美观

            checkbox = QCheckBox(item["label"])  # 文字直接在 checkbox 上
            checkbox.setContentsMargins(0, 0, 0, 0)

            status_label = QLabel()
            status_label.setContentsMargins(0, 0, 0, 0)
            status_text = item.get("1", "开启") if checkbox.isChecked() else item.get("0", "关闭")
            status_label.setText(status_text)
            status_label.setFixedWidth(40)

            h_layout.addWidget(status_label)
            h_layout.addWidget(checkbox)


            checkbox.stateChanged.connect(
                lambda state, cb=checkbox, st_label=status_label, it=item:
                    self.on_checkbox_state_changed(cb, st_label, it)
            )


            # 把每组放到 grid layout 的合适位置
            row = idx // self.items_per_row
            col = idx % self.items_per_row
            grid_layout.addLayout(h_layout, row, col)

            # 保存引用
            self.switch_widgets[item["signame"]] = checkbox
            self.status_labels[item["signame"]] = status_label

        group_box.setLayout(grid_layout)
        return group_box
    

    def on_checkbox_state_changed(self, checkbox, status_label, item):
        """开关状态改变时的处理函数"""
        new_state = item.get("1", "开启") if checkbox.isChecked() else item.get("0", "关闭")
        status_label.setText(new_state)
        # 👉 可在此处扩展：打印/写日志/发信号等
        print(f"{item['signame']} 状态变为: {new_state}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SwitchPanel()  
    window.resize(600, 300)
    window.show()
    sys.exit(app.exec_())
