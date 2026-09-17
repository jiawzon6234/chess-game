"""透過 UCI（Universal Chess Interface）協定與外部西洋棋引擎溝通的最小封裝。

只實作西洋棋 AI 對手需要的子集（啟動握手、設定難度、詢問最佳走法、
結束程序），不依賴 `python-chess` 等現成套件，維持本專案「規則邏輯
從零實作」的慣例——這裡只是啟動子程序、透過 stdin/stdout 傳收文字
指令，並不涉及棋規判斷。
"""

import os
import subprocess
import time

# 預設引擎執行檔位置：專案根目錄下的 engines/stockfish/stockfish.exe。
# 這個資料夾不納入版本控制（檔案過大），需另外下載安裝，見
# engines/README.md 或專案 README 的說明。
DEFAULT_ENGINE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "engines", "stockfish", "stockfish.exe"
)


class EngineError(RuntimeError):
    """引擎找不到、無法啟動，或溝通逾時/失敗時拋出。"""


class UciEngine:
    """包住一個透過 stdin/stdout 溝通的 UCI 引擎子程序（例如 Stockfish）。"""

    def __init__(
        self,
        path: str = DEFAULT_ENGINE_PATH,
        skill_level: int = 20,
        movetime_ms: int = 1000,
    ):
        if not os.path.isfile(path):
            raise EngineError("找不到西洋棋引擎，請見 README 安裝說明")

        try:
            self._process = subprocess.Popen(
                [path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except OSError:
            raise EngineError("西洋棋引擎啟動失敗，執行檔可能已損壞") from None

        self.movetime_ms = movetime_ms
        try:
            self._send("uci")
            self._wait_for("uciok")
            self.set_skill_level(skill_level)
            self._send("isready")
            self._wait_for("readyok")
            self.new_game()
        except EngineError:
            self._process.kill()
            raise

    def _send(self, command: str) -> None:
        if self._process.stdin is None or self._process.poll() is not None:
            raise EngineError("西洋棋引擎程序已結束，無法傳送指令。")
        try:
            self._process.stdin.write(command + "\n")
            self._process.stdin.flush()
        except OSError as exc:
            raise EngineError(f"傳送指令給引擎失敗：{exc}") from exc

    def _wait_for(self, token: str, timeout: float = 10.0) -> str:
        if self._process.stdout is None:
            raise EngineError("無法讀取引擎輸出。")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self._process.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line == token or line.startswith(token):
                return line
        raise EngineError(f"等待引擎回應「{token}」逾時。")

    def set_skill_level(self, skill_level: int) -> None:
        """設定引擎棋力（0 最弱、20 最強，對應 Stockfish 的 Skill Level）。"""
        skill_level = max(0, min(20, skill_level))
        self._send(f"setoption name Skill Level value {skill_level}")

    def new_game(self) -> None:
        """通知引擎開始新的一局（清空過往局面的暫存資訊）。"""
        self._send("ucinewgame")
        self._send("isready")
        self._wait_for("readyok")

    def best_move(self, moves_uci: list, movetime_ms: int = None) -> str:
        """給定目前為止的走法（UCI 記譜，如 ["e2e4", "e7e5"]），
        回傳引擎認為最佳的下一步（同樣是 UCI 記譜，如 "g1f3" 或 "e7e8q"）。
        """
        position_cmd = "position startpos"
        if moves_uci:
            position_cmd += " moves " + " ".join(moves_uci)
        self._send(position_cmd)
        self._send(f"go movetime {movetime_ms or self.movetime_ms}")

        line = self._wait_for("bestmove", timeout=(movetime_ms or self.movetime_ms) / 1000 + 10)
        parts = line.split()
        if len(parts) < 2 or parts[1] == "(none)":
            raise EngineError("引擎回報沒有合法走法可下。")
        return parts[1]

    def quit(self) -> None:
        """結束引擎子程序。可安全重複呼叫。"""
        if self._process.poll() is not None:
            return
        try:
            self._send("quit")
            self._process.wait(timeout=3)
        except Exception:
            self._process.kill()
