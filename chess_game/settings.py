"""遊戲設定（音樂音量、音效音量）的載入、儲存與套用。"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "settings.json")

DEFAULT_VOLUME = 100


class Settings:
    def __init__(self, music_volume: int = DEFAULT_VOLUME, sfx_volume: int = DEFAULT_VOLUME):
        self.music_volume = max(0, min(100, music_volume))
        self.sfx_volume = max(0, min(100, sfx_volume))

    @property
    def music_volume_ratio(self) -> float:
        """回傳 0.0 ~ 1.0 之間的音樂音量比例，供 pygame.mixer.music 使用。"""
        return self.music_volume / 100

    @property
    def sfx_volume_ratio(self) -> float:
        """回傳 0.0 ~ 1.0 之間的音效音量比例，供 pygame.mixer.Sound 使用。"""
        return self.sfx_volume / 100

    def apply(self) -> None:
        """將目前音樂音量套用到 pygame 音效系統（尚未初始化音效裝置時略過）。"""
        import pygame

        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.music_volume_ratio)

    def save(self) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"music_volume": self.music_volume, "sfx_volume": self.sfx_volume}, f)
        except OSError:
            pass

    @classmethod
    def load(cls) -> "Settings":
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            music_volume = int(data.get("music_volume", DEFAULT_VOLUME))
            sfx_volume = int(data.get("sfx_volume", DEFAULT_VOLUME))
        except (OSError, ValueError, json.JSONDecodeError):
            music_volume = DEFAULT_VOLUME
            sfx_volume = DEFAULT_VOLUME
        return cls(music_volume=music_volume, sfx_volume=sfx_volume)
