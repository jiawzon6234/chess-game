"""負責把棋盤狀態畫到 Pygame 視窗上。

若 assets/images/ 底下有對應的棋子圖片(檔名如 wK.png、bQ.png)，
會優先使用圖片；否則退回使用「圓圈+字母」的簡易佔位圖形，
方便在還沒準備美術素材前就能開發與測試。
"""

import os

import pygame

from .. import constants as C
from ..pieces import Color

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images")


def load_piece_images() -> dict:
    """嘗試載入 assets/images/ 底下的棋子圖片。找不到就略過，回傳空字典。"""
    images = {}
    if not os.path.isdir(ASSET_DIR):
        return images

    color_prefix = {Color.WHITE: "w", Color.BLACK: "b"}
    for color, prefix in color_prefix.items():
        for symbol in ("P", "N", "B", "R", "Q", "K"):
            path = os.path.join(ASSET_DIR, f"{prefix}{symbol}.png")
            if os.path.isfile(path):
                try:
                    image = pygame.image.load(path).convert_alpha()
                    image = pygame.transform.smoothscale(
                        image, (C.SQUARE_SIZE, C.SQUARE_SIZE)
                    )
                    images[(color, symbol)] = image
                except pygame.error:
                    continue
    return images


class Renderer:
    def __init__(self, screen: "pygame.Surface"):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", int(C.SQUARE_SIZE * 0.46), bold=True)
        self.images = load_piece_images()

    def draw_board(self) -> None:
        for row in range(C.BOARD_SIZE):
            for col in range(C.BOARD_SIZE):
                color = C.LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else C.DARK_SQUARE_COLOR
                rect = pygame.Rect(
                    col * C.SQUARE_SIZE, row * C.SQUARE_SIZE, C.SQUARE_SIZE, C.SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, color, rect)

    def highlight_squares(self, positions, rgb_color, alpha: int = 140) -> None:
        for row, col in positions:
            rect = pygame.Rect(
                col * C.SQUARE_SIZE, row * C.SQUARE_SIZE, C.SQUARE_SIZE, C.SQUARE_SIZE
            )
            overlay = pygame.Surface((C.SQUARE_SIZE, C.SQUARE_SIZE), pygame.SRCALPHA)
            overlay.fill((*rgb_color, alpha))
            self.screen.blit(overlay, rect)

    def draw_pieces(self, board) -> None:
        for row in range(C.BOARD_SIZE):
            for col in range(C.BOARD_SIZE):
                piece = board.grid[row][col]
                if piece is None:
                    continue
                x, y = col * C.SQUARE_SIZE, row * C.SQUARE_SIZE
                key = (piece.color, piece.type.value)
                if key in self.images:
                    self.screen.blit(self.images[key], (x, y))
                else:
                    self._draw_placeholder_piece(piece, x, y)

    def _draw_placeholder_piece(self, piece, x: int, y: int) -> None:
        center = (x + C.SQUARE_SIZE // 2, y + C.SQUARE_SIZE // 2)
        radius = int(C.SQUARE_SIZE * 0.38)
        fill_color = C.WHITE_PIECE_FILL if piece.color is Color.WHITE else C.BLACK_PIECE_FILL
        text_color = (20, 20, 20) if piece.color is Color.WHITE else (245, 245, 245)

        pygame.draw.circle(self.screen, fill_color, center, radius)
        pygame.draw.circle(self.screen, C.PIECE_OUTLINE_COLOR, center, radius, 2)

        label = self.font.render(piece.type.value, True, text_color)
        label_rect = label.get_rect(center=center)
        self.screen.blit(label, label_rect)
