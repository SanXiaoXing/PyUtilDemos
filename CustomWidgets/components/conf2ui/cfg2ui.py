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


# 自定义 QSlider 支持 tooltip hover 显示状态
class HoverSlider(QSlider):
    def __init__(self, labels=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.labels = labels or {}
        self.setMouseTracking(True)
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseMove:
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            handle_pos = self.style().subControlRect(
                self.style().CC_Slider,
                option,
                self.style().SC_SliderHandle,
                self
            )
            if handle_pos.contains(event.pos()):
                val = self.value()
                label = self.labels.get(str(val), str(val))
                QToolTip.showText(QCursor.pos(), label, self)
            else:
                QToolTip.hideText()
        return super().eventFilter(source, event)


class ConfigurableUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("动态界面生成")
        self.load_config(_CONFIG_PATH)
        self.init_ui()

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        # ✅ 控件布局参数
        self.spinbox_per_row = 2  # 每行几个输入框
        self.slider_per_row = 1   # 每行几个开关滑块
        input_group=self.init_doublespinbox()
        switch_group=self.init_slider()
        
        self.main_layout.addWidget(input_group)
        self.main_layout.addWidget(switch_group)



    def init_doublespinbox(self):
        # ▶ 输入区域 GroupBox
        input_group = QGroupBox("参数输入")
        input_layout = QGridLayout()
        self.input_widgets = []

        for idx, item in enumerate(self.config.get("input_area", [])):
            row = idx // self.spinbox_per_row
            col = idx % self.spinbox_per_row

            label = QLabel(item["label"])
            spin = QDoubleSpinBox()
            spin.setRange(item["min"], item["max"])
            spin.setSingleStep(item["step"])
            spin.setValue(item["default"])
            spin.setObjectName(item['signame'])
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            spin.editingFinished.connect(lambda s=spin, l=item["label"]: self.on_spinbox_finished(s, l))

            # 小横排，保持 label 和控件紧凑
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(spin)
            spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            wrapper = QWidget()
            wrapper.setLayout(hbox)

            input_layout.addWidget(wrapper, row, col)
            self.input_widgets.append((label, spin))

        input_group.setLayout(input_layout)

        return input_group
    

    
    def on_spinbox_finished(self, spinbox, label):
        value = spinbox.value()
        signame=spinbox.objectName()
        print(f"{label} {signame} 当前值：{value}")



    
    def init_slider(self):
        # ▶ 开关区域 GroupBox
        switch_group = QGroupBox("开关设置")
        switch_layout = QGridLayout()
        self.switch_widgets = []

        for idx, item in enumerate(self.config.get("switch_area", [])):
            row = idx // self.slider_per_row
            col = idx % self.slider_per_row

            label = QLabel(item["label"])
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # ✅ 提取"0"和"1"对应含义
            state_labels = {
                "0": item.get("0", "0"),
                "1": item.get("1", "1")
            }

            slider = HoverSlider(labels=state_labels, orientation=Qt.Horizontal)
            slider.setRange(0, 1)
            slider.setSingleStep(1)
            slider.setTickInterval(1)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setValue(item["default"])
            slider.setMaximumWidth(150)
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            slider.setStyleSheet(_SLIDER_QSS)

            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(slider)
            wrapper = QWidget()
            wrapper.setLayout(hbox)

            switch_layout.addWidget(wrapper, row, col)
            self.switch_widgets.append((label, slider))

        switch_group.setLayout(switch_layout)

        return switch_group





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigurableUI()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())
