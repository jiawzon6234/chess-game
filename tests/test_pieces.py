from chess_game.board import Board


def test_knight_initial_moves_from_b1():
    board = Board()
    knight_pos = Board.square_to_pos("b1")
    knight = board.get_piece(knight_pos)
    destinations = {m.to_pos for m in knight.pseudo_legal_moves(knight_pos, board)}
    assert Board.square_to_pos("a3") in destinations
    assert Board.square_to_pos("c3") in destinations
    assert len(destinations) == 2  # 起始位置只有兩個可走的格子


def test_pawn_double_step_available_from_start():
    board = Board()
    pawn_pos = Board.square_to_pos("e2")
    pawn = board.get_piece(pawn_pos)
    destinations = {m.to_pos for m in pawn.pseudo_legal_moves(pawn_pos, board)}
    assert Board.square_to_pos("e3") in destinations
    assert Board.square_to_pos("e4") in destinations


def test_rook_blocked_by_own_pieces_at_start():
    board = Board()
    rook_pos = Board.square_to_pos("a1")
    rook = board.get_piece(rook_pos)
    assert rook.pseudo_legal_moves(rook_pos, board) == []


def test_bishop_blocked_by_own_pieces_at_start():
    board = Board()
    bishop_pos = Board.square_to_pos("c1")
    bishop = board.get_piece(bishop_pos)
    assert bishop.pseudo_legal_moves(bishop_pos, board) == []
