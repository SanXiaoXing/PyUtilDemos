"""
总线数据监控
===========


按总线->通道->数据的层级显示数据
以列表的形式显示监控对象的工程值和原始值

 """   


import sys
import os
import time
import json
import h5py
import threading
import queue
from pathlib import Path
from collections import defaultdict
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal

# ========== 加载协议描述 ==========
class ProtocolDecoder:
    def __init__(self, protocol_file):
        # 打开协议文件，读取协议内容
        with open(protocol_file, 'r') as f:
            self.protocol = json.load(f)

    def decode(self, raw_bytes, channel):
        # 获取协议中对应通道的解析规则
        fmt = self.protocol.get(channel, {})
        if not fmt:
            # 如果通道不存在，返回错误信息
            return {"error": "unknown channel"}
        # 示例解析规则：假设结构为 {id:1B, value:2B, status:1B}
        return {
            # id为raw_bytes的第一个字节
            "id": raw_bytes[0],
            # value为raw_bytes的第2到第3个字节，以大端字节序转换为整数
            "value": int.from_bytes(raw_bytes[1:3], 'big'),
            # status为raw_bytes的第4个字节，与0x0F进行按位与操作，得到低4位
            "status": raw_bytes[3] & 0x0F
        }

# ========== HDF5 写入类 ==========
class HDFWriter:
    # 初始化HDFWriter类，传入文件名
    def __init__(self, filename):
        # 打开文件，以写模式
        self.file = h5py.File(filename, 'w')
        # 创建锁，用于线程安全
        self.lock = threading.Lock()
        # 写入次数
        self.write_count = 0
        # 每个通道的写入次数
        self.channel_write_counts = defaultdict(int)

    # 写入数据
    def write(self, channel, timestamp, raw_data, parsed_data=None):
        # 加锁，保证线程安全
        with self.lock:
            # 创建数据组
            grp = self.file.require_group(f"/data/{channel}")
            # 创建raw数据集
            raw_dset = grp.require_dataset("raw", shape=(0,), maxshape=(None,), dtype=h5py.vlen_dtype(bytes), exact=False)
            # 创建timestamp数据集
            ts_dset = grp.require_dataset("timestamp", shape=(0,), maxshape=(None,), dtype='f8', exact=False)
            # 创建parsed数据集
            parsed_dset = grp.require_dataset("parsed", shape=(0,), maxshape=(None,), dtype=h5py.string_dtype('utf-8'), exact=False)

            # 获取当前数据集的长度
            idx = raw_dset.shape[0]
            # 调整数据集大小
            raw_dset.resize((idx + 1,))
            ts_dset.resize((idx + 1,))
            parsed_dset.resize((idx + 1,))

            # 写入数据
            raw_dset[idx] = raw_data
            ts_dset[idx] = timestamp
            parsed_dset[idx] = json.dumps(parsed_data)

            # 更新写入次数
            self.write_count += 1
            # 更新每个通道的写入次数
            self.channel_write_counts[channel] += 1

    # 关闭文件
    def close(self):
        self.file.close()

# ========== 数据采集线程 ==========
class DataCollector(QThread):
    # 定义一个信号，用于传递通道和随机数
    data_collected = pyqtSignal(str, bytes)

    # 初始化函数，传入通道和间隔时间
    def __init__(self, channel, interval_ms=20):
        super().__init__()
        self.channel = channel
        self.interval = interval_ms / 1000
        self.running = True

    # 运行函数，循环执行，直到self.running为False
    def run(self):
        # 循环执行，直到self.running为False
        while self.running:
            # 生成8个字节的随机数
            raw = os.urandom(8)
            # 发射信号，将通道和随机数传递给槽函数
            self.data_collected.emit(self.channel, raw)
            # 暂停一段时间
            time.sleep(self.interval)

    def stop(self):
        self.running = False

# ========== 数据解析线程 ==========
class ParserThread(QThread):
    # 定义一个信号，用于发送解析后的数据
    parsed_signal = pyqtSignal(str, dict)

    # 初始化函数，接收输入队列、输出队列和解码器作为参数
    def __init__(self, in_queue, out_queue, decoder):
        super().__init__()
        self.queue = in_queue
        self.out_queue = out_queue
        self.decoder = decoder
        self.running = True

    # 运行函数，从输入队列中获取数据，进行解码，并将解码后的数据放入输出队列中
    def run(self):
        while self.running:
            try:
                # 从输入队列中获取数据，超时时间为0.1秒
                channel, raw = self.queue.get(timeout=0.1)
                # 解码数据
                parsed = self.decoder.decode(raw, channel)
                # 将解码后的数据放入输出队列中
                self.out_queue.put((channel, raw, parsed))
                # 发送解析后的数据信号
                self.parsed_signal.emit(channel, parsed)
            except queue.Empty:
                # 如果队列为空，则继续循环
                continue

    # 停止函数，将running标志设置为False
    def stop(self):
        self.running = False

# ========== 写入线程 ==========
class WriterThread(QThread):
    # 初始化WriterThread类，继承自QThread
    def __init__(self, writer, in_queue):
        # 调用父类的初始化方法
        super().__init__()
        # 将传入的writer和in_queue赋值给类的属性
        self.writer = writer
        self.queue = in_queue
        # 设置running属性为True
        self.running = True

    def run(self):
        # 循环执行，直到running属性为False
        while self.running:
            try:
                # 从队列中获取channel、raw和parsed
                channel, raw, parsed = self.queue.get(timeout=0.1)
                # 获取当前时间戳
                timestamp = time.time()
                # 调用writer的write方法，将channel、timestamp、raw和parsed传入
                self.writer.write(channel, timestamp, raw, parsed)
            except queue.Empty:
                # 如果队列为空，继续循环
                continue

    def stop(self):
        # 设置running属性为False
        self.running = False
        # 调用writer的close方法
        self.writer.close()

# ========== UI 主界面 ==========
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口标题
        self.setWindowTitle("多通道实时数据采集系统")
        # 设置窗口大小
        self.resize(600, 400)

        # 创建垂直布局
        layout = QVBoxLayout(self)
        # 创建标签
        self.label = QLabel("最近帧数据：")
        # 创建表格
        self.table = QTableWidget(0, 4)
        # 设置表格表头
        self.table.setHorizontalHeaderLabels(["Channel", "ID", "Value", "Status"])

        # 将标签和表格添加到布局中
        layout.addWidget(self.label)
        layout.addWidget(self.table)

        # 创建两个队列
        self.raw_queue = queue.Queue()
        self.write_queue = queue.Queue()


        # 获取协议文件路径
        protocol_path = Path('C:/Users/10062/Videos/Desktop/PyUtilDemos/BusDataMonitor/protocol.json')
        # 创建协议解码器
        self.decoder = ProtocolDecoder(protocol_path)
        # 创建HDFWriter
        self.writer = HDFWriter("multi_channel_demo.h5")

        # 创建数据采集器列表
        self.collectors = []
        # 创建通道列表
        self.channels = ["ch0", "ch1"]
        # 遍历通道列表，创建数据采集器，并将数据采集器添加到采集器列表中
        for ch in self.channels:
            collector = DataCollector(ch, 20)
            # 将数据采集器的数据采集完成信号连接到raw_queue的put方法
            collector.data_collected.connect(self.raw_queue.put)
            # 启动数据采集器
            collector.start()
            # 将数据采集器添加到采集器列表中
            self.collectors.append(collector)

        # 创建解析线程和写入线程
        self.parser = ParserThread(self.raw_queue, self.write_queue, self.decoder)
        self.writer_thread = WriterThread(self.writer, self.write_queue)

        # 将解析线程的解析完成信号连接到update_table方法
        self.parser.parsed_signal.connect(self.update_table)

        # 启动解析线程和写入线程
        self.parser.start()
        self.writer_thread.start()

    # 更新表格方法
    def update_table(self, channel, parsed):
        # 在表格中插入一行
        self.table.insertRow(0)
        # 设置表格第一列的值为channel
        self.table.setItem(0, 0, QTableWidgetItem(channel))
        # 设置表格第二列的值为parsed的id
        self.table.setItem(0, 1, QTableWidgetItem(str(parsed.get("id"))))
        # 设置表格第三列的值为parsed的value
        self.table.setItem(0, 2, QTableWidgetItem(str(parsed.get("value"))))
        # 设置表格第四列的值为parsed的status
        self.table.setItem(0, 3, QTableWidgetItem(str(parsed.get("status"))))
        # 如果表格的行数大于50，则删除最后一行
        if self.table.rowCount() > 50:
            self.table.removeRow(self.table.rowCount() - 1)

    # 关闭事件方法
    def closeEvent(self, event):
        # 遍历采集器列表，停止并等待每个采集器
        for c in self.collectors:
            c.stop()
            c.wait()
        # 停止并等待解析线程和写入线程
        self.parser.stop()
        self.writer_thread.stop()
        self.parser.wait()
        self.writer_thread.wait()
        # 打印系统已关闭
        print("系统已关闭。")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
