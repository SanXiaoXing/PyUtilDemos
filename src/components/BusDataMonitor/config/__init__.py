"""
功能描述：配置信息
"""



import json
from pathlib import Path

# ===== 路径定义 =====
BASE_DIR = Path(__file__).parent
CHANNEL_CONFIG_PATH = BASE_DIR / "channel_config.json"
PROTOCOL_CONFIG_PATH = BASE_DIR / "protocol_info.json"

# ===== 全局变量 =====
channel_config = {}
protocol_config = {}

# ===== 内部函数 =====
def _load_json(file_path: Path) -> dict:
    """安全读取 JSON 文件"""
    if not file_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"配置文件解析失败: {file_path}\n错误信息: {e}")

# ===== 初始化加载 =====
def _init_configs():
    global channel_config, protocol_config
    channel_config = _load_json(CHANNEL_CONFIG_PATH)
    protocol_config = _load_json(PROTOCOL_CONFIG_PATH)

# ===== 提供刷新接口 =====
def reload_configs():
    """重新加载配置文件"""
    _init_configs()

# 初始化时加载
_init_configs()