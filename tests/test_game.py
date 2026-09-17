from chess_game.board import Board
from chess_game.game import Game, GameStatus
from chess_game.pieces import Color, Piece, PieceType


def _apply_algebraic(game: Game, move_str: str) -> None:
    from_pos = Board.square_to_pos(move_str[0:2])
    to_pos = Board.square_to_pos(move_str[2:4])
    assert game.make_move(from_pos, to_pos), f"走法 {move_str} 應該合法"


def test_threefold_repetition_draws_the_game():
    """雙方騎士來回走動 (Ng1-f3 Ng8-f6 Nf3-g1 Nf6-g8) x2，
    局面會與開局完全相同、第三次出現時應判和。"""
    game = Game()
    shuffle = ("g1f3", "g8f6", "f3g1", "f6g8")

    for move_str in shuffle:
        _apply_algebraic(game, move_str)
    assert game.status == GameStatus.ONGOING  # 開局算第 1 次、這裡是第 2 次出現

    for move_str in shuffle[:-1]:
        _apply_algebraic(game, move_str)
    assert game.status == GameStatus.ONGOING

    _apply_algebraic(game, shuffle[-1])  # 第 3 次出現，觸發和局
    assert game.status == GameStatus.DRAW_BY_REPETITION
    assert game.is_game_over()


def test_position_with_different_castling_rights_is_not_a_repetition():
    """棋子擺放相同，但其中一次白方已失去易位權，不應被視為重複局面。"""
    game = Game()
    key_with_rights = game._position_key(game.board)

    game.board.castling_rights[Color.WHITE]["kingside"] = False
    key_without_rights = game._position_key(game.board)

    assert key_with_rights != key_without_rights


def test_fifty_move_rule_draws_when_limit_reached():
    """halfmove_clock 達到 100（50 手）且沒有兵走動/吃子時應判和。"""
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[7][4] = Piece(Color.WHITE, PieceType.KING)  # e1
    game.board.grid[7][1] = Piece(Color.WHITE, PieceType.KNIGHT)  # b1
    game.board.grid[0][4] = Piece(Color.BLACK, PieceType.KING)  # e8
    game.board.grid[0][1] = Piece(Color.BLACK, PieceType.KNIGHT)  # b8
    game.board.turn = Color.WHITE
    game.board.halfmove_clock = 99

    _apply_algebraic(game, "b1c3")  # 騎士走動，非兵move/吃子，觸發 halfmove_clock=100

    assert game.status == GameStatus.DRAW_BY_FIFTY_MOVE_RULE
    assert game.is_game_over()


def test_fifty_move_rule_not_yet_triggered_below_limit():
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[7][4] = Piece(Color.WHITE, PieceType.KING)
    game.board.grid[7][1] = Piece(Color.WHITE, PieceType.KNIGHT)
    game.board.grid[0][4] = Piece(Color.BLACK, PieceType.KING)
    game.board.grid[0][1] = Piece(Color.BLACK, PieceType.KNIGHT)
    game.board.turn = Color.WHITE
    game.board.halfmove_clock = 98

    _apply_algebraic(game, "b1c3")  # halfmove_clock -> 99，尚未達門檻

    assert game.status == GameStatus.ONGOING
    assert not game.is_game_over()


def test_pawn_move_resets_fifty_move_counter():
    game = Game()
    game.board.halfmove_clock = 40

    _apply_algebraic(game, "e2e4")  # 兵走動應重置計數器

    assert game.board.halfmove_clock == 0
    assert game.status == GameStatus.ONGOING


def test_cannot_undo_fresh_game():
    game = Game()
    assert not game.can_undo()
    assert not game.undo()


def test_undo_reverts_last_move():
    game = Game()
    _apply_algebraic(game, "e2e4")
    assert game.board.get_piece(Board.square_to_pos("e4")) is not None
    assert game.turn is Color.BLACK
    assert game.can_undo()

    assert game.undo()

    assert game.board.get_piece(Board.square_to_pos("e4")) is None
    e2_piece = game.board.get_piece(Board.square_to_pos("e2"))
    assert e2_piece is not None and e2_piece.type is PieceType.PAWN
    assert game.turn is Color.WHITE
    assert game.move_history == []
    assert not game.can_undo()


def test_undo_multiple_moves_one_at_a_time():
    game = Game()
    for move_str in ("e2e4", "e7e5", "g1f3"):
        _apply_algebraic(game, move_str)
    assert len(game.move_history) == 3

    assert game.undo()
    assert len(game.move_history) == 2
    assert game.board.get_piece(Board.square_to_pos("g1")).type is PieceType.KNIGHT

    assert game.undo()
    assert game.undo()
    assert game.move_history == []
    assert not game.can_undo()
    assert game.board.get_piece(Board.square_to_pos("e2")).type is PieceType.PAWN
    assert game.board.get_piece(Board.square_to_pos("e7")).type is PieceType.PAWN


def test_undo_restores_captured_piece():
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[7][4] = Piece(Color.WHITE, PieceType.KING)  # e1
    game.board.grid[0][4] = Piece(Color.BLACK, PieceType.KING)  # e8
    game.board.grid[5][2] = Piece(Color.WHITE, PieceType.KNIGHT)  # c3
    game.board.grid[3][3] = Piece(Color.BLACK, PieceType.PAWN)  # d5
    game.board.turn = Color.WHITE

    _apply_algebraic(game, "c3d5")  # 騎士吃兵
    assert game.board.get_piece(Board.square_to_pos("d5")).color is Color.WHITE
    assert game.board.halfmove_clock == 0  # 吃子重置計數器

    assert game.undo()

    captured_back = game.board.get_piece(Board.square_to_pos("d5"))
    assert captured_back is not None
    assert captured_back.color is Color.BLACK and captured_back.type is PieceType.PAWN
    knight_back = game.board.get_piece(Board.square_to_pos("c3"))
    assert knight_back is not None
    assert knight_back.color is Color.WHITE and knight_back.type is PieceType.KNIGHT


def test_undo_restores_pawn_before_promotion():
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[7][4] = Piece(Color.WHITE, PieceType.KING)  # e1
    game.board.grid[0][4] = Piece(Color.BLACK, PieceType.KING)  # e8
    game.board.grid[1][0] = Piece(Color.WHITE, PieceType.PAWN)  # a7
    game.board.turn = Color.WHITE

    assert game.make_move(
        Board.square_to_pos("a7"), Board.square_to_pos("a8"), promotion=PieceType.QUEEN
    )
    promoted = game.board.get_piece(Board.square_to_pos("a8"))
    assert promoted.type is PieceType.QUEEN

    assert game.undo()

    assert game.board.get_piece(Board.square_to_pos("a8")) is None
    pawn_back = game.board.get_piece(Board.square_to_pos("a7"))
    assert pawn_back is not None and pawn_back.type is PieceType.PAWN


def test_undo_after_checkmate_reopens_the_game():
    """經典「學者將死」，悔掉最後一步應能讓棋局恢復進行中。"""
    game = Game()
    for move_str in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
        _apply_algebraic(game, move_str)
    assert game.status == GameStatus.CHECKMATE
    assert game.is_game_over()

    assert game.undo()

    assert game.status == GameStatus.ONGOING
    assert not game.is_game_over()
    assert game.turn is Color.WHITE
    assert len(game.all_legal_moves()) > 0


def test_new_game_has_five_minute_clock_for_both_sides():
    game = Game()
    assert game.clock.remaining[Color.WHITE] == 300
    assert game.clock.remaining[Color.BLACK] == 300


def test_tick_only_drains_the_side_to_move():
    game = Game()  # 白方先走
    game.tick(10)
    assert game.clock.remaining[Color.WHITE] == 290
    assert game.clock.remaining[Color.BLACK] == 300
    assert game.status == GameStatus.ONGOING


def test_tick_causes_timeout_loss_when_time_runs_out():
    game = Game(time_limit_seconds=5)
    game.tick(5.5)

    assert game.status == GameStatus.TIMEOUT
    assert game.winner is Color.BLACK  # 白方超時，黑方獲勝
    assert game.is_game_over()


def test_tick_does_nothing_once_game_is_over():
    game = Game()
    for move_str in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
        _apply_algebraic(game, move_str)
    assert game.status == GameStatus.CHECKMATE

    remaining_before = dict(game.clock.remaining)
    game.tick(9999)

    assert game.clock.remaining == remaining_before
    assert game.status == GameStatus.CHECKMATE  # 未被 tick 覆蓋成 TIMEOUT


def test_undo_restores_clock_state():
    game = Game()
    game.tick(30)
    assert game.clock.remaining[Color.WHITE] == 270

    _apply_algebraic(game, "e2e4")
    game.tick(15)
    assert game.clock.remaining[Color.BLACK] == 285

    assert game.undo()

    assert game.clock.remaining[Color.WHITE] == 270
    assert game.clock.remaining[Color.BLACK] == 300


def test_undo_after_timeout_allows_clock_to_resume():
    """悔掉造成超時之前的那一步後，時鐘應恢復正常運作
    （而不是因為 timed_out_color 殘留而永遠卡住）。"""
    game = Game(time_limit_seconds=5)
    _apply_algebraic(game, "e2e4")  # 先走一步，才有東西可悔棋
    game.tick(5.5)  # 換黑方計時，黑方超時
    assert game.status == GameStatus.TIMEOUT
    assert game.winner is Color.WHITE

    assert game.undo()
    assert game.status == GameStatus.ONGOING
    assert game.clock.timed_out_color is None
    assert game.turn is Color.WHITE

    game.tick(1)
    assert game.clock.remaining[Color.WHITE] == 4
    assert game.status == GameStatus.ONGOING
