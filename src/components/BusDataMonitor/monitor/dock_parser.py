# parsed_data_dock.py
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from src.components.BusDataMonitor.monitor.gui.Ui_dock_parser import Ui_dock_parser 
from src.components.BusDataMonitor.monitor.busdata_parser import BusDataParser
from src.components.BusDataMonitor.protocol import ProtocolLoader

class ParserWorker(QObject):
    finished = pyqtSignal(dict)  # 解析完成后发出结果
    def __init__(self, protocol, hex_data):
        super().__init__()
        self.protocol = protocol
        self.hex_data = hex_data

    def run(self):
        parser = BusDataParser(self.protocol)
        result = parser.parse(self.hex_data)
        self.finished.emit(result)


class DockParser(QWidget, Ui_dock_parser):
    def __init__(self, protocol_name,index, parent=None):
        super().__init__( parent)
        self.setupUi(self)
        self.protocol_name = protocol_name
        self.curr_index=index
        self.hex_display = False  # 默认显示解析值
        self.init_ui()

    def init_ui(self):
        self.model = QStandardItemModel(0, 2, self)
        self.model.setHorizontalHeaderLabels(["字段名称", "值"])
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.label_index.setText(f"序号：{self.curr_index}")
        self.btn_toggle.clicked.connect(self.toggle_display)
        


    def toggle_display(self):
        self.hex_display = not self.hex_display
        self.refresh_display()

    def update_data(self, hex_str):
        """ 启动线程解析数据 """
        self.current_hex = hex_str
        protocol_loader = ProtocolLoader()
        protocol = protocol_loader.get(self.protocol_name)
        self.thread = QThread()
        self.worker = ParserWorker(protocol, hex_str)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_parsed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_parsed(self, parsed_dict):
        self.parsed_data = parsed_dict
        self.refresh_display()

    def refresh_display(self):
        self.model.removeRows(0, self.model.rowCount())
        if not hasattr(self, "parsed_data"):
            return

        for key, value in self.parsed_data.items():
            if self.hex_display:
                # 显示16进制
                if isinstance(value, int):
                    display_val = hex(value)
                else:
                    display_val = str(value)
            else:
                display_val = str(value)
            self.model.appendRow([QStandardItem(key), QStandardItem(display_val)])
