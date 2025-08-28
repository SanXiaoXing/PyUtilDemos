from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt
from src.components.BusDataMonitor.config import channel_config, protocol_config, save_channel_config

class ChannelConfigDialog(QDialog):
    """
    通道配置对话框（支持单向/双向通道）
    """
    def __init__(self, channel_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通道配置信息")
        self.resize(450, 550)
        self.channel_id = str(channel_id)
        self.channel_conf = channel_config.get(self.channel_id, {})

        if not self.channel_conf:
            QMessageBox.warning(self, "错误", f"未找到通道配置: {self.channel_id}")
            self.close()
            return

        self.selected_protocol = None  # 单向: str，双向: dict {"Tx":..., "Rx":...}

        # --- UI ---
        self.layout = QVBoxLayout(self)

        # 基础信息区（可编辑）
        self.base_form = QFormLayout()
        base_group = QGroupBox("通道基础信息（可编辑）")
        base_group.setLayout(self.base_form)
        self.layout.addWidget(base_group)

        self.fill_channel_info()

        # 协议选择区
        self.init_protocol_selectors()

        # 确认按钮
        self.btn_ok = QPushButton("确定")
        self.btn_ok.clicked.connect(self.on_accept)
        self.layout.addWidget(self.btn_ok, alignment=Qt.AlignCenter)

    def fill_channel_info(self):
        """显示通道基础信息"""
        # 通道号
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
        self.combo_parity.addItems(["N", "E", "O"])
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

    def init_protocol_selectors(self):
        """初始化协议选择控件与协议信息区"""
        TorR = self.channel_conf.get("TorR", "Tx")
        if TorR == "Tx/Rx":
            # 双向通道
            self.selected_protocol = {"Tx": "", "Rx": ""}
            
            # Tx
            self.tx_protocol_combo = QComboBox()
            self.tx_protocol_combo.addItems(protocol_config.keys())
            self.tx_protocol_combo.setCurrentText(self.channel_conf["protocol"].get("Tx", "send422"))
            self.tx_protocol_combo.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt, "Tx"))
            self.layout.addWidget(QLabel("选择 Tx 协议:"))
            self.layout.addWidget(self.tx_protocol_combo)

            self.tx_proto_form = QFormLayout()
            tx_group = QGroupBox("Tx 协议详细信息（只读）")
            tx_group.setLayout(self.tx_proto_form)
            self.layout.addWidget(tx_group)
            self.on_protocol_changed(self.tx_protocol_combo.currentText(), "Tx")

            # Rx
            self.rx_protocol_combo = QComboBox()
            self.rx_protocol_combo.addItems(protocol_config.keys())
            self.rx_protocol_combo.setCurrentText(self.channel_conf["protocol"].get("Rx", "recv422"))
            self.rx_protocol_combo.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt, "Rx"))
            self.layout.addWidget(QLabel("选择 Rx 协议:"))
            self.layout.addWidget(self.rx_protocol_combo)

            self.rx_proto_form = QFormLayout()
            rx_group = QGroupBox("Rx 协议详细信息（只读）")
            rx_group.setLayout(self.rx_proto_form)
            self.layout.addWidget(rx_group)
            self.on_protocol_changed(self.rx_protocol_combo.currentText(), "Rx")
        else:
            # 单向通道
            self.selected_protocol = self.channel_conf.get("protocol", "")
            self.protocol_combo = QComboBox()
            self.protocol_combo.addItems(protocol_config.keys())
            self.protocol_combo.setCurrentText(self.selected_protocol)
            self.protocol_combo.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt))
            self.layout.addWidget(QLabel("选择通讯协议:"))
            self.layout.addWidget(self.protocol_combo)

            self.proto_form = QFormLayout()
            proto_group = QGroupBox("协议详细信息（只读）")
            proto_group.setLayout(self.proto_form)
            self.layout.addWidget(proto_group)
            self.on_protocol_changed(self.protocol_combo.currentText())

    def on_protocol_changed(self, protocol_name, direction=None):
        """切换协议显示（只读）"""
        if direction:
            # 双向通道
            if not isinstance(self.selected_protocol, dict):
                self.selected_protocol = {"Tx": "", "Rx": ""}
            self.selected_protocol[direction] = protocol_name
            form = self.tx_proto_form if direction == "Tx" else self.rx_proto_form
        else:
            # 单向通道
            self.selected_protocol = protocol_name
            form = self.proto_form

        proto = protocol_config.get(protocol_name, {})
        # 清空旧内容
        while form.rowCount():
            form.removeRow(0)
        # 填入新内容
        form.addRow("协议名称:", QLabel(protocol_name))
        form.addRow("数据长度:", QLabel(str(proto.get("length", "-"))))
        form.addRow("版本:", QLabel(proto.get("version", "-")))
        form.addRow("描述:", QLabel(proto.get("desc", "-")))

    def on_accept(self):
        """保存修改到 channel_config"""
        if self.channel_id not in channel_config:
            return

        # 更新基础信息
        channel_config[self.channel_id]["freq"] = self.spin_freq.value()
        channel_config[self.channel_id]["store"] = self.combo_store.currentText()
        channel_config[self.channel_id]["settings"] = {
            "baudrate": self.spin_baud.value(),
            "bytesize": self.spin_bytesize.value(),
            "stopbits": self.spin_stopbits.value(),
            "parity": self.combo_parity.currentText()
        }

        TorR = self.channel_conf.get("TorR", "Tx")
        if TorR == "Tx/Rx": 
            channel_config[self.channel_id]["protocol"] = self.selected_protocol.copy()
        else:
            channel_config[self.channel_id]["protocol"] = self.selected_protocol

        save_channel_config()
        self.accept()

    def get_selected_protocol(self):
        """返回用户选择的协议"""
        return self.selected_protocol
