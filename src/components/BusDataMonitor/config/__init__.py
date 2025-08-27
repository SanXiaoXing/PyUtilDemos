from pathlib import Path
import json

BASE_DIR = Path(__file__).parent
CHANNEL_CONFIG_PATH = BASE_DIR / "channel_config.json"
PROTOCOL_CONFIG_PATH = BASE_DIR / "protocol_config.json"

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

channel_config = _load_json(CHANNEL_CONFIG_PATH)
protocol_config = _load_json(PROTOCOL_CONFIG_PATH)

def reload_configs():
    global channel_config, protocol_config
    channel_config = _load_json(CHANNEL_CONFIG_PATH)
    protocol_config = _load_json(PROTOCOL_CONFIG_PATH)

def save_channel_config():
    _write_json(CHANNEL_CONFIG_PATH, channel_config)
