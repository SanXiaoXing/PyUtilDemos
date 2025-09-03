import threading, time, random, queue, json
from datetime import datetime
from abc import ABC, abstractmethod
from ..config import protocol_config

class RS422ProducerBase(ABC):
    """RS422 数据生产者抽象基类（一个方向：Tx 或 Rx）"""
    def __init__(self, ch_id: str, q: queue.Queue, tor: str, freq: float,protocol:dict):
        self.ch_id = ch_id
        self.queue = q
        self.tor = tor  # "Tx" 或 "Rx"
        self.period = 1.0 / freq
        self.protocol=protocol
        self._stop_event = threading.Event()
        self.thread = None

    @abstractmethod
    def _loop(self):
        pass

    def start(self):
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=1.0)


class RS422SimProducer(RS422ProducerBase):
    """模拟 RS422 通信通道"""
    def _now_str(self):
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _rand_frame(self, length):
        return bytes(random.randint(0, 255) for _ in range(length))

    def _format_hex(self, data: bytes):
        return " ".join(f"{b:02X}" for b in data)

    def _loop(self):
        protocol_name=self.protocol[self.tor]
        protocol=protocol_config[protocol_name]
        frame_len=protocol['length']

        while not self._stop_event.is_set():
            ts = self._now_str()
            frame = self._rand_frame(frame_len)
            hex_str = self._format_hex(frame)
            try:
                self.queue.put_nowait((ts, self.tor, hex_str))
            except queue.Full:
                pass
            time.sleep(self.period)


class RS422RealProducer(RS422ProducerBase):
    """真实板卡 RS422 通信通道（占位示例）"""
    def __init__(self, ch_id, q, tor, freq, settings):
        super().__init__(ch_id, q, tor, freq)
        self.settings = settings
        # self.dev = open_device(settings) # 实际硬件初始化

    def _loop(self):
        """"模拟数据读取，需替换为实际数据读取逻辑"""
        data = bytes([0xAA]*8) if self.tor.lower()=="tx" else bytes([0x55]*8)
        while not self._stop_event.is_set():
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_str = " ".join(f"{b:02X}" for b in data)
            try:
                self.queue.put_nowait((ts, self.tor, hex_str))
            except queue.Full:
                pass
            time.sleep(self.period)


class RS422Manager:
    """管理所有 RS422 通道：自动读取配置文件并启动对应 Producer"""
    def __init__(self, config: str, use_sim=True):
        
        self.config = config

        self.use_sim = use_sim
        self.producers = {}  # ch_id -> list of producers
        self.queues = {}     # ch_id -> queue.Queue

        ProducerClass = RS422SimProducer if self.use_sim else RS422RealProducer

        for ch_id, cfg in self.config.items():
            q = queue.Queue(maxsize=10000)
            self.queues[ch_id] = q
            self.producers[ch_id] = []

            tor_cfg = cfg["TorR"]
            freq = cfg["freq"]
            protocol=cfg['protocol']
            
            # 如果是单方向
            if tor_cfg in ("Tx", "Rx"):
                if self.use_sim:
                    p = ProducerClass(ch_id, q, tor_cfg, freq,protocol)
                else:
                    p = ProducerClass(ch_id, q, tor_cfg, freq, cfg["settings"],protocol)
                self.producers[ch_id].append(p)

            # 如果是双向（Tx/Rx）
            elif tor_cfg == "Tx/Rx":
                for tor in ("Tx", "Rx"):
                    if self.use_sim:
                        p = ProducerClass(ch_id, q, tor, freq,protocol)
                    else:
                        p = ProducerClass(ch_id, q, tor, freq, cfg["settings"],protocol)
                    self.producers[ch_id].append(p)
            else:
                raise ValueError(f"Invalid TorR: {tor_cfg}")

    def start_all(self):
        for plist in self.producers.values():
            for p in plist:
                p.start()

    def stop_all(self):
        for plist in self.producers.values():
            for p in plist:
                p.stop()
