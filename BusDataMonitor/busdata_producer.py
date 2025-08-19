import threading
import time
import random
import queue
from datetime import datetime
from abc import ABC, abstractmethod

class RS422ProducerBase(ABC):
    """
    RS422数据生产者抽象基类
    所有数据源必须实现 start/stop 接口
    """
    def __init__(self, tx_queue: queue.Queue, rx_queue: queue.Queue):
        self.tx_queue = tx_queue
        self.rx_queue = rx_queue

    @abstractmethod
    def start(self):
        """启动数据生产（线程/硬件驱动）"""
        pass

    @abstractmethod
    def stop(self):
        """停止数据生产"""
        pass


class RS422SimProducer(RS422ProducerBase):
    """
    模拟 RS422 数据采集线程 和 发送线程
    继承自 RS422ProducerBase 基类，实现了模拟 RS422 通信的发送和接收功能
    """
    def __init__(self, tx_queue, rx_queue, tx_period_ms=50, rx_period_ms=30):
        # 调用父类的初始化方法
        super().__init__(tx_queue, rx_queue)
        # 将发送周期从毫秒转换为秒
        self.tx_period = tx_period_ms / 1000.0
        # 将接收周期从毫秒转换为秒
        self.rx_period = rx_period_ms / 1000.0
        # 创建停止事件，用于控制线程的运行状态
        self._stop_event = threading.Event()
        # 初始化发送线程为 None
        self.tx_thread = None
        # 初始化接收线程为 None
        self.rx_thread = None

    def start(self):
        # 清除停止事件，表示线程可以运行
        self._stop_event.clear()
        # 创建发送线程，设置为守护线程
        self.tx_thread = threading.Thread(target=self._tx_loop, daemon=True)
        # 创建接收线程，设置为守护线程
        self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        # 启动发送线程
        self.tx_thread.start()
        # 启动接收线程
        self.rx_thread.start()

    def stop(self):
        # 设置停止事件，通知线程应该停止运行
        self._stop_event.set()
        # 如果发送线程存在，则等待其结束，最多等待1秒
        if self.tx_thread:
            self.tx_thread.join(timeout=1.0)
        # 如果接收线程存在，则等待其结束，最多等待1秒
        if self.rx_thread:
            self.rx_thread.join(timeout=1.0)

    def _now_str(self):
        # 获取当前时间并格式化为 "时:分:秒.毫秒" 的字符串格式
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _rand_frame(self, length=8):
        # 生成指定长度的随机字节序列，默认长度为8字节
        return bytes(random.randint(0, 255) for _ in range(length))

    def _format_hex(self, data: bytes):
        # 将字节数据格式化为十六进制字符串表示，每个字节用两个十六进制数表示，字节间用空格分隔
        return " ".join(f"{b:02X}" for b in data)

    def _tx_loop(self):
        # 发送线程的主循环，直到停止事件被设置
        while not self._stop_event.is_set():
            # 获取当前时间戳
            ts = self._now_str()
            # 生成随机数据帧
            frame = self._rand_frame()
            # 将数据帧格式化为十六进制字符串
            hex_str = self._format_hex(frame)
            try:
                # 尝试将数据放入发送队列，不阻塞
                self.tx_queue.put_nowait((ts, hex_str))
            except queue.Full:
                # 如果队列已满，则忽略异常
                pass
            # 按照设定的发送周期休眠
            time.sleep(self.tx_period)

    def _rx_loop(self):
        # 接收线程的主循环，直到停止事件被设置
        while not self._stop_event.is_set():
            # 获取当前时间戳
            ts = self._now_str()
            # 生成随机数据帧
            frame = self._rand_frame()
            # 将数据帧格式化为十六进制字符串
            hex_str = self._format_hex(frame)
            try:
                # 尝试将数据放入接收队列，不阻塞
                self.rx_queue.put_nowait((ts, hex_str))
            except queue.Full:
                # 如果队列已满，则忽略异常
                pass
            # 按照设定的接收周期休眠
            time.sleep(self.rx_period)


class RS422RealProducer(RS422ProducerBase):
    """
    未来接入真实RS422硬件时使用此类
    在start()中启动硬件读写线程，在stop()中释放资源
    """
    def __init__(self, tx_queue, rx_queue, device_config):
        super().__init__(tx_queue, rx_queue)
        self.device_config = device_config
        self._stop_event = threading.Event()
        self.rx_thread = None
        self.tx_thread = None
        # 根据实际需求保存句柄，例如 self.dev = open_device(device_config)

    def start(self):

        """
        启动通信线程
        此方法用于启动接收和发送数据的线程
        """
        self._stop_event.clear()  # 清除停止事件，允许线程运行
        # 启动实际硬件接收线程
        self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)  # 创建接收数据线程，设置为守护线程
        self.tx_thread = threading.Thread(target=self._tx_loop, daemon=True)  # 创建发送数据线程，设置为守护线程
        self.rx_thread.start()  # 启动接收线程
        self.tx_thread.start()  # 启动发送线程

    def stop(self):
        self._stop_event.set()
        if self.rx_thread:
            self.rx_thread.join(timeout=1.0)
        if self.tx_thread:
            self.tx_thread.join(timeout=1.0)
        # 释放硬件资源
        # close_device(self.dev)

    def _rx_loop(self):
        """从真实硬件读取数据"""
        while not self._stop_event.is_set():
            # 这里替换为实际DLL或串口读取
            # data = read_from_device()
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            data = bytes([0x55]*8)  # 占位：真实数据
            hex_str = " ".join(f"{b:02X}" for b in data)
            try:
                self.rx_queue.put_nowait((ts, hex_str))
            except queue.Full:
                pass
            time.sleep(0.05)  # 模拟硬件延迟

    def _tx_loop(self):
        """从应用层获取发送帧并写入硬件"""
        while not self._stop_event.is_set():
            # 如果有独立的发送数据通道，可在此读取应用待发送帧
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            data = bytes([0xAA]*8)  # 占位：真实发送数据
            hex_str = " ".join(f"{b:02X}" for b in data)
            try:
                self.tx_queue.put_nowait((ts, hex_str))
            except queue.Full:
                pass
            time.sleep(0.05)
