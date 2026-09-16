"""提供能正確顯示中文字的字型，避免預設字型（如 Arial）顯示成亂碼／方框。"""

import pygame

# 依序嘗試的候選字型（Windows 常見的中文字型，找不到則自動略過）。
_CJK_FONT_CANDIDATES = [
    "microsoftjhenghei",
    "microsoftjhengheiui",
    "microsoftyahei",
    "microsoftyaheiui",
    "simsun",
    "mingliu",
    "notosanstc",
    "notosanshk",
    "arial",
]


def get_font(size: int, bold: bool = False) -> "pygame.font.Font":
    """回傳可顯示中文字的字型；系統缺少對應字型時退回 pygame 預設字型。"""
    return pygame.font.SysFont(_CJK_FONT_CANDIDATES, size, bold=bold)
