"""
使用doublespinbox作为输入框

"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


_CONFIG_PATH = Path(__file__).parent / "config.json"


class InputSpinxboForm(QWidget):
    def __init__(self):
        super().__init__()
        self.load_config(_CONFIG_PATH)
        self.init_ui()

    def load_config(self, path):
        # 加载配置文件
        with open(path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        # ✅ 控件布局参数
        self.spinbox_per_row = 2  # 每行几个输入框
        input_group=self.init_doublespinbox()
        self.main_layout.addWidget(input_group)


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
            spin.setMinimumWidth(50)
            spin.setMaximumWidth(100)
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
        """spinbox编辑完成时调用"""
        """可在此自定义处理逻辑"""
        value = spinbox.value()
        signame=spinbox.objectName()
        print(f"{label} {signame} 当前值：{value}")



    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InputSpinxboForm()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())
