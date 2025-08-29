import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from src.components.BusDataMonitor.monitor.gui.Ui_dialog_setting import *
from src.components.BusDataMonitor.config import channel_config, protocol_config, save_channel_config
from src.components.BusDataMonitor.protocol import ProtocolLoader

class ChannelConfigDialog(QDialog,Ui_dialog_setting):
    """
    通道配置对话框（支持单向/双向通道）
    """
    def __init__(self, channel_id: int, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("通道配置信息")
        self.resize(300, 400)
        self.channel_id = str(channel_id)
        self.channel_conf = channel_config.get(self.channel_id, {})

        if not self.channel_conf:
            QMessageBox.warning(self, "错误", f"未找到通道配置: {self.channel_id}")
            self.close()
            return

        self.selected_protocol = None  # 单向: str，双向: dict {"Tx":..., "Rx":...}
        protocol_loader=ProtocolLoader()
        self.protocol_list=protocol_loader.list_protocols()
        # 基础信息区
        self.fill_channel_info()
        # 协议选择区
        self.init_protocol_selectors()
        # 确认按钮
        self.btn_set.clicked.connect(self.on_accept)
        self.btn_cancel.clicked.connect(self.close)



    def fill_channel_info(self):
        """显示通道基础信息"""
        self.label_ch.setText(self.channel_id)
        self.label_TorR.setText(self.channel_conf.get("TorR", ""))
        self.spinBox_freq.setValue(int(self.channel_conf.get("freq", 20)))
        self.comboBox_baudrate.setCurrentText(str(self.channel_conf.get("settings", {}).get("baudrate", 9600)))
        self.comboBox_databits.setCurrentText(str(self.channel_conf.get("settings", {}).get("bytesize", 8)))
        self.comboBox_stopbits.setCurrentText(str(self.channel_conf.get("settings", {}).get("stopbits", 1)))
        self.comboBox_parity.setCurrentText(self.channel_conf.get("settings", {}).get("parity", "None"))
        self.comboBox_store.setCurrentText(self.channel_conf.get("store", "是"))


    def init_protocol_selectors(self):
        """初始化协议选择控件与协议信息区"""
        TorR = self.channel_conf.get("TorR", "")
        
        self.comboBox_tx.addItems(self.protocol_list)
        self.comboBox_tx.setCurrentText(self.channel_conf["protocol"].get("Tx", ""))
        self.comboBox_tx.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt, "Tx"))
        #self.on_protocol_changed(self.comboBox_tx.currentText(), "Tx")

        self.comboBox_rx.addItems(self.protocol_list)
        self.comboBox_rx.setCurrentText(self.channel_conf["protocol"].get("Rx", ""))
        self.comboBox_rx.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt, "Rx"))
        #self.on_protocol_changed(self.comboBox_rx.currentText(), "Rx")

        if TorR=="Tx":
            self.tabWidget.setTabEnabled(1, False)
        elif TorR=="Rx":
            self.tabWidget.setTabEnabled(0, False)




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
        channel_config[self.channel_id]["protocol"] = self.selected_protocol.copy()
        save_channel_config()
        self.accept()

    def get_selected_protocol(self):
        """返回用户选择的协议"""
        return self.selected_protocol
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = ChannelConfigDialog(channel_id="1")
    form.show()
    sys.exit(app.exec_())