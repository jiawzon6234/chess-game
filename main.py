#!/usr/bin/env python3
"""西洋棋遊戲進入點。

用法：
    python main.py            # 預設啟動 Pygame 圖形介面
    python main.py --mode gui # 同上
    python main.py --mode cli # 啟動命令列文字介面
"""

import argparse

from chess_game.board import Board
from chess_game.game import Game, GameStatus


def print_board(board: Board) -> None:
    print()
    for row in range(8):
        rank_label = 8 - row
        cells = [(piece.symbol if piece else ".") for piece in board.grid[row]]
        print(f"{rank_label} " + " ".join(cells))
    print("  " + " ".join("abcdefgh"))
    print()


def run_cli() -> None:
    game = Game()
    print("=== 西洋棋 CLI 模式 ===")
    print("走法格式為起點+終點座標，例如 e2e4；輸入 quit 離開。\n")

    while not game.is_game_over():
        print_board(game.board)
        turn_name = "白方 (White)" if game.turn.value == "white" else "黑方 (Black)"
        move_str = input(f"{turn_name} 走棋: ").strip()

        if move_str.lower() in ("quit", "exit"):
            print("已離開遊戲。")
            return

        if len(move_str) not in (4, 5):
            print("格式錯誤，請輸入如 e2e4 的走法。")
            continue

        try:
            from_pos = Board.square_to_pos(move_str[0:2])
            to_pos = Board.square_to_pos(move_str[2:4])
        except (IndexError, ValueError):
            print("無法解析座標，請確認輸入格式。")
            continue

        if not game.make_move(from_pos, to_pos):
            print("不合法的走法，請再試一次。")

    print_board(game.board)
    if game.status == GameStatus.CHECKMATE:
        winner_name = "白方" if game.winner.value == "white" else "黑方"
        print(f"將死！{winner_name}獲勝。")
    elif game.status == GameStatus.STALEMATE:
        print("和棋（逼和）。")
    elif game.status == GameStatus.DRAW_BY_REPETITION:
        print("和棋（三次重複局面）。")
    elif game.status == GameStatus.DRAW_BY_FIFTY_MOVE_RULE:
        print("和棋（50 手和局規則）。")


def main() -> None:
    parser = argparse.ArgumentParser(description="西洋棋遊戲")
    parser.add_argument(
        "--mode",
        choices=["gui", "cli"],
        default="gui",
        help="選擇介面模式，預設為 gui（圖形介面）",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        run_cli()
    else:
        from chess_game.gui.app import run

        run()


if __name__ == "__main__":
    main()
