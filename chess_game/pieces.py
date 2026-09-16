"""棋子定義與每種棋子的「虛擬合法走法(pseudo-legal moves)」產生邏輯。

這裡產生的走法只考慮「棋子本身的移動規則」，尚未檢查走完之後
是否會讓自己的國王被將軍——那一層過濾在 rules.py 中處理。
"""

from enum import Enum

from .moves import Move


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    @property
    def opposite(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE


class PieceType(Enum):
    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "B"
    ROOK = "R"
    QUEEN = "Q"
    KING = "K"


class Piece:
    """棋子物件。has_moved 用於判斷易位權與兵的雙步移動資格。"""

    def __init__(self, color: Color, piece_type: PieceType, has_moved: bool = False):
        self.color = color
        self.type = piece_type
        self.has_moved = has_moved

    @property
    def symbol(self) -> str:
        """回傳單一字元代表棋子，白棋大寫、黑棋小寫 (類似 FEN 表示法)。"""
        s = self.type.value
        return s if self.color is Color.WHITE else s.lower()

    def pseudo_legal_moves(self, pos: tuple, board) -> list:
        """回傳此棋子在目前棋盤狀態下，忽略「是否會被將軍」的所有可能走法。"""
        generator = _MOVE_GENERATORS[self.type]
        return generator(self, pos, board)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Piece({self.color.value}, {self.type.value})"


# ---------------------------------------------------------------------------
# 各棋子走法產生器
# ---------------------------------------------------------------------------

KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRECTIONS = BISHOP_DIRECTIONS + ROOK_DIRECTIONS

PROMOTION_CHOICES = (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT)


def _pawn_moves(piece: Piece, pos: tuple, board) -> list:
    moves = []
    row, col = pos
    direction = -1 if piece.color is Color.WHITE else 1
    start_row = 6 if piece.color is Color.WHITE else 1
    promotion_row = 0 if piece.color is Color.WHITE else 7

    # 前進一格
    one_step = (row + direction, col)
    if board.in_bounds(one_step) and board.is_empty(one_step):
        moves.extend(_expand_pawn_move(piece, pos, one_step, promotion_row))
        # 起始位置可前進兩格
        two_step = (row + 2 * direction, col)
        if row == start_row and board.is_empty(two_step):
            moves.append(Move(pos, two_step, piece, is_double_pawn_push=True))

    # 斜吃 (含吃過路兵)
    for dc in (-1, 1):
        capture_pos = (row + direction, col + dc)
        if not board.in_bounds(capture_pos):
            continue
        if board.is_enemy(capture_pos, piece.color):
            captured = board.get_piece(capture_pos)
            moves.extend(_expand_pawn_move(piece, pos, capture_pos, promotion_row, captured))
        elif board.en_passant_target == capture_pos:
            captured_pawn_pos = (row, col + dc)
            moves.append(
                Move(
                    pos,
                    capture_pos,
                    piece,
                    captured_piece=board.get_piece(captured_pawn_pos),
                    is_en_passant=True,
                )
            )
    return moves


def _expand_pawn_move(piece, from_pos, to_pos, promotion_row, captured=None):
    if to_pos[0] == promotion_row:
        return [
            Move(from_pos, to_pos, piece, captured_piece=captured, promotion=choice)
            for choice in PROMOTION_CHOICES
        ]
    return [Move(from_pos, to_pos, piece, captured_piece=captured)]


def _knight_moves(piece: Piece, pos: tuple, board) -> list:
    moves = []
    row, col = pos
    for dr, dc in KNIGHT_OFFSETS:
        target = (row + dr, col + dc)
        if board.in_bounds(target) and not board.is_friend(target, piece.color):
            moves.append(Move(pos, target, piece, captured_piece=board.get_piece(target)))
    return moves


def _sliding_moves(piece: Piece, pos: tuple, board, directions) -> list:
    moves = []
    row, col = pos
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while board.in_bounds((r, c)):
            if board.is_friend((r, c), piece.color):
                break
            captured = board.get_piece((r, c))
            moves.append(Move(pos, (r, c), piece, captured_piece=captured))
            if captured is not None:
                break
            r += dr
            c += dc
    return moves


def _bishop_moves(piece: Piece, pos: tuple, board) -> list:
    return _sliding_moves(piece, pos, board, BISHOP_DIRECTIONS)


def _rook_moves(piece: Piece, pos: tuple, board) -> list:
    return _sliding_moves(piece, pos, board, ROOK_DIRECTIONS)


def _queen_moves(piece: Piece, pos: tuple, board) -> list:
    return _sliding_moves(piece, pos, board, QUEEN_DIRECTIONS)


def _king_moves(piece: Piece, pos: tuple, board) -> list:
    # 注意：易位 (castling) 走法在 rules.py 中另外產生，
    # 因為需要檢查棋盤上多個格子是否被攻擊，屬於「規則層」而非「棋子本身」的邏輯。
    moves = []
    row, col = pos
    for dr, dc in KING_OFFSETS:
        target = (row + dr, col + dc)
        if board.in_bounds(target) and not board.is_friend(target, piece.color):
            moves.append(Move(pos, target, piece, captured_piece=board.get_piece(target)))
    return moves


_MOVE_GENERATORS = {
    PieceType.PAWN: _pawn_moves,
    PieceType.KNIGHT: _knight_moves,
    PieceType.BISHOP: _bishop_moves,
    PieceType.ROOK: _rook_moves,
    PieceType.QUEEN: _queen_moves,
    PieceType.KING: _king_moves,
}
