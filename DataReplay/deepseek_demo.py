"""
deepseek写的分块加载demo(准备参考)
"""


import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal

class CSVLoader(QThread):
    """后台分块加载线程"""
    data_chunk_loaded = pyqtSignal(pd.DataFrame, int)  # 信号：数据块加载完成
    loading_finished = pyqtSignal()  # 信号：全部加载完成
    
    def __init__(self, file_path, chunk_size=10000):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.total_chunks = 0
    
    def run(self):
        # 分块读取CSV
        chunk_reader = pd.read_csv(
            self.file_path,
            chunksize=self.chunk_size,
            parse_dates=['timestamp']  # 自动解析时间戳列
        )
        
        # 逐块处理数据
        for i, chunk in enumerate(chunk_reader):
            # 预处理：处理缺失值
            chunk.fillna(method='ffill', inplace=True)  
            self.data_chunk_loaded.emit(chunk, i)
            self.total_chunks = i + 1
        
        self.loading_finished.emit()




class DataReplayManager:
    def __init__(self):
        self.active_chunks = {}  # 当前活跃数据块 {chunk_id: DataFrame}
        self.max_active_chunks = 5  # 最大缓存块数
        
    def add_chunk(self, chunk, chunk_id):
        """添加新数据块并管理内存"""
        # 添加新块
        self.active_chunks[chunk_id] = chunk
        
        # 内存清理：移除最旧块
        if len(self.active_chunks) > self.max_active_chunks:
            oldest_id = min(self.active_chunks.keys())
            del self.active_chunks[oldest_id]
            
    def get_data_range(self, start_idx, end_idx):
        """获取指定索引范围的数据"""
        result = pd.DataFrame()
        
        # 合并所需数据块
        for chunk_id, chunk in self.active_chunks.items():
            chunk_start = chunk_id * self.chunk_size
            chunk_end = chunk_start + len(chunk)
            
            if chunk_end > start_idx and chunk_start < end_idx:
                # 计算切片范围
                local_start = max(0, start_idx - chunk_start)
                local_end = min(len(chunk), end_idx - chunk_start)
                
                # 拼接数据
                result = pd.concat([result, chunk.iloc[local_start:local_end]])
        
        return result
    

class DataReplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化加载器
        self.loader_thread = CSVLoader("large_file.csv")
        self.data_manager = DataReplayManager()
        
        # 连接信号
        self.loader_thread.data_chunk_loaded.connect(self.handle_new_chunk)
        self.loader_thread.loading_finished.connect(self.on_loading_complete)
        
    def start_loading(self):
        """开始加载文件"""
        self.loader_thread.start()
        self.statusBar().showMessage("分块加载中...")
        
    def handle_new_chunk(self, chunk, chunk_id):
        """处理新加载的数据块"""
        self.data_manager.add_chunk(chunk, chunk_id)
        self.update_progress(chunk_id)
        
        # 如果是第一块数据，初始化视图
        if chunk_id == 0:
            self.init_plot(chunk)
    
    def update_plot(self, current_time):
        """更新当前视图数据"""
        # 计算需要的数据范围 (示例)
        start_idx = int(current_time - 10)  # 显示前10秒数据
        end_idx = int(current_time + 10)    # 显示后10秒数据
        
        visible_data = self.data_manager.get_data_range(start_idx, end_idx)
        self.plot_widget.update_data(visible_data)



replayer = DataReplayWindow()
replayer.start_loading("sensor_data_10GB.csv")
replayer.show()