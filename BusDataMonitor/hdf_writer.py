import h5py
import threading
import time
import random
import os
from collections import defaultdict

class HDFWriter:
    def __init__(self, filename, flush_interval=5, flush_every_n=None):
        self.file = h5py.File(filename, 'w')
        self.lock = threading.Lock()

        self.flush_interval = flush_interval
        self.flush_every_n = flush_every_n
        self.write_count_since_flush = 0

        self.total_write_count = 0
        self.channel_write_counts = defaultdict(int)

        self._stop_event = threading.Event()
        if flush_interval:
            self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
            self.flush_thread.start()

    def write_frame(self, channel, timestamp, raw_data, parsed_data=None):
        with self.lock:
            grp = self.file.require_group(f"/data/{channel}")

            raw_dset = grp.require_dataset(
                "raw", shape=(0,), maxshape=(None,), dtype=h5py.vlen_dtype(bytes), exact=False
            )
            ts_dset = grp.require_dataset(
                "timestamp", shape=(0,), maxshape=(None,), dtype='f8', exact=False
            )

            if parsed_data is not None:
                parsed_dset = grp.require_dataset(
                    "parsed", shape=(0,), maxshape=(None,), dtype=h5py.string_dtype('utf-8'), exact=False
                )
            else:
                parsed_dset = None

            idx = raw_dset.shape[0]
            raw_dset.resize((idx + 1,))
            ts_dset.resize((idx + 1,))
            raw_dset[idx] = raw_data
            ts_dset[idx] = timestamp
            if parsed_dset is not None:
                parsed_dset.resize((idx + 1,))
                parsed_dset[idx] = parsed_data

            # 更新写入计数
            self.total_write_count += 1
            self.channel_write_counts[channel] += 1
            self.write_count_since_flush += 1

            # 条数阈值触发 flush
            if self.flush_every_n and self.write_count_since_flush >= self.flush_every_n:
                self.flush()
                self.write_count_since_flush = 0

    def flush(self):
        with self.lock:
            self.file.flush()
            print(f"[{time.strftime('%H:%M:%S')}] Flushed to disk. Total writes: {self.total_write_count}")

    def _flush_worker(self):
        while not self._stop_event.wait(self.flush_interval):
            self.flush()

    def get_stats(self):
        with self.lock:
            # 返回一个深拷贝，避免外部修改内部状态
            return {
                "total": self.total_write_count,
                "per_channel": dict(self.channel_write_counts)
            }

    def close(self):
        self._stop_event.set()
        if self.flush_interval:
            self.flush_thread.join()
        self.flush()
        self.file.close()
        print("HDF5 文件已关闭。")

# =====================
# 示例：写入模拟数据 + 打印监控信息
# =====================
def simulate_data_write(writer, channel_id):
    for i in range(10):
        timestamp = time.time()
        raw_data = os.urandom(8)
        parsed_data = f"CH{channel_id} Frame-{i}"
        writer.write_frame(f"ch{channel_id}", timestamp, raw_data, parsed_data)
        time.sleep(random.uniform(0.05, 0.3))

if __name__ == "__main__":
    writer = HDFWriter("demo_data_stats.h5", flush_interval=5, flush_every_n=7)

    threads = []
    for ch in range(3):
        t = threading.Thread(target=simulate_data_write, args=(writer, ch))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    stats = writer.get_stats()
    print("\n📊 最终写入统计:")
    print(f"总写入帧数: {stats['total']}")
    for ch, count in stats["per_channel"].items():
        print(f"通道 {ch}: {count} 帧")

    writer.close()
