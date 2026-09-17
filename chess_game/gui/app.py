"""Pygame 主程式：開始畫面、設定畫面，以及棋盤事件迴圈與畫面繪製。"""

import os
import sys
from enum import Enum, auto

import pygame

from .. import constants as C
from ..game import Game, GameStatus
from ..pieces import Color, PROMOTION_CHOICES
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
    PLAYING = auto()


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


_HINTS = "按 R 重新開始，Ctrl+Z 悔棋，Esc 回主選單"


def _status_text(game: Game) -> str:
    turn_name = "白方" if game.turn.value == "white" else "黑方"
    if game.status == GameStatus.CHECKMATE:
        winner_name = "白方" if game.winner.value == "white" else "黑方"
        return f"Chess Game - 將死！{winner_name}獲勝（{_HINTS}）"
    if game.status == GameStatus.STALEMATE:
        return f"Chess Game - 和棋（逼和，{_HINTS}）"
    if game.status == GameStatus.DRAW_BY_REPETITION:
        return f"Chess Game - 和棋（三次重複局面，{_HINTS}）"
    if game.status == GameStatus.DRAW_BY_FIFTY_MOVE_RULE:
        return f"Chess Game - 和棋（50 手和局規則，{_HINTS}）"
    if game.status == GameStatus.TIMEOUT:
        winner_name = "白方" if game.winner.value == "white" else "黑方"
        loser_name = "黑方" if game.winner.value == "white" else "白方"
        return f"Chess Game - {loser_name}時間到！{winner_name}獲勝（{_HINTS}）"
    return f"Chess Game - 輪到{turn_name}走棋（{_HINTS}）"


def _format_clock_time(seconds: float) -> str:
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


_SHORTCUT_LINES = ("快捷鍵", "R 重新開始", "Ctrl+Z 悔棋", "Esc 回主選單")


def _draw_shortcut_hints(screen, tiny_font) -> None:
    """快捷鍵提示：畫在右側留白區的右上角。"""
    left_x = C.SIDE_MARGIN_WIDTH + C.WINDOW_SIZE + MARGIN_PADDING
    y = MARGIN_PADDING
    for i, line in enumerate(_SHORTCUT_LINES):
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
                        game = Game()
                        selected_pos, legal_targets = None, []
                        pending_promotion = None
                        skip_next_tick = True
                        screen_state = Screen.PLAYING
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

            elif screen_state == Screen.PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    sfx.play_restart()
                    game = Game()
                    selected_pos, legal_targets = None, []
                    pending_promotion = None
                    skip_next_tick = True
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_z
                    and event.mod & pygame.KMOD_CTRL
                ):
                    if pending_promotion is None and game.undo():
                        sfx.play_move()
                        selected_pos, legal_targets = None, []
                        skip_next_tick = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if pending_promotion is not None:
                        pending_promotion = None
                    else:
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
            pygame.display.set_caption(_status_text(game))

        screen.blit(content, (C.SIDE_MARGIN_WIDTH, 0))

        if screen_state == Screen.PLAYING:
            _draw_black_clock(screen, clock_font, tiny_font, game)
            _draw_white_clock(screen, clock_font, tiny_font, game)
            _draw_shortcut_hints(screen, tiny_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
