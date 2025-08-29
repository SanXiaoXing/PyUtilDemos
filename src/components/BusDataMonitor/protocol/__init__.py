import json
from pathlib import Path

PROTOCOL_PATH = Path(__file__).parent


class ProtocolLoader:
    def __init__(self):
        self.directory_path = PROTOCOL_PATH
        self._cache = {}  # 已加载的协议
        if not PROTOCOL_PATH.exists() or not PROTOCOL_PATH.is_dir():
            raise FileNotFoundError(f"Directory not found: {PROTOCOL_PATH}")

    def get(self, name: str):
        """按协议名（不含扩展名）获取 JSON 数据"""
        if name in self._cache:
            return self._cache[name]

        file_path = self.directory_path / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Protocol file not found: {file_path}")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[name] = data
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")

    def list_protocols(self):
        """列出目录下所有可用的协议文件名（不含扩展名）"""
        return [p.stem for p in self.directory_path.glob("*.json")]



