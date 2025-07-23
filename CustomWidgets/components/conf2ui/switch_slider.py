"""
开关滑块控件模块

该模块提供了一个基于QSlider的开关控制面板组件，具有以下特点：
- 支持从JSON配置文件动态加载开关配置
- 使用滑块形式的开关控件，提供更好的用户体验
- 自动布局管理，可配置每行显示的开关数量
- 支持为每个开关设置自定义标签和状态文本
- 提供开关状态改变事件回调机制
- 具有美观的自定义样式表(QSS)外观



适用场景：设备控制面板、系统设置界面、功能开关管理等需要布尔型控制但希望有更好交互体验的场合。
"""


import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


_CONFIG_PATH = Path(__file__).parent / "config.json"


_SLIDER_QSS="""
            QSlider::groove:horizontal {
                height: 10px;
                background: #dddddd;
                border: 1px solid #999999;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                height: 20px;
                background: #147aff;
                border: 1px solid #147aff;
                border-radius: 10px;
                margin: -5px 0; /* Handle overlaps the groove by 5px on each side */
            }
            QSlider::handle:horizontal:hover {
                background: #156dd7;
            }"""


class SwitchSliderForm(QWidget):
    def __init__(self):
        super().__init__()
        self.load_config(_CONFIG_PATH)
        self.init_ui()

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        # ✅ 控件布局参数
        self.slider_per_row = 2   # 每行几个开关滑块
        switch_group=self.init_slider()
        self.main_layout.addWidget(switch_group)

    
    def init_slider(self):
        # ▶ 开关区域 GroupBox
        switch_group = QGroupBox("开关设置")
        switch_layout = QGridLayout()
        switch_layout.setContentsMargins(10, 10, 10, 10)
        switch_layout.setHorizontalSpacing(12)
        switch_layout.setVerticalSpacing(8)

        for idx, item in enumerate(self.config.get("switch_area", [])):
            row = idx // self.slider_per_row
            col = idx % self.slider_per_row

            label = QLabel(item["label"])
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            # 提取状态含义
            state_labels = {
                "0": item.get("0", "0"),
                "1": item.get("1", "1")
            }

            # 状态 QLabel
            status_label = QLabel(state_labels[str(item["default"])])
            status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            status_label.setMinimumWidth(40)
            status_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            # 滑块
            slider = QSlider(Qt.Horizontal)
            slider.setObjectName(item['signame'])
            slider.setRange(0, 1)
            slider.setSingleStep(1)
            slider.setTickInterval(1)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setValue(item["default"])
            slider.setMinimumWidth(60)
            slider.setMaximumWidth(80)
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            slider.setStyleSheet(_SLIDER_QSS)

            # 绑定更新状态
            slider.valueChanged.connect(lambda val, it=item, lb=status_label: self.switch_changed_value(it, val, lb))

            # 按列添加到GridLayout（按列对齐）
            base_col = col * 3
            switch_layout.addWidget(label, row, base_col)
            switch_layout.addWidget(slider, row, base_col + 1)
            switch_layout.addWidget(status_label, row, base_col + 2)

        switch_group.setLayout(switch_layout)
        return switch_group


    def switch_changed_value(self, item, value, status_label):
        """slider状态改变时触发"""
        label = item['label']
        state_label = item.get(str(value), str(value))
        status_label.setText(state_label)

        print(f'{label} changed: {state_label} ({value})')





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SwitchSliderForm()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())
