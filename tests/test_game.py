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
