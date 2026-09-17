import os

import pytest

from chess_game.engine import DEFAULT_ENGINE_PATH, EngineError, UciEngine

_ENGINE_AVAILABLE = os.path.isfile(DEFAULT_ENGINE_PATH)

requires_engine = pytest.mark.skipif(
    not _ENGINE_AVAILABLE,
    reason="找不到 engines/stockfish/stockfish.exe，需先安裝才能跑這些整合測試",
)


def test_missing_binary_raises_engine_error():
    with pytest.raises(EngineError):
        UciEngine(path="這個路徑不存在/stockfish.exe")


@requires_engine
def test_engine_starts_and_quits_cleanly():
    engine = UciEngine(skill_level=1, movetime_ms=100)
    engine.quit()
    # quit() 應可安全重複呼叫。
    engine.quit()


@requires_engine
def test_best_move_from_starting_position_is_plausible():
    engine = UciEngine(skill_level=1, movetime_ms=100)
    try:
        move = engine.best_move([])
    finally:
        engine.quit()

    assert len(move) in (4, 5)
    from_square, to_square = move[0:2], move[2:4]
    assert from_square[0] in "abcdefgh" and from_square[1] in "12345678"
    assert to_square[0] in "abcdefgh" and to_square[1] in "12345678"


@requires_engine
def test_best_move_reacts_to_given_move_list():
    engine = UciEngine(skill_level=1, movetime_ms=100)
    try:
        opening_move = engine.best_move([])
        reply = engine.best_move([opening_move, "a7a6"])
    finally:
        engine.quit()

    assert reply != opening_move  # 換黑方剛走完 a6，白方不會重複同一步


@requires_engine
def test_best_move_finds_mate_in_one():
    """經典「學者將死」局面差一步：讓引擎找出 Qxf7#（e7 或 f2 等其他子力
    不會擋到，Stockfish 在任何難度下都應找出唯一的將死走法）。"""
    engine = UciEngine(skill_level=20, movetime_ms=300)
    try:
        moves = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6"]
        move = engine.best_move(moves)
    finally:
        engine.quit()

    assert move == "h5f7"
