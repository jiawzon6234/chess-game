"""Pygame 主程式：開始畫面、設定畫面，以及棋盤事件迴圈與畫面繪製。"""

import os
import sys
from enum import Enum, auto

import pygame

from .. import constants as C
from ..board import Board
from ..engine import EngineError, UciEngine
from ..game import Game, GameStatus
from ..pieces import Color, PieceType, PROMOTION_CHOICES
from ..settings import Settings
from .fonts import get_font
from .renderer import Renderer
from .screens import Button, Slider
from .sound_effects import SoundEffects

# 背景音樂素材（CC0 授權，來源見 assets/audio/README.md）。
MUSIC_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "audio", "background_music.ogg"
)

# 開始畫面背景圖（程序繪製產生，見 assets/images/README.md）。
MENU_BACKGROUND_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "images", "menu_background.png"
)


class Screen(Enum):
    MENU = auto()
    SETTINGS = auto()
    GAME_OPTIONS = auto()
    PLAYING = auto()


# 持棋時間選項：(顯示文字, 秒數)，None 代表無限制。
TIME_LIMIT_OPTIONS = (("5 分鐘", 300), ("15 分鐘", 900), ("無限制", None))

# 對戰模式：(顯示文字, 模式代碼)。
GAME_MODE_OPTIONS = (("人 vs 人", "pvp"), ("人 vs 電腦", "pve"))

# 先後手：(顯示文字, 玩家執子顏色)。
HUMAN_COLOR_OPTIONS = (("先手（白方）", Color.WHITE), ("後手（黑方）", Color.BLACK))

# 電腦難度：(顯示文字, {skill_level, movetime_ms})，對應 Stockfish 的
# Skill Level（0~20）與思考時間，數字越大電腦越強。
DIFFICULTY_OPTIONS = (
    ("簡單", {"skill_level": 3, "movetime_ms": 300}),
    ("普通", {"skill_level": 10, "movetime_ms": 800}),
    ("困難", {"skill_level": 20, "movetime_ms": 1500}),
)

_UCI_PROMOTION_PIECE_TYPES = {
    "q": PieceType.QUEEN,
    "r": PieceType.ROOK,
    "b": PieceType.BISHOP,
    "n": PieceType.KNIGHT,
}


def _parse_uci_move(move_uci: str) -> tuple:
    """把引擎回傳的 UCI 走法字串（如 'e2e4'、'e7e8q'）解析成
    (from_pos, to_pos, promotion)。"""
    from_pos = Board.square_to_pos(move_uci[0:2])
    to_pos = Board.square_to_pos(move_uci[2:4])
    promotion = _UCI_PROMOTION_PIECE_TYPES.get(move_uci[4]) if len(move_uci) >= 5 else None
    return from_pos, to_pos, promotion


# ---- 對局設定畫面的版面座標（同時供按鈕建立與標籤繪製使用）----
_OPT_MODE_LABEL_Y = 118
_OPT_MODE_BUTTON_Y, _OPT_MODE_BUTTON_H = 142, 48
_OPT_COLOR_LABEL_Y = 222
_OPT_COLOR_BUTTON_Y, _OPT_COLOR_BUTTON_H = 246, 44
_OPT_DIFF_LABEL_Y = 318
_OPT_DIFF_BUTTON_Y, _OPT_DIFF_BUTTON_H = 342, 44
_OPT_TIME_LABEL_Y = 414
_OPT_TIME_BUTTON_Y, _OPT_TIME_BUTTON_H = 438, 50
_OPT_UNDO_LABEL_Y = 514
_OPT_UNDO_BUTTON_Y, _OPT_UNDO_BUTTON_H = 536, 46
_OPT_BOTTOM_BUTTON_Y, _OPT_BOTTOM_BUTTON_H = 632, 56


def _start_background_music(settings: Settings) -> None:
    """載入並循環播放背景音樂；找不到音效裝置或音檔時靜默略過。"""
    if not pygame.mixer.get_init() or not os.path.isfile(MUSIC_PATH):
        return
    try:
        pygame.mixer.music.load(MUSIC_PATH)
        pygame.mixer.music.set_volume(settings.music_volume_ratio)
        pygame.mixer.music.play(loops=-1)
    except pygame.error:
        pass


def _pos_from_mouse(mouse_pos: tuple) -> tuple:
    x, y = mouse_pos
    return (y // C.SQUARE_SIZE, x // C.SQUARE_SIZE)


def _hints_text(undo_enabled: bool) -> str:
    parts = ["按 R 重新開始"]
    if undo_enabled:
        parts.append("Ctrl+Z 悔棋")
    parts.append("Esc 回主選單")
    return "，".join(parts)


def _status_text(game: Game, undo_enabled: bool) -> str:
    hints = _hints_text(undo_enabled)
    turn_name = "白方" if game.turn.value == "white" else "黑方"
    if game.status == GameStatus.CHECKMATE:
        winner_name = "白方" if game.winner.value == "white" else "黑方"
        return f"Chess Game - 將死！{winner_name}獲勝（{hints}）"
    if game.status == GameStatus.STALEMATE:
        return f"Chess Game - 和棋（逼和，{hints}）"
    if game.status == GameStatus.DRAW_BY_REPETITION:
        return f"Chess Game - 和棋（三次重複局面，{hints}）"
    if game.status == GameStatus.DRAW_BY_FIFTY_MOVE_RULE:
        return f"Chess Game - 和棋（50 手和局規則，{hints}）"
    if game.status == GameStatus.TIMEOUT:
        winner_name = "白方" if game.winner.value == "white" else "黑方"
        loser_name = "黑方" if game.winner.value == "white" else "白方"
        return f"Chess Game - {loser_name}時間到！{winner_name}獲勝（{hints}）"
    return f"Chess Game - 輪到{turn_name}走棋（{hints}）"


def _format_clock_time(seconds: float) -> str:
    if seconds == float("inf"):
        return "∞"
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


MARGIN_PADDING = 18


def _clock_time_color(game: Game, color: Color) -> tuple:
    remaining = game.clock.remaining[color]
    active_color = game.turn if not game.is_game_over() else None
    if remaining <= C.CLOCK_LOW_TIME_THRESHOLD_SECONDS:
        return C.CLOCK_LOW_TIME_COLOR
    if color is active_color:
        return C.CLOCK_ACTIVE_TEXT_COLOR
    return C.CLOCK_TEXT_COLOR


def _draw_black_clock(screen, clock_font, tiny_font, game: Game) -> None:
    """黑方西洋棋鐘：畫在左側留白區的左上角。"""
    label_surface = tiny_font.render("黑方", True, C.HINT_TITLE_COLOR)
    label_rect = label_surface.get_rect(topleft=(MARGIN_PADDING, MARGIN_PADDING))
    screen.blit(label_surface, label_rect)

    time_text = _format_clock_time(game.clock.remaining[Color.BLACK])
    time_surface = clock_font.render(time_text, True, _clock_time_color(game, Color.BLACK))
    time_rect = time_surface.get_rect(topleft=(MARGIN_PADDING, label_rect.bottom + 4))
    screen.blit(time_surface, time_rect)


def _draw_white_clock(screen, clock_font, tiny_font, game: Game) -> None:
    """白方西洋棋鐘：畫在右側留白區的右下角。"""
    right_x = C.WINDOW_WIDTH - MARGIN_PADDING

    time_text = _format_clock_time(game.clock.remaining[Color.WHITE])
    time_surface = clock_font.render(time_text, True, _clock_time_color(game, Color.WHITE))
    time_rect = time_surface.get_rect(bottomright=(right_x, C.WINDOW_HEIGHT - MARGIN_PADDING))
    screen.blit(time_surface, time_rect)

    label_surface = tiny_font.render("白方", True, C.HINT_TITLE_COLOR)
    label_rect = label_surface.get_rect(bottomright=(right_x, time_rect.top - 4))
    screen.blit(label_surface, label_rect)


def _draw_shortcut_hints(screen, tiny_font, undo_enabled: bool) -> None:
    """快捷鍵提示：畫在右側留白區的右上角。"""
    lines = ["快捷鍵", "R 重新開始"]
    if undo_enabled:
        lines.append("Ctrl+Z 悔棋")
    lines.append("Esc 回主選單")

    left_x = C.SIDE_MARGIN_WIDTH + C.WINDOW_SIZE + MARGIN_PADDING
    y = MARGIN_PADDING
    for i, line in enumerate(lines):
        color = C.HINT_TITLE_COLOR if i == 0 else C.HINT_TEXT_COLOR
        surface = tiny_font.render(line, True, color)
        rect = surface.get_rect(topleft=(left_x, y))
        screen.blit(surface, rect)
        y = rect.bottom + 6


def _load_menu_background() -> "pygame.Surface | None":
    """載入開始畫面背景圖；找不到檔案時回傳 None，改用純色背景。"""
    if not os.path.isfile(MENU_BACKGROUND_PATH):
        return None
    try:
        image = pygame.image.load(MENU_BACKGROUND_PATH).convert()
        if image.get_size() != (C.WINDOW_SIZE, C.WINDOW_SIZE):
            image = pygame.transform.smoothscale(image, (C.WINDOW_SIZE, C.WINDOW_SIZE))
        return image
    except pygame.error:
        return None


def _draw_menu(
    screen, title_font, start_button, settings_button, background, mouse_pos
) -> None:
    if background is not None:
        screen.blit(background, (0, 0))
    else:
        screen.fill(C.MENU_BACKGROUND_COLOR)

    title_surface = title_font.render("CHESS", True, C.MENU_TITLE_COLOR)
    title_rect = title_surface.get_rect(center=(C.WINDOW_SIZE // 2, C.WINDOW_SIZE // 3))
    screen.blit(title_surface, title_rect)

    start_button.draw(screen, mouse_pos)
    settings_button.draw(screen, mouse_pos)


def _draw_settings(
    screen, title_font, label_font, music_slider, sfx_slider, back_button, mouse_pos
) -> None:
    screen.fill(C.MENU_BACKGROUND_COLOR)

    title_surface = title_font.render("設定", True, C.MENU_TITLE_COLOR)
    title_rect = title_surface.get_rect(center=(C.WINDOW_SIZE // 2, C.WINDOW_SIZE // 4))
    screen.blit(title_surface, title_rect)

    for slider, text in (
        (music_slider, f"音樂音量：{music_slider.value}"),
        (sfx_slider, f"音效音量：{sfx_slider.value}"),
    ):
        label_surface = label_font.render(text, True, C.BUTTON_TEXT_COLOR)
        label_rect = label_surface.get_rect(center=(C.WINDOW_SIZE // 2, slider.rect.y - 30))
        screen.blit(label_surface, label_rect)
        slider.draw(screen)

    back_button.draw(screen, mouse_pos)


def _draw_option_row(screen, label_font, label_text, y, buttons, selected_value, mouse_pos) -> None:
    """畫一列「標籤 + 一排可選按鈕」，buttons 為 [(value, Button), ...]。"""
    label_surface = label_font.render(label_text, True, C.BUTTON_TEXT_COLOR)
    label_rect = label_surface.get_rect(center=(C.WINDOW_SIZE // 2, y))
    screen.blit(label_surface, label_rect)

    for value, button in buttons:
        button.draw(screen, mouse_pos, selected=value == selected_value)


def _draw_game_options(
    screen,
    options_title_font,
    label_font,
    mode_buttons,
    color_buttons,
    difficulty_buttons,
    time_buttons,
    undo_toggle_button,
    confirm_button,
    back_button,
    selected_game_mode,
    selected_human_color,
    selected_difficulty_index,
    selected_time_limit_seconds,
    undo_enabled,
    game_options_error,
    mouse_pos,
) -> None:
    screen.fill(C.MENU_BACKGROUND_COLOR)
    vs_computer = selected_game_mode == "pve"

    title_surface = options_title_font.render("對局設定", True, C.MENU_TITLE_COLOR)
    title_rect = title_surface.get_rect(center=(C.WINDOW_SIZE // 2, 60))
    screen.blit(title_surface, title_rect)

    _draw_option_row(
        screen, label_font, "對戰模式", _OPT_MODE_LABEL_Y, mode_buttons, selected_game_mode,
        mouse_pos,
    )

    if vs_computer:
        _draw_option_row(
            screen, label_font, "先後手", _OPT_COLOR_LABEL_Y, color_buttons,
            selected_human_color, mouse_pos,
        )
        _draw_option_row(
            screen, label_font, "電腦難度", _OPT_DIFF_LABEL_Y, difficulty_buttons,
            selected_difficulty_index, mouse_pos,
        )

    time_label = label_font.render("持棋時間", True, C.BUTTON_TEXT_COLOR)
    time_label_rect = time_label.get_rect(center=(C.WINDOW_SIZE // 2, _OPT_TIME_LABEL_Y))
    screen.blit(time_label, time_label_rect)

    for seconds, button in time_buttons:
        is_selected = (not undo_enabled) and seconds == selected_time_limit_seconds
        button.draw(screen, mouse_pos, selected=is_selected, disabled=undo_enabled)

    undo_label = label_font.render("允許悔棋", True, C.BUTTON_TEXT_COLOR)
    undo_label_rect = undo_label.get_rect(center=(C.WINDOW_SIZE // 2, _OPT_UNDO_LABEL_Y))
    screen.blit(undo_label, undo_label_rect)

    undo_toggle_button.text = "開" if undo_enabled else "關"
    undo_toggle_button.draw(screen, mouse_pos, selected=undo_enabled)

    # 錯誤訊息與悔棋提示只會擇一顯示（都放在同一行位置），避免兩行文字
    # 疊在一起、甚至蓋到下方的返回/開始對局按鈕。錯誤訊息優先顯示。
    note_y = undo_toggle_button.rect.bottom + 20
    if game_options_error:
        error_surface = label_font.render(game_options_error, True, C.CLOCK_LOW_TIME_COLOR)
        max_width = C.WINDOW_SIZE - 40
        if error_surface.get_width() > max_width:
            scale = max_width / error_surface.get_width()
            error_surface = pygame.transform.smoothscale(
                error_surface,
                (max_width, max(1, int(error_surface.get_height() * scale))),
            )
        error_rect = error_surface.get_rect(center=(C.WINDOW_SIZE // 2, note_y))
        screen.blit(error_surface, error_rect)
    elif undo_enabled:
        note_surface = label_font.render(
            "（悔棋開啟時，持棋時間自動設為無限制）", True, C.HINT_TEXT_COLOR
        )
        note_rect = note_surface.get_rect(center=(C.WINDOW_SIZE // 2, note_y))
        screen.blit(note_surface, note_rect)

    back_button.draw(screen, mouse_pos)
    confirm_button.draw(screen, mouse_pos)


def _draw_promotion_popup(screen, renderer, label_font, color, promotion_rects, mouse_pos) -> None:
    overlay = pygame.Surface((C.WINDOW_SIZE, C.WINDOW_SIZE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    icon_rects = list(promotion_rects.values())
    title_height = 34
    padding = 20
    panel_rect = pygame.Rect(
        icon_rects[0].left - padding,
        icon_rects[0].top - padding - title_height,
        icon_rects[-1].right - icon_rects[0].left + padding * 2,
        icon_rects[0].height + padding * 2 + title_height,
    )
    pygame.draw.rect(screen, C.BUTTON_COLOR, panel_rect, border_radius=14)
    pygame.draw.rect(screen, C.BUTTON_TEXT_COLOR, panel_rect, 2, border_radius=14)

    title_surface = label_font.render("選擇升變棋子", True, C.BUTTON_TEXT_COLOR)
    title_rect = title_surface.get_rect(centerx=panel_rect.centerx, top=panel_rect.top + 8)
    screen.blit(title_surface, title_rect)

    for piece_type, rect in promotion_rects.items():
        hovered = rect.collidepoint(mouse_pos)
        bg_color = C.BUTTON_HOVER_COLOR if hovered else C.LIGHT_SQUARE_COLOR
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, C.BUTTON_TEXT_COLOR, rect, 2, border_radius=8)

        icon = renderer.render_piece_icon(color, piece_type, rect.width - 8)
        icon_rect = icon.get_rect(center=rect.center)
        screen.blit(icon, icon_rect)


def _draw_ai_thinking_overlay(screen, label_font) -> None:
    overlay = pygame.Surface((C.WINDOW_SIZE, C.WINDOW_SIZE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 90))
    screen.blit(overlay, (0, 0))

    text_surface = label_font.render("電腦思考中…", True, C.BUTTON_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=(C.WINDOW_SIZE // 2, C.WINDOW_SIZE // 2))
    panel_rect = text_rect.inflate(56, 32)
    pygame.draw.rect(screen, C.BUTTON_COLOR, panel_rect, border_radius=14)
    pygame.draw.rect(screen, C.BUTTON_TEXT_COLOR, panel_rect, 2, border_radius=14)
    screen.blit(text_surface, text_rect)


def _stop_engine(engine: "UciEngine | None") -> None:
    if engine is not None:
        try:
            engine.quit()
        except Exception:
            pass


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Chess Game")
    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    # 選單/設定/棋盤內容都畫在這張置中的正方形畫布上，兩側留白區直接畫在 screen 上。
    content = pygame.Surface((C.WINDOW_SIZE, C.WINDOW_SIZE))
    clock = pygame.time.Clock()

    settings = Settings.load()
    settings.apply()
    _start_background_music(settings)
    menu_background = _load_menu_background()

    sfx = SoundEffects()
    sfx.set_volume(settings.sfx_volume_ratio)

    title_font = get_font(int(C.WINDOW_SIZE * 0.1), bold=True)
    label_font = get_font(26)
    button_font = get_font(28, bold=True)
    clock_font = get_font(34, bold=True)
    tiny_font = get_font(18)
    options_title_font = get_font(46, bold=True)

    center_x = C.WINDOW_SIZE // 2
    button_width, button_height = 260, 64

    start_button = Button(
        pygame.Rect(
            center_x - button_width // 2,
            C.WINDOW_SIZE // 2,
            button_width,
            button_height,
        ),
        "進入遊戲",
        button_font,
    )
    settings_button = Button(
        pygame.Rect(
            center_x - button_width // 2,
            C.WINDOW_SIZE // 2 + button_height + 24,
            button_width,
            button_height,
        ),
        "設定",
        button_font,
    )
    back_button = Button(
        pygame.Rect(
            center_x - button_width // 2,
            C.WINDOW_SIZE - button_height - 60,
            button_width,
            button_height,
        ),
        "返回",
        button_font,
    )
    music_slider = Slider(
        pygame.Rect(center_x - 160, C.WINDOW_SIZE // 2 - 70, 320, 18),
        value=settings.music_volume,
    )
    sfx_slider = Slider(
        pygame.Rect(center_x - 160, C.WINDOW_SIZE // 2 + 40, 320, 18),
        value=settings.sfx_volume,
    )

    option_button_font = get_font(22, bold=True)

    def _build_option_row(options, y, height, font=option_button_font):
        """依 (顯示文字, 值) 列表建立一排等寬、置中排列的 Button，回傳 [(值, Button), ...]。"""
        width = max(140, min(190, (C.WINDOW_SIZE - 80) // len(options) - 16))
        gap = 16
        total_width = len(options) * width + (len(options) - 1) * gap
        start_x = center_x - total_width // 2
        return [
            (
                value,
                Button(
                    pygame.Rect(start_x + i * (width + gap), y, width, height),
                    text,
                    font,
                ),
            )
            for i, (text, value) in enumerate(options)
        ]

    mode_buttons = _build_option_row(
        GAME_MODE_OPTIONS, _OPT_MODE_BUTTON_Y, _OPT_MODE_BUTTON_H
    )
    color_buttons = _build_option_row(
        HUMAN_COLOR_OPTIONS, _OPT_COLOR_BUTTON_Y, _OPT_COLOR_BUTTON_H
    )
    difficulty_buttons = _build_option_row(
        [(text, i) for i, (text, _settings) in enumerate(DIFFICULTY_OPTIONS)],
        _OPT_DIFF_BUTTON_Y,
        _OPT_DIFF_BUTTON_H,
    )
    time_buttons = _build_option_row(
        TIME_LIMIT_OPTIONS, _OPT_TIME_BUTTON_Y, _OPT_TIME_BUTTON_H
    )

    undo_toggle_button = Button(
        pygame.Rect(center_x - 70, _OPT_UNDO_BUTTON_Y, 140, _OPT_UNDO_BUTTON_H),
        "關",
        option_button_font,
    )

    options_bottom_width, options_bottom_gap = 200, 24
    options_bottom_total_width = options_bottom_width * 2 + options_bottom_gap
    options_bottom_start_x = center_x - options_bottom_total_width // 2
    options_back_button = Button(
        pygame.Rect(
            options_bottom_start_x,
            _OPT_BOTTOM_BUTTON_Y,
            options_bottom_width,
            _OPT_BOTTOM_BUTTON_H,
        ),
        "返回",
        button_font,
    )
    confirm_button = Button(
        pygame.Rect(
            options_bottom_start_x + options_bottom_width + options_bottom_gap,
            _OPT_BOTTOM_BUTTON_Y,
            options_bottom_width,
            _OPT_BOTTOM_BUTTON_H,
        ),
        "開始對局",
        button_font,
    )

    selected_game_mode = "pvp"
    selected_human_color = Color.WHITE
    selected_difficulty_index = 1  # 預設「普通」
    selected_time_limit_seconds = 300
    undo_enabled = False
    game_options_error = None

    promotion_icon_size = 72
    promotion_gap = 14
    promotion_popup_width = len(PROMOTION_CHOICES) * promotion_icon_size + (
        len(PROMOTION_CHOICES) - 1
    ) * promotion_gap
    promotion_start_x = center_x - promotion_popup_width // 2
    promotion_y = C.WINDOW_SIZE // 2 - promotion_icon_size // 2
    promotion_rects = {
        piece_type: pygame.Rect(
            promotion_start_x + i * (promotion_icon_size + promotion_gap),
            promotion_y,
            promotion_icon_size,
            promotion_icon_size,
        )
        for i, piece_type in enumerate(PROMOTION_CHOICES)
    }

    renderer = Renderer(content)
    game = Game()
    active_undo_enabled = False  # 目前這局是否允許悔棋，由對局設定畫面決定
    active_vs_computer = False  # 目前這局是否為人機對戰
    active_ai_color = None  # 電腦執子顏色（None 表示非人機對戰）
    engine = None  # 目前使用中的 UciEngine（僅人機對戰時存在）
    pending_ai_move = False  # 輪到電腦走棋、尚未取得引擎回應
    selected_pos = None
    legal_targets = []
    pending_promotion = None
    skip_next_tick = True  # 避免把「進入對局前」經過的時間算進西洋棋鐘

    screen_state = Screen.MENU

    running = True
    while running:
        dt_seconds = clock.tick(C.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                # 內容（選單/設定/棋盤）畫在置中的 content 畫布上，所有互動元件的
                # Rect 都是以該畫布為座標系；這裡把滑鼠座標平移回同一個座標系，
                # 下游的按鈕/滑桿/棋盤點擊判斷就不需要另外處理留白區位移。
                event.pos = (event.pos[0] - C.SIDE_MARGIN_WIDTH, event.pos[1])

            if screen_state == Screen.MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button.is_clicked(event.pos):
                        sfx.play_click()
                        screen_state = Screen.GAME_OPTIONS
                    elif settings_button.is_clicked(event.pos):
                        sfx.play_click()
                        screen_state = Screen.SETTINGS

            elif screen_state == Screen.SETTINGS:
                music_slider.handle_event(event)
                if music_slider.value != settings.music_volume:
                    settings.music_volume = music_slider.value
                    settings.apply()
                    settings.save()

                sfx_slider.handle_event(event)
                if sfx_slider.value != settings.sfx_volume:
                    settings.sfx_volume = sfx_slider.value
                    sfx.set_volume(settings.sfx_volume_ratio)
                    settings.save()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_button.is_clicked(event.pos):
                        sfx.play_click()
                        screen_state = Screen.MENU

            elif screen_state == Screen.GAME_OPTIONS:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 用獨立的旗標判斷「有沒有點到時間按鈕」，不能只看
                    # clicked_time_option 是否為 None——「無限制」選項本身
                    # 的值就是 None，兩者用同一個變數判斷會分不清楚。
                    time_option_clicked = False
                    clicked_time_option = None
                    if not undo_enabled:
                        for seconds, button in time_buttons:
                            if button.is_clicked(event.pos):
                                clicked_time_option = seconds
                                time_option_clicked = True
                                break

                    clicked_mode = next(
                        (mode for mode, btn in mode_buttons if btn.is_clicked(event.pos)), None
                    )
                    clicked_color = None
                    clicked_difficulty_index = None
                    if selected_game_mode == "pve":
                        clicked_color = next(
                            (c for c, btn in color_buttons if btn.is_clicked(event.pos)), None
                        )
                        clicked_difficulty_index = next(
                            (i for i, btn in difficulty_buttons if btn.is_clicked(event.pos)),
                            None,
                        )

                    if time_option_clicked:
                        sfx.play_click()
                        selected_time_limit_seconds = clicked_time_option
                        game_options_error = None
                    elif clicked_mode is not None:
                        sfx.play_click()
                        selected_game_mode = clicked_mode
                        game_options_error = None
                    elif clicked_color is not None:
                        sfx.play_click()
                        selected_human_color = clicked_color
                        game_options_error = None
                    elif clicked_difficulty_index is not None:
                        sfx.play_click()
                        selected_difficulty_index = clicked_difficulty_index
                        game_options_error = None
                    elif undo_toggle_button.is_clicked(event.pos):
                        sfx.play_click()
                        undo_enabled = not undo_enabled
                        game_options_error = None
                    elif options_back_button.is_clicked(event.pos):
                        sfx.play_click()
                        screen_state = Screen.MENU
                    elif confirm_button.is_clicked(event.pos):
                        sfx.play_click()
                        if undo_enabled or selected_time_limit_seconds is None:
                            effective_time_limit = float("inf")
                        else:
                            effective_time_limit = selected_time_limit_seconds

                        vs_computer = selected_game_mode == "pve"
                        new_engine = None
                        engine_start_failed = False
                        if vs_computer:
                            difficulty = DIFFICULTY_OPTIONS[selected_difficulty_index][1]
                            try:
                                new_engine = UciEngine(
                                    skill_level=difficulty["skill_level"],
                                    movetime_ms=difficulty["movetime_ms"],
                                )
                            except EngineError as exc:
                                game_options_error = str(exc)
                                engine_start_failed = True

                        if engine_start_failed:
                            pass  # 引擎啟動失敗，停留在設定畫面讓玩家看到錯誤訊息
                        else:
                            _stop_engine(engine)
                            engine = new_engine
                            game = Game(time_limit_seconds=effective_time_limit)
                            active_undo_enabled = undo_enabled
                            active_vs_computer = vs_computer
                            active_ai_color = (
                                selected_human_color.opposite if vs_computer else None
                            )
                            selected_pos, legal_targets = None, []
                            pending_promotion = None
                            skip_next_tick = True
                            pending_ai_move = vs_computer and active_ai_color is Color.WHITE
                            screen_state = Screen.PLAYING

            elif screen_state == Screen.PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    sfx.play_restart()
                    game = Game(time_limit_seconds=game.clock.time_limit_seconds)
                    if active_vs_computer and engine is not None:
                        engine.new_game()
                    selected_pos, legal_targets = None, []
                    pending_promotion = None
                    skip_next_tick = True
                    pending_ai_move = active_vs_computer and active_ai_color is Color.WHITE
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_z
                    and event.mod & pygame.KMOD_CTRL
                ):
                    if active_undo_enabled and pending_promotion is None and game.undo():
                        sfx.play_move()
                        selected_pos, legal_targets = None, []
                        skip_next_tick = True
                        pending_ai_move = (
                            active_vs_computer
                            and not game.is_game_over()
                            and game.turn is active_ai_color
                        )
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if pending_promotion is not None:
                        pending_promotion = None
                    else:
                        _stop_engine(engine)
                        engine = None
                        active_vs_computer = False
                        active_ai_color = None
                        pending_ai_move = False
                        screen_state = Screen.MENU
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and not game.is_game_over()
                ):
                    if pending_promotion is not None:
                        chosen = next(
                            (
                                piece_type
                                for piece_type, rect in promotion_rects.items()
                                if rect.collidepoint(event.pos)
                            ),
                            None,
                        )
                        if chosen is not None:
                            sfx.play_click()
                            game.make_move(
                                pending_promotion["from_pos"],
                                pending_promotion["to_pos"],
                                promotion=chosen,
                            )
                            sfx.play_move()
                            if game.is_game_over():
                                sfx.play_game_over()
                            elif active_vs_computer and game.turn is active_ai_color:
                                pending_ai_move = True
                        # 點擊視窗以外的地方視同取消這次升變選擇
                        pending_promotion = None
                        continue

                    clicked_pos = _pos_from_mouse(event.pos)

                    if selected_pos == clicked_pos:
                        selected_pos, legal_targets = None, []
                    elif selected_pos is not None and clicked_pos in legal_targets:
                        moves_here = [
                            m
                            for m in game.legal_moves_for(selected_pos)
                            if m.to_pos == clicked_pos
                        ]
                        if any(m.promotion is not None for m in moves_here):
                            pending_promotion = {
                                "from_pos": selected_pos,
                                "to_pos": clicked_pos,
                                "color": game.board.get_piece(selected_pos).color,
                            }
                        else:
                            game.make_move(selected_pos, clicked_pos)
                            sfx.play_move()
                            if game.is_game_over():
                                sfx.play_game_over()
                            elif active_vs_computer and game.turn is active_ai_color:
                                pending_ai_move = True
                        selected_pos, legal_targets = None, []
                    else:
                        piece = game.board.get_piece(clicked_pos)
                        if piece is not None and piece.color is game.turn:
                            selected_pos = clicked_pos
                            legal_targets = [
                                m.to_pos for m in game.legal_moves_for(clicked_pos)
                            ]
                        else:
                            selected_pos, legal_targets = None, []

        content_mouse_pos = (
            pygame.mouse.get_pos()[0] - C.SIDE_MARGIN_WIDTH,
            pygame.mouse.get_pos()[1],
        )
        screen.fill(C.MARGIN_BACKGROUND_COLOR)

        if screen_state == Screen.MENU:
            _draw_menu(
                content, title_font, start_button, settings_button, menu_background,
                content_mouse_pos,
            )
            pygame.display.set_caption("Chess Game - 主選單")
        elif screen_state == Screen.SETTINGS:
            _draw_settings(
                content, title_font, label_font, music_slider, sfx_slider, back_button,
                content_mouse_pos,
            )
            pygame.display.set_caption("Chess Game - 設定")
        elif screen_state == Screen.GAME_OPTIONS:
            _draw_game_options(
                content,
                options_title_font,
                label_font,
                mode_buttons,
                color_buttons,
                difficulty_buttons,
                time_buttons,
                undo_toggle_button,
                confirm_button,
                options_back_button,
                selected_game_mode,
                selected_human_color,
                selected_difficulty_index,
                selected_time_limit_seconds,
                undo_enabled,
                game_options_error,
                content_mouse_pos,
            )
            pygame.display.set_caption("Chess Game - 對局設定")
        else:
            if skip_next_tick:
                skip_next_tick = False
            else:
                was_game_over = game.is_game_over()
                game.tick(dt_seconds)
                if not was_game_over and game.is_game_over():
                    sfx.play_game_over()

            renderer.draw_board()
            if selected_pos is not None:
                renderer.highlight_squares([selected_pos], C.SELECTED_SQUARE_COLOR)
                renderer.highlight_squares(legal_targets, C.LEGAL_MOVE_HINT_COLOR)
            renderer.draw_pieces(game.board)
            if pending_promotion is not None:
                _draw_promotion_popup(
                    content,
                    renderer,
                    label_font,
                    pending_promotion["color"],
                    promotion_rects,
                    content_mouse_pos,
                )
            pygame.display.set_caption(_status_text(game, active_undo_enabled))

        screen.blit(content, (C.SIDE_MARGIN_WIDTH, 0))

        if screen_state == Screen.PLAYING:
            _draw_black_clock(screen, clock_font, tiny_font, game)
            _draw_white_clock(screen, clock_font, tiny_font, game)
            _draw_shortcut_hints(screen, tiny_font, active_undo_enabled)

            if pending_ai_move and engine is not None and not game.is_game_over():
                # 先把「電腦思考中」畫面呈現出來，再進行會阻塞的引擎運算，
                # 避免視窗看起來像當掉。
                _draw_ai_thinking_overlay(content, label_font)
                screen.blit(content, (C.SIDE_MARGIN_WIDTH, 0))
                pygame.display.flip()

                try:
                    move_uci = engine.best_move(game.moves_as_algebraic())
                    from_pos, to_pos, promotion = _parse_uci_move(move_uci)
                    game.make_move(from_pos, to_pos, promotion=promotion)
                    sfx.play_move()
                    if game.is_game_over():
                        sfx.play_game_over()
                except EngineError:
                    pass  # 引擎溝通失敗，維持目前局面，讓玩家可自行操作
                pending_ai_move = False

        pygame.display.flip()

    _stop_engine(engine)
    pygame.quit()
    sys.exit()
