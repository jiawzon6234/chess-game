from chess_game import rules
from chess_game.board import Board
from chess_game.pieces import Color, Piece, PieceType


def _apply_algebraic(board: Board, move_str: str) -> None:
    from_pos = Board.square_to_pos(move_str[0:2])
    to_pos = Board.square_to_pos(move_str[2:4])
    piece = board.get_piece(from_pos)
    assert piece is not None, f"{move_str} 的起點沒有棋子"
    candidates = [
        m
        for m in rules.generate_legal_moves(board, piece.color)
        if m.from_pos == from_pos and m.to_pos == to_pos
    ]
    assert candidates, f"走法 {move_str} 應該合法"
    rules.apply_move(board, candidates[0])


def test_no_check_at_initial_position():
    board = Board()
    assert not rules.is_in_check(board, Color.WHITE)
    assert not rules.is_in_check(board, Color.BLACK)


def test_scholars_mate_checkmate():
    """經典「學者將死」：1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#"""
    board = Board()
    for move_str in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
        _apply_algebraic(board, move_str)

    assert rules.is_in_check(board, Color.BLACK)
    assert rules.is_checkmate(board, Color.BLACK)


def test_stalemate_known_position():
    """經典「后+王」逼和局面：黑王 h8，白王 f7，白后 g6，輪到黑方且未被將軍。"""
    board = Board()
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    board.grid[0][7] = Piece(Color.BLACK, PieceType.KING)  # h8
    board.grid[1][5] = Piece(Color.WHITE, PieceType.KING)  # f7
    board.grid[2][6] = Piece(Color.WHITE, PieceType.QUEEN)  # g6
    board.turn = Color.BLACK

    assert not rules.is_in_check(board, Color.BLACK)
    assert rules.is_stalemate(board, Color.BLACK)


def test_en_passant_capture_available():
    board = Board()
    for move_str in ("e2e4", "a7a6", "e4e5", "d7d5"):
        _apply_algebraic(board, move_str)

    # 白兵在 e5，黑兵剛從 d7 走到 d5，白兵應可吃過路兵到 d6
    en_passant_target = Board.square_to_pos("d6")
    assert board.en_passant_target == en_passant_target

    white_pawn_pos = Board.square_to_pos("e5")
    legal_moves = rules.generate_legal_moves(board, Color.WHITE)
    assert any(
        m.from_pos == white_pawn_pos and m.to_pos == en_passant_target and m.is_en_passant
        for m in legal_moves
    )
