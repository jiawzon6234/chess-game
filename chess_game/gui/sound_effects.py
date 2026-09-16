"""音效載入與播放：按鈕、走棋、重新開始、棋局結束。"""

import os

import pygame

SFX_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "audio", "sfx")

_SOUND_FILES = {
    "click": "click.ogg",
    "move": "move.ogg",
    "restart": "restart.ogg",
    "game_over": "game_over.ogg",
}


class SoundEffects:
    """管理遊戲內的短音效；找不到音效裝置或檔案時，播放呼叫會靜默略過。"""

    def __init__(self):
        self._sounds: dict = {}
        if not pygame.mixer.get_init():
            return
        for name, filename in _SOUND_FILES.items():
            path = os.path.join(SFX_DIR, filename)
            if not os.path.isfile(path):
                continue
            try:
                self._sounds[name] = pygame.mixer.Sound(path)
            except pygame.error:
                continue

    def set_volume(self, volume_ratio: float) -> None:
        for sound in self._sounds.values():
            sound.set_volume(volume_ratio)

    def _play(self, name: str) -> None:
        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()

    def play_click(self) -> None:
        self._play("click")

    def play_move(self) -> None:
        self._play("move")

    def play_restart(self) -> None:
        self._play("restart")

    def play_game_over(self) -> None:
        self._play("game_over")
