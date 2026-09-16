from chess_game.board import Board
from chess_game.pieces import Color, PieceType


def test_initial_setup_has_32_pieces():
    board = Board()
    assert len(board.all_pieces()) == 32


def test_initial_pawn_rows():
    board = Board()
    for col in range(8):
        white_pawn = board.grid[6][col]
        black_pawn = board.grid[1][col]
        assert white_pawn.type is PieceType.PAWN and white_pawn.color is Color.WHITE
        assert black_pawn.type is PieceType.PAWN and black_pawn.color is Color.BLACK


def test_white_moves_first():
    board = Board()
    assert board.turn is Color.WHITE


def test_square_conversion_roundtrip():
    for square in ("a1", "h8", "e4", "d5", "h1", "a8"):
        pos = Board.square_to_pos(square)
        assert Board.pos_to_square(pos) == square


def test_square_to_pos_known_values():
    assert Board.square_to_pos("e2") == (6, 4)
    assert Board.square_to_pos("e4") == (4, 4)
    assert Board.square_to_pos("a8") == (0, 0)
    assert Board.square_to_pos("h1") == (7, 7)
