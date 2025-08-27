from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QGroupBox, QLineEdit, QSpinBox
)
from PyQt5.QtCore import Qt
from src.components.BusDataMonitor.config import channel_config, protocol_config, save_channel_config

class ChannelConfigDialog(QDialog):
    """
    通道配置对话框
    - 从全局 channel_config / protocol_config 读取
    - 通道基础配置可修改，点击确定写回 JSON
    - 协议信息只读
    """
    def __init__(self, channel_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通道配置信息")
        self.resize(450, 500)
        self.channel_id = str(channel_id)
        self.channel_conf = channel_config.get(self.channel_id, {})
        self.selected_protocol = self.channel_conf.get("protocol")

        # --- UI ---
        self.layout = QVBoxLayout(self)

        # 基础信息区（可编辑）
        self.base_form = QFormLayout()
        base_group = QGroupBox("通道基础信息（可编辑）")
        base_group.setLayout(self.base_form)
        self.layout.addWidget(base_group)

        # 协议选择区（可改）
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(protocol_config.keys())
        self.protocol_combo.setCurrentText(self.selected_protocol)
        self.protocol_combo.currentTextChanged.connect(self.on_protocol_changed)
        self.layout.addWidget(QLabel("选择通讯协议:"))
        self.layout.addWidget(self.protocol_combo)

        # 协议信息区（只读）
        self.proto_form = QFormLayout()
        proto_group = QGroupBox("协议详细信息（只读）")
        proto_group.setLayout(self.proto_form)
        self.layout.addWidget(proto_group)

        # 确认按钮
        self.btn_ok = QPushButton("确定")
        self.btn_ok.clicked.connect(self.on_accept)
        self.layout.addWidget(self.btn_ok, alignment=Qt.AlignCenter)

        self.fill_channel_info()
        self.on_protocol_changed(self.selected_protocol)

    def fill_channel_info(self):
        """显示通道信息（改为可编辑）"""
        if not self.channel_conf:
            QMessageBox.warning(self, "错误", f"未找到通道配置: {self.channel_id}")
            self.close()
            return

        # 通道号显示为标签（不可编辑）
        self.label_channel_id = QLabel(self.channel_id)
        self.base_form.addRow("通道号:", self.label_channel_id)

        # 方向 TorR
        self.TorR = QLabel(self.channel_conf.get("TorR", "Tx"))
        self.base_form.addRow("方向 (TorR):", self.TorR)
        
        # 频率
        self.spin_freq = QSpinBox()
        self.spin_freq.setRange(1, 1000000)
        self.spin_freq.setValue(int(self.channel_conf.get("freq", 20)))
        self.base_form.addRow("频率 (Hz):", self.spin_freq)

        # 串口设置
        settings = self.channel_conf.get("settings", {})
        self.spin_baud = QSpinBox()
        self.spin_baud.setRange(1200, 4000000)
        self.spin_baud.setValue(int(settings.get("baudrate", 9600)))

        self.spin_bytesize = QSpinBox()
        self.spin_bytesize.setRange(5, 9)
        self.spin_bytesize.setValue(int(settings.get("bytesize", 8)))

        self.spin_stopbits = QSpinBox()
        self.spin_stopbits.setRange(1, 2)
        self.spin_stopbits.setValue(int(settings.get("stopbits", 1)))

        self.combo_parity = QComboBox()
        self.combo_parity.addItems(["N", "E", "O"])  # None, Even, Odd
        self.combo_parity.setCurrentText(settings.get("parity", "N"))

        self.base_form.addRow("波特率:", self.spin_baud)
        self.base_form.addRow("数据位:", self.spin_bytesize)
        self.base_form.addRow("停止位:", self.spin_stopbits)
        self.base_form.addRow("奇偶校验:", self.combo_parity)

        # 是否存储
        self.combo_store = QComboBox()
        self.combo_store.addItems(["true", "false"])
        self.combo_store.setCurrentText(self.channel_conf.get("store", "true"))
        self.base_form.addRow("是否存储:", self.combo_store)

    def on_protocol_changed(self, protocol_name):
        """切换协议显示（只读）"""
        self.selected_protocol = protocol_name 
        proto = protocol_config.get(protocol_name, {})
        self.selected_version= proto.get("version", "")
        # 清空旧内容
        while self.proto_form.rowCount():
            self.proto_form.removeRow(0)
        # 填入新内容（不可编辑）
        self.proto_form.addRow("协议名称:", QLabel(protocol_name))
        self.proto_form.addRow("数据长度:", QLabel(str(proto.get("length", "-"))))
        self.proto_form.addRow("版本:", QLabel(proto.get("version", "-")))
        self.proto_form.addRow("描述:", QLabel(proto.get("desc", "-")))

    def on_accept(self):
        """把修改同步回 channel_config.json"""
        if self.channel_id in channel_config:
            # 更新通道配置
            channel_config[self.channel_id]["TorR"] = self.combo_torr.currentText()
            channel_config[self.channel_id]["freq"] = self.spin_freq.value()
            channel_config[self.channel_id]["store"] = self.combo_store.currentText()
            channel_config[self.channel_id]["protocol"] = self.selected_protocol
            channel_config[self.channel_id]["settings"] = {
                "baudrate": self.spin_baud.value(),
                "bytesize": self.spin_bytesize.value(),
                "stopbits": self.spin_stopbits.value(),
                "parity": self.combo_parity.currentText()
            }
            # 写回文件
            save_channel_config()
        self.accept()

    def get_selected_protocol(self):
        """返回用户选择的协议名"""
        return f"{self.selected_protocol}V{self.selected_version}"
