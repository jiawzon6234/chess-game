"""Pygame 主程式：開始畫面、設定畫面，以及棋盤事件迴圈與畫面繪製。"""

import sys
from enum import Enum, auto

import pygame

from .. import constants as C
from ..game import Game, GameStatus
from ..settings import Settings
from .fonts import get_font
from .renderer import Renderer
from .screens import Button, Slider


class Screen(Enum):
    MENU = auto()
    SETTINGS = auto()
    PLAYING = auto()


def _pos_from_mouse(mouse_pos: tuple) -> tuple:
    x, y = mouse_pos
    return (y // C.SQUARE_SIZE, x // C.SQUARE_SIZE)


def _status_text(game: Game) -> str:
    turn_name = "白方" if game.turn.value == "white" else "黑方"
    if game.status == GameStatus.CHECKMATE:
        winner_name = "白方" if game.winner.value == "white" else "黑方"
        return f"Chess Game - 將死！{winner_name}獲勝（按 R 重新開始，Esc 回主選單）"
    if game.status == GameStatus.STALEMATE:
        return "Chess Game - 和棋（逼和，按 R 重新開始，Esc 回主選單）"
    return f"Chess Game - 輪到{turn_name}走棋（按 R 重新開始，Esc 回主選單）"


def _draw_menu(screen, title_font, start_button, settings_button) -> None:
    screen.fill(C.MENU_BACKGROUND_COLOR)

    title_surface = title_font.render("CHESS", True, C.MENU_TITLE_COLOR)
    title_rect = title_surface.get_rect(center=(C.WINDOW_SIZE // 2, C.WINDOW_SIZE // 3))
    screen.blit(title_surface, title_rect)

    start_button.draw(screen)
    settings_button.draw(screen)


def _draw_settings(screen, title_font, label_font, volume_slider, back_button) -> None:
    screen.fill(C.MENU_BACKGROUND_COLOR)

    title_surface = title_font.render("設定", True, C.MENU_TITLE_COLOR)
    title_rect = title_surface.get_rect(center=(C.WINDOW_SIZE // 2, C.WINDOW_SIZE // 4))
    screen.blit(title_surface, title_rect)

    label_surface = label_font.render(f"音量：{volume_slider.value}", True, C.BUTTON_TEXT_COLOR)
    label_rect = label_surface.get_rect(
        center=(C.WINDOW_SIZE // 2, volume_slider.rect.y - 36)
    )
    screen.blit(label_surface, label_rect)

    volume_slider.draw(screen)
    back_button.draw(screen)


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Chess Game")
    screen = pygame.display.set_mode((C.WINDOW_SIZE, C.WINDOW_SIZE))
    clock = pygame.time.Clock()

    settings = Settings.load()
    settings.apply()

    title_font = get_font(int(C.WINDOW_SIZE * 0.1), bold=True)
    label_font = get_font(26)
    button_font = get_font(28, bold=True)

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
    volume_slider = Slider(
        pygame.Rect(center_x - 160, C.WINDOW_SIZE // 2, 320, 18),
        value=settings.volume,
    )

    renderer = Renderer(screen)
    game = Game()
    selected_pos = None
    legal_targets = []

    screen_state = Screen.MENU

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if screen_state == Screen.MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button.is_clicked(event.pos):
                        game = Game()
                        selected_pos, legal_targets = None, []
                        screen_state = Screen.PLAYING
                    elif settings_button.is_clicked(event.pos):
                        screen_state = Screen.SETTINGS

            elif screen_state == Screen.SETTINGS:
                volume_slider.handle_event(event)
                if volume_slider.value != settings.volume:
                    settings.volume = volume_slider.value
                    settings.apply()
                    settings.save()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_button.is_clicked(event.pos):
                        screen_state = Screen.MENU

            elif screen_state == Screen.PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    game = Game()
                    selected_pos, legal_targets = None, []
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    screen_state = Screen.MENU
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and not game.is_game_over()
                ):
                    clicked_pos = _pos_from_mouse(event.pos)

                    if selected_pos == clicked_pos:
                        selected_pos, legal_targets = None, []
                    elif selected_pos is not None and clicked_pos in legal_targets:
                        # GUI 模式下兵升變預設自動升為皇后；
                        # 之後可擴充成彈出選單讓玩家自行選擇。
                        game.make_move(selected_pos, clicked_pos)
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

        if screen_state == Screen.MENU:
            _draw_menu(screen, title_font, start_button, settings_button)
            pygame.display.set_caption("Chess Game - 主選單")
        elif screen_state == Screen.SETTINGS:
            _draw_settings(screen, title_font, label_font, volume_slider, back_button)
            pygame.display.set_caption("Chess Game - 設定")
        else:
            renderer.draw_board()
            if selected_pos is not None:
                renderer.highlight_squares([selected_pos], C.SELECTED_SQUARE_COLOR)
                renderer.highlight_squares(legal_targets, C.LEGAL_MOVE_HINT_COLOR)
            renderer.draw_pieces(game.board)
            pygame.display.set_caption(_status_text(game))

        pygame.display.flip()
        clock.tick(C.FPS)

    pygame.quit()
    sys.exit()
