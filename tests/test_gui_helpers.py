"""測試 chess_game.gui.app 內不需要建立視窗/顯示裝置的純邏輯函式。"""

from chess_game.board import Board
from chess_game.gui.app import _parse_uci_move
from chess_game.pieces import PieceType


def test_parse_uci_move_normal():
    from_pos, to_pos, promotion = _parse_uci_move("e2e4")
    assert from_pos == Board.square_to_pos("e2")
    assert to_pos == Board.square_to_pos("e4")
    assert promotion is None


def test_parse_uci_move_promotion_queen():
    from_pos, to_pos, promotion = _parse_uci_move("e7e8q")
    assert from_pos == Board.square_to_pos("e7")
    assert to_pos == Board.square_to_pos("e8")
    assert promotion is PieceType.QUEEN


def test_parse_uci_move_promotion_knight_underpromotion():
    _, _, promotion = _parse_uci_move("a7a8n")
    assert promotion is PieceType.KNIGHT
