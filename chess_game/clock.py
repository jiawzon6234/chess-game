"""西洋棋鐘：追蹤雙方剩餘思考時間，時間歸零即判負（超時）。"""

from .pieces import Color

# 每方預設持棋時間：5 分鐘。
DEFAULT_TIME_LIMIT_SECONDS = 5 * 60


class ChessClock:
    """管理白/黑雙方各自的倒數計時。呼叫端(Game)須每幀呼叫 tick() 推進時間。"""

    def __init__(self, time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS):
        self.time_limit_seconds = time_limit_seconds
        self.remaining = {
            Color.WHITE: time_limit_seconds,
            Color.BLACK: time_limit_seconds,
        }
        self.timed_out_color = None  # 超時的一方 (Color)，尚未超時則為 None

    def tick(self, active_color: Color, elapsed_seconds: float) -> None:
        """讓 active_color 的剩餘時間減少 elapsed_seconds。

        若某一方已經超時，之後的 tick 不再改變狀態(需由外部判定為輸棋、
        不應該讓時間繼續變動或被另一方的超時覆蓋)。
        """
        if elapsed_seconds <= 0 or self.timed_out_color is not None:
            return

        remaining = max(0.0, self.remaining[active_color] - elapsed_seconds)
        self.remaining[active_color] = remaining
        if remaining <= 0:
            self.timed_out_color = active_color

    def is_time_up(self, color: Color) -> bool:
        return self.remaining[color] <= 0

    def snapshot(self):
        """回傳目前狀態的快照，供 Game.undo() 還原用。"""
        return (dict(self.remaining), self.timed_out_color)

    def restore(self, snapshot) -> None:
        remaining, timed_out_color = snapshot
        self.remaining = dict(remaining)
        self.timed_out_color = timed_out_color
