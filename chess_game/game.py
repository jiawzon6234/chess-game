"""Game 類別：整合 board / rules，管理回合、走棋歷史與遊戲狀態。"""

from . import rules
from .board import Board
from .pieces import PieceType


class GameStatus:
    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"


class Game:
    def __init__(self):
        self.board = Board()
        self.move_history = []
        self.status = GameStatus.ONGOING
        self.winner = None

    @property
    def turn(self):
        return self.board.turn

    def is_game_over(self) -> bool:
        return self.status != GameStatus.ONGOING

    def all_legal_moves(self) -> list:
        if self.is_game_over():
            return []
        return rules.generate_legal_moves(self.board, self.board.turn)

    def legal_moves_for(self, pos: tuple) -> list:
        """回傳從 pos 出發的所有合法走法(只有輪到該棋子的顏色時才有結果)。"""
        piece = self.board.get_piece(pos)
        if piece is None or piece.color is not self.board.turn:
            return []
        return [m for m in self.all_legal_moves() if m.from_pos == pos]

    def make_move(self, from_pos: tuple, to_pos: tuple, promotion: PieceType = None) -> bool:
        """嘗試走一步棋。合法則套用並回傳 True，否則不改變狀態並回傳 False。"""
        if self.is_game_over():
            return False

        candidates = [
            m for m in self.all_legal_moves() if m.from_pos == from_pos and m.to_pos == to_pos
        ]
        if not candidates:
            return False

        move = candidates[0]
        if move.promotion is not None and promotion is not None:
            move = next((m for m in candidates if m.promotion is promotion), move)

        rules.apply_move(self.board, move)
        self.move_history.append(move)
        self._update_status()
        return True

    def _update_status(self) -> None:
        side_to_move = self.board.turn
        if rules.is_checkmate(self.board, side_to_move):
            self.status = GameStatus.CHECKMATE
            self.winner = side_to_move.opposite
        elif rules.is_stalemate(self.board, side_to_move):
            self.status = GameStatus.STALEMATE
        else:
            self.status = GameStatus.ONGOING

    def moves_as_algebraic(self) -> list:
        return [move.to_algebraic() for move in self.move_history]
