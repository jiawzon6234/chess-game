"""選單／設定畫面共用的簡易 UI 元件：按鈕與滑桿。"""

import pygame

from .. import constants as C


class Button:
    def __init__(self, rect: "pygame.Rect", text: str, font: "pygame.font.Font"):
        self.rect = rect
        self.text = text
        self.font = font

    def is_clicked(self, mouse_pos: tuple) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def draw(self, screen: "pygame.Surface") -> None:
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = C.BUTTON_HOVER_COLOR if hovered else C.BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, C.BUTTON_TEXT_COLOR, self.rect, 2, border_radius=10)

        label = self.font.render(self.text, True, C.BUTTON_TEXT_COLOR)
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)


class Slider:
    """水平拖曳式滑桿，預設數值範圍 0~100，用於音量控制。"""

    def __init__(
        self,
        rect: "pygame.Rect",
        min_value: int = 0,
        max_value: int = 100,
        value: int = 100,
    ):
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(min_value, min(max_value, value))
        self._dragging = False

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) or self._handle_rect().collidepoint(event.pos):
                self._dragging = True
                self._update_value_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_value_from_x(event.pos[0])

    def _update_value_from_x(self, x: int) -> None:
        ratio = (x - self.rect.x) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        self.value = round(self.min_value + ratio * (self.max_value - self.min_value))

    def _handle_rect(self) -> "pygame.Rect":
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        handle_x = self.rect.x + int(self.rect.width * ratio)
        radius = self.rect.height
        return pygame.Rect(handle_x - radius, self.rect.centery - radius, radius * 2, radius * 2)

    def draw(self, screen: "pygame.Surface") -> None:
        pygame.draw.rect(
            screen, C.SLIDER_TRACK_COLOR, self.rect, border_radius=self.rect.height // 2
        )

        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        fill_rect = pygame.Rect(
            self.rect.x, self.rect.y, int(self.rect.width * ratio), self.rect.height
        )
        if fill_rect.width > 0:
            pygame.draw.rect(
                screen, C.SLIDER_FILL_COLOR, fill_rect, border_radius=self.rect.height // 2
            )

        handle_rect = self._handle_rect()
        pygame.draw.ellipse(screen, C.SLIDER_HANDLE_COLOR, handle_rect)
        pygame.draw.ellipse(screen, C.BUTTON_TEXT_COLOR, handle_rect, 2)
