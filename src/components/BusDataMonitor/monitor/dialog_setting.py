import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QPushButton, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt

class ChannelConfigDialog(QDialog):
    """
    通道配置对话框
    - 显示通道基础配置（通道配置文件）
    - 协议选择与显示（协议信息文件）
    """
    def __init__(self, channel_json: Path, protocol_json: Path, channel_id: int, parent=None):
        """
        :param channel_json: 通道配置文件路径
        :param protocol_json: 协议信息文件路径
        :param channel_id: 当前通道号
        :param parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("通道配置信息")
        self.resize(450, 400)
        self.channel_json = channel_json
        self.protocol_json = protocol_json
        self.channel_id = str(channel_id)
        self.channel_conf = {}
        self.protocol_conf = {}
        self.protocols = {}  # 所有协议字典
        self.selected_protocol = None

        # --- UI ---
        self.layout = QVBoxLayout(self)

        # 基础信息区
        self.base_form = QFormLayout()
        base_group = QGroupBox("通道基础信息")
        base_group.setLayout(self.base_form)
        self.layout.addWidget(base_group)

        # 协议选择区
        self.protocol_combo = QComboBox()
        self.protocol_combo.currentTextChanged.connect(self.on_protocol_changed)
        self.layout.addWidget(QLabel("选择通讯协议:"))
        self.layout.addWidget(self.protocol_combo)

        # 协议信息区
        self.proto_form = QFormLayout()
        proto_group = QGroupBox("协议详细信息")
        proto_group.setLayout(self.proto_form)
        self.layout.addWidget(proto_group)

        # 确认按钮
        self.btn_ok = QPushButton("确定")
        self.btn_ok.clicked.connect(self.accept)
        self.layout.addWidget(self.btn_ok, alignment=Qt.AlignCenter)

        # 加载配置
        self.load_config()

    def load_config(self):
        """加载通道和协议配置"""
        # --- 读取通道配置 ---
        if not self.channel_json.exists():
            QMessageBox.warning(self, "错误", f"通道配置文件不存在:\n{self.channel_json}")
            self.close()
            return

        with open(self.channel_json, "r", encoding="utf-8") as f:
            channel_data = json.load(f)
        self.channel_conf = channel_data.get(self.channel_id, {})

        if not self.channel_conf:
            QMessageBox.warning(self, "错误", f"未找到通道配置: {self.channel_id}")
            self.close()
            return

        # 填写基础信息
        self.base_form.addRow("通道号:", QLabel(self.channel_id))
        self.base_form.addRow("方向 (TorR):", QLabel(self.channel_conf.get("TorR", "-")))
        self.base_form.addRow("频率 (Hz):", QLabel(str(self.channel_conf.get("freq", "-"))))
        settings = self.channel_conf.get("settings", {})
        self.base_form.addRow("波特率:", QLabel(str(settings.get("baudrate", "-"))))
        self.base_form.addRow("数据位:", QLabel(str(settings.get("bytesize", "-"))))
        self.base_form.addRow("停止位:", QLabel(str(settings.get("stopbits", "-"))))
        self.base_form.addRow("奇偶校验:", QLabel(settings.get("parity", "-")))
        self.base_form.addRow("是否存储:", QLabel(self.channel_conf.get("store", "-")))

        # --- 读取协议配置 ---
        if not self.protocol_json.exists():
            QMessageBox.warning(self, "错误", f"协议文件不存在:\n{self.protocol_json}")
            self.close()
            return

        with open(self.protocol_json, "r", encoding="utf-8") as f:
            self.protocols = json.load(f)

        # 协议选择列表（只允许现有协议）
        self.protocol_combo.addItems(self.protocols.keys())
        default_protocol = self.channel_conf.get("protocol")
        if default_protocol in self.protocols:
            self.protocol_combo.setCurrentText(default_protocol)
        else:
            self.protocol_combo.setCurrentIndex(0)

        # 加载对应协议内容
        self.on_protocol_changed(self.protocol_combo.currentText())

    def on_protocol_changed(self, protocol_name):
        """切换协议显示"""
        self.selected_protocol = protocol_name
        proto = self.protocols.get(protocol_name, {})
        # 先清空旧内容
        while self.proto_form.rowCount():
            self.proto_form.removeRow(0)
        # 填入新内容
        self.proto_form.addRow("协议名称:", QLabel(protocol_name))
        self.proto_form.addRow("通道号:", QLabel(str(proto.get("channel", "-"))))
        self.proto_form.addRow("数据长度:", QLabel(str(proto.get("length", "-"))))
        self.proto_form.addRow("版本:", QLabel(proto.get("version", "-")))
        self.proto_form.addRow("描述:", QLabel(proto.get("desc", "-")))

    def get_selected_protocol(self):
        """返回用户选择的协议名"""
        return self.selected_protocol
