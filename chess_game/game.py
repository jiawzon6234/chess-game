"""Game 類別：整合 board / rules，管理回合、走棋歷史與遊戲狀態。"""

from . import rules
from .board import Board
from .pieces import PieceType

# 三次重複局面：同一局面（棋子擺放、輪到誰走、易位權、吃過路兵目標格皆相同）
# 出現達此次數即判和。
THREEFOLD_REPETITION_COUNT = 3

# 50 手和局規則：雙方合計 100 個半回合（half-move，即 50 手）內若沒有兵移動
# 或吃子，則判和。對應 board.halfmove_clock。
FIFTY_MOVE_HALFMOVE_LIMIT = 100


class GameStatus:
    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW_BY_REPETITION = "draw_by_repetition"
    DRAW_BY_FIFTY_MOVE_RULE = "draw_by_fifty_move_rule"


class Game:
    def __init__(self):
        self.board = Board()
        self.move_history = []
        self.status = GameStatus.ONGOING
        self.winner = None
        self.position_history = {}
        self._record_position()

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
        self._record_position()
        self._update_status()
        return True

    def _update_status(self) -> None:
        side_to_move = self.board.turn
        if rules.is_checkmate(self.board, side_to_move):
            self.status = GameStatus.CHECKMATE
            self.winner = side_to_move.opposite
        elif rules.is_stalemate(self.board, side_to_move):
            self.status = GameStatus.STALEMATE
        elif self._is_threefold_repetition():
            self.status = GameStatus.DRAW_BY_REPETITION
        elif self.board.halfmove_clock >= FIFTY_MOVE_HALFMOVE_LIMIT:
            self.status = GameStatus.DRAW_BY_FIFTY_MOVE_RULE
        else:
            self.status = GameStatus.ONGOING

    @staticmethod
    def _position_key(board: Board):
        """回傳可雜湊的局面表示，用於判斷三次重複局面。

        局面是否「相同」取決於：棋子擺放、輪到哪一方走、雙方易位權、
        吃過路兵目標格——皆一致才視為同一局面。
        """
        grid_key = tuple(
            tuple(
                None if piece is None else (piece.color.value, piece.type.value)
                for piece in row
            )
            for row in board.grid
        )
        castling_key = tuple(
            (color.value, rights["kingside"], rights["queenside"])
            for color, rights in sorted(
                board.castling_rights.items(), key=lambda item: item[0].value
            )
        )
        return (grid_key, board.turn.value, castling_key, board.en_passant_target)

    def _record_position(self) -> None:
        key = self._position_key(self.board)
        self.position_history[key] = self.position_history.get(key, 0) + 1

    def _is_threefold_repetition(self) -> bool:
        key = self._position_key(self.board)
        return self.position_history.get(key, 0) >= THREEFOLD_REPETITION_COUNT

    def moves_as_algebraic(self) -> list:
        return [move.to_algebraic() for move in self.move_history]
