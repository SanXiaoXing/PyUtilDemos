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
        
        self.TorR=self.channel_conf.get("TorR", "")
        self.selected_protocol = {"Tx": "", "Rx": ""}
        protocol_loader=ProtocolLoader()
        self.protocol_list=protocol_loader.list_protocols()
        self.fill_channel_info()
        self.init_protocol_selectors()
        self.btn_set.clicked.connect(self.on_accept)
        self.btn_cancel.clicked.connect(self.close)

    def fill_channel_info(self):
        self.label_ch.setText(self.channel_id)
        self.label_TorR.setText(self.channel_conf.get("TorR", ""))
        self.spinBox_freq.setValue(int(self.channel_conf.get("freq", 20)))
        self.comboBox_baudrate.setCurrentText(str(self.channel_conf.get("settings", {}).get("baudrate", 9600)))
        self.comboBox_databits.setCurrentText(str(self.channel_conf.get("settings", {}).get("bytesize", 8)))
        self.comboBox_stopbits.setCurrentText(str(self.channel_conf.get("settings", {}).get("stopbits", 1)))
        self.comboBox_parity.setCurrentText(self.channel_conf.get("settings", {}).get("parity", "None"))
        self.comboBox_store.setCurrentText("是" if self.channel_conf.get("store", True) else "否")

    def init_protocol_selectors(self):
        if self.TorR == "Tx":
            self.tabWidget.removeTab(1)
        elif self.TorR == "Rx":
            self.tabWidget.removeTab(0)

        self.comboBox_tx.addItems(self.protocol_list)
        self.comboBox_tx.setCurrentText(self.channel_conf.get("protocol", {}).get("Tx", ""))
        self.on_protocol_changed(self.comboBox_tx.currentText(), "Tx")
        self.comboBox_tx.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt, "Tx"))
        
        self.comboBox_rx.addItems(self.protocol_list)
        self.comboBox_rx.setCurrentText(self.channel_conf.get("protocol", {}).get("Rx", ""))
        self.on_protocol_changed(self.comboBox_rx.currentText(), "Rx")
        self.comboBox_rx.currentTextChanged.connect(lambda txt: self.on_protocol_changed(txt, "Rx"))
        

    def on_protocol_changed(self, protocol_name, direction=None):
        self.selected_protocol[direction] = protocol_name
        proto = protocol_config.get(protocol_name, {})
        if direction == "Tx":
            self.label_tx_length.setText(str(proto.get("length", "-")))
            self.label_tx_version.setText(proto.get("version", "-"))
            self.label_tx_desc.setText(proto.get("desc", "-"))
        elif direction == "Rx":
            self.label_rx_length.setText(str(proto.get("length", "-")))
            self.label_rx_version.setText(proto.get("version", "-"))
            self.label_rx_desc.setText(proto.get("desc", "-"))
       
    def on_accept(self):
        if self.channel_id not in channel_config:
            return
        
        self.channel_conf["freq"]=self.spinBox_freq.value()
        self.channel_conf["store"]=self.comboBox_store.currentText()=="是"
        self.channel_conf["settings"] = {
            "baudrate": self.comboBox_baudrate.currentText(),
            "bytesize": self.comboBox_databits.currentText(),
            "stopbits": self.comboBox_stopbits.currentText(),
            "parity": self.comboBox_parity.currentText()
        }

        if self.TorR == "Tx":
            self.channel_conf["protocol"] = {"Tx": self.selected_protocol.get("Tx", "")}
        elif self.TorR == "Rx":
            self.channel_conf["protocol"] = {"Rx": self.selected_protocol.get("Rx", "")}
        else:
            self.channel_conf["protocol"] = {
                "Tx": self.selected_protocol.get("Tx", ""),
                "Rx": self.selected_protocol.get("Rx", "")
            }

        channel_config[self.channel_id]=self.channel_conf

        save_channel_config()
        self.accept()

    def get_selected_protocol(self):
        return self.channel_conf["protocol"]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = ChannelConfigDialog(channel_id="0")
    form.show()
    sys.exit(app.exec_())
