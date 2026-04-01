"""配置管理 - 读写 JSON 配置文件"""

import json
import os

CONFIG_DIR = os.path.expanduser("~/Library/Application Support/RemindApp")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULTS = {
    "interval_minutes": 30,
    "recurring": True,
    "enabled": False,
    "notification_type": "banner",  # "banner" or "overlay"
    "sound_enabled": True,
    "sound_name": "Ping",
    "use_random_template": True,
    "selected_template_key": "neck",
    "custom_message": "",
    "tts_enabled": False,
    "tts_voice": "Tingting",
}


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._load()
        return cls._instance

    def _load(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data = {**DEFAULTS, **saved}
            except (json.JSONDecodeError, OSError):
                self._data = dict(DEFAULTS)
        else:
            self._data = dict(DEFAULTS)

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def get(self, key):
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value
        self.save()
