"""棋盤狀態管理：棋子擺放、易位權、吃過路兵目標格等。"""

import copy

from .pieces import Color, Piece, PieceType

BOARD_SIZE = 8

_BACK_RANK_ORDER = [
    PieceType.ROOK,
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.QUEEN,
    PieceType.KING,
    PieceType.BISHOP,
    PieceType.KNIGHT,
    PieceType.ROOK,
]


class Board:
    """代表一個完整的棋局狀態(不含走棋歷史，歷史由 game.Game 管理)。"""

    def __init__(self):
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = Color.WHITE
        self.castling_rights = {
            Color.WHITE: {"kingside": True, "queenside": True},
            Color.BLACK: {"kingside": True, "queenside": True},
        }
        self.en_passant_target = None  # (row, col) 或 None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self._setup_standard_position()

    def _setup_standard_position(self):
        for col, piece_type in enumerate(_BACK_RANK_ORDER):
            self.grid[0][col] = Piece(Color.BLACK, piece_type)
            self.grid[7][col] = Piece(Color.WHITE, piece_type)
        for col in range(BOARD_SIZE):
            self.grid[1][col] = Piece(Color.BLACK, PieceType.PAWN)
            self.grid[6][col] = Piece(Color.WHITE, PieceType.PAWN)

    # ---- 基本存取 ----
    @staticmethod
    def in_bounds(pos: tuple) -> bool:
        row, col = pos
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_piece(self, pos: tuple):
        row, col = pos
        return self.grid[row][col]

    def set_piece(self, pos: tuple, piece) -> None:
        row, col = pos
        self.grid[row][col] = piece

    def is_empty(self, pos: tuple) -> bool:
        return self.get_piece(pos) is None

    def is_enemy(self, pos: tuple, color: Color) -> bool:
        piece = self.get_piece(pos)
        return piece is not None and piece.color is not color

    def is_friend(self, pos: tuple, color: Color) -> bool:
        piece = self.get_piece(pos)
        return piece is not None and piece.color is color

    def find_king(self, color: Color):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.grid[row][col]
                if piece is not None and piece.type is PieceType.KING and piece.color is color:
                    return (row, col)
        return None

    def all_pieces(self, color: Color = None):
        """回傳 [(pos, piece), ...]，可選擇只回傳特定顏色的棋子。"""
        result = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.grid[row][col]
                if piece is not None and (color is None or piece.color is color):
                    result.append(((row, col), piece))
        return result

    def clone(self) -> "Board":
        """深層複製整個棋盤狀態，供「試走一步看看會不會被將軍」使用。"""
        return copy.deepcopy(self)

    # ---- 座標與代數記譜轉換 ----
    @staticmethod
    def square_to_pos(square: str) -> tuple:
        """例如 'e4' -> (row, col)。"""
        file_char, rank_char = square[0], square[1]
        col = ord(file_char.lower()) - ord("a")
        row = BOARD_SIZE - int(rank_char)
        return (row, col)

    @staticmethod
    def pos_to_square(pos: tuple) -> str:
        row, col = pos
        file_char = chr(col + ord("a"))
        rank_char = str(BOARD_SIZE - row)
        return f"{file_char}{rank_char}"

    def __repr__(self) -> str:  # pragma: no cover
        rows = []
        for row in range(BOARD_SIZE):
            cells = [p.symbol if p else "." for p in self.grid[row]]
            rows.append(" ".join(cells))
        return "\n".join(rows)
