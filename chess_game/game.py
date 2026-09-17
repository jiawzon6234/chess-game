"""Game 類別：整合 board / rules，管理回合、走棋歷史與遊戲狀態。"""

from . import rules
from .board import Board
from .clock import ChessClock, DEFAULT_TIME_LIMIT_SECONDS
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
    TIMEOUT = "timeout"


class Game:
    def __init__(self, time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS):
        self.board = Board()
        self.move_history = []
        self.status = GameStatus.ONGOING
        self.winner = None
        self.position_history = {}
        self._record_position()
        self._undo_stack = []
        self.clock = ChessClock(time_limit_seconds)

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

        self._undo_stack.append(
            (
                self.board.clone(),
                self.status,
                self.winner,
                dict(self.position_history),
                self.clock.snapshot(),
            )
        )

        rules.apply_move(self.board, move)
        self.move_history.append(move)
        self._record_position()
        self._update_status()
        return True

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def undo(self) -> bool:
        """悔棋一步，回到上一步走完之前的狀態。若沒有步可悔則回傳 False。

        悔棋不受 `is_game_over()` 限制——即使已將死/和局/超時，也能悔掉
        最後一步棋，讓棋局回到進行中的狀態；雙方的西洋棋鐘剩餘時間也會
        一併還原。
        """
        if not self._undo_stack:
            return False

        board, status, winner, position_history, clock_snapshot = self._undo_stack.pop()
        self.board = board
        self.status = status
        self.winner = winner
        self.position_history = position_history
        self.clock.restore(clock_snapshot)
        self.move_history.pop()
        return True

    def tick(self, elapsed_seconds: float) -> None:
        """讓目前輪到走棋的一方西洋棋鐘減少 elapsed_seconds；時間歸零則立即
        判定該方超時輸棋。棋局已結束時不做任何事。"""
        if self.is_game_over():
            return

        self.clock.tick(self.board.turn, elapsed_seconds)
        if self.clock.timed_out_color is not None:
            self.status = GameStatus.TIMEOUT
            self.winner = self.clock.timed_out_color.opposite

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
