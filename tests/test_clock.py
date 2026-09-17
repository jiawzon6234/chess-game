from chess_game.clock import ChessClock, DEFAULT_TIME_LIMIT_SECONDS
from chess_game.pieces import Color


def test_default_time_limit_is_five_minutes():
    assert DEFAULT_TIME_LIMIT_SECONDS == 5 * 60
    clock = ChessClock()
    assert clock.remaining[Color.WHITE] == 300
    assert clock.remaining[Color.BLACK] == 300


def test_tick_only_decreases_active_color():
    clock = ChessClock(60)
    clock.tick(Color.WHITE, 10)
    assert clock.remaining[Color.WHITE] == 50
    assert clock.remaining[Color.BLACK] == 60


def test_tick_marks_timed_out_when_reaching_zero():
    clock = ChessClock(5)
    clock.tick(Color.WHITE, 5)
    assert clock.remaining[Color.WHITE] == 0
    assert clock.is_time_up(Color.WHITE)
    assert clock.timed_out_color is Color.WHITE


def test_tick_never_goes_negative():
    clock = ChessClock(5)
    clock.tick(Color.WHITE, 999)
    assert clock.remaining[Color.WHITE] == 0


def test_tick_ignored_once_timed_out():
    clock = ChessClock(5)
    clock.tick(Color.WHITE, 5)
    assert clock.timed_out_color is Color.WHITE

    clock.tick(Color.BLACK, 3)  # 一方已超時後，計時不應再變動任何一方
    assert clock.remaining[Color.BLACK] == 5
    assert clock.timed_out_color is Color.WHITE


def test_unlimited_time_never_times_out():
    """time_limit_seconds=inf 用來代表「無限制」，長時間流逝也不應超時。"""
    clock = ChessClock(float("inf"))
    clock.tick(Color.WHITE, 10_000_000)
    assert clock.remaining[Color.WHITE] == float("inf")
    assert clock.timed_out_color is None
    assert not clock.is_time_up(Color.WHITE)


def test_snapshot_and_restore_roundtrip():
    clock = ChessClock(60)
    clock.tick(Color.WHITE, 20)
    snapshot = clock.snapshot()

    clock.tick(Color.WHITE, 999)  # 讓白方超時
    assert clock.timed_out_color is Color.WHITE

    clock.restore(snapshot)
    assert clock.remaining[Color.WHITE] == 40
    assert clock.remaining[Color.BLACK] == 60
    assert clock.timed_out_color is None
