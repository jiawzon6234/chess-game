"""遊戲設定（目前僅音量）的載入、儲存與套用。"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "settings.json")

DEFAULT_VOLUME = 100


class Settings:
    def __init__(self, volume: int = DEFAULT_VOLUME):
        self.volume = max(0, min(100, volume))

    @property
    def volume_ratio(self) -> float:
        """回傳 0.0 ~ 1.0 之間的音量比例，供 pygame.mixer 使用。"""
        return self.volume / 100

    def apply(self) -> None:
        """將目前音量套用到 pygame 音效系統（尚未初始化音效裝置時略過）。"""
        import pygame

        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume_ratio)

    def save(self) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"volume": self.volume}, f)
        except OSError:
            pass

    @classmethod
    def load(cls) -> "Settings":
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            volume = int(data.get("volume", DEFAULT_VOLUME))
        except (OSError, ValueError, json.JSONDecodeError):
            volume = DEFAULT_VOLUME
        return cls(volume=volume)
