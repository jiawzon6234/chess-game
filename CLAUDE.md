# CLAUDE.md

本文件提供給在此專案中工作的 Claude Code 使用，說明專案背景、架構與慣例。

## 專案概述

Python + Pygame 開發的西洋棋遊戲。棋規邏輯（走法、將軍、將死、逼和、易位、
吃過路兵、兵升變）完全從零實作，未使用 `python-chess` 等現成套件。

## 常用開發指令

```bash
# 建立 / 啟用虛擬環境
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 安裝套件（開發用）
pip install -r requirements-dev.txt

# 執行遊戲
python main.py               # 圖形介面
python main.py --mode cli    # 命令列介面

# 執行測試
pytest tests -v

# 格式化 / 靜態檢查
black .
flake8 .
```

## 架構說明

- `chess_game/constants.py`：棋盤大小、顏色、視窗大小等常數。
- `chess_game/board.py`：`Board` 類別，儲存 8x8 棋子陣列、易位權、
  吃過路兵目標格、回合資訊；提供代數記譜（如 `"e4"`）與內部座標
  `(row, col)` 互轉的靜態方法。
- `chess_game/pieces.py`：`Piece`、`Color`、`PieceType` 定義，以及每種
  棋子的「虛擬合法走法（pseudo-legal moves）」產生邏輯——只考慮棋子
  本身的走法規則，尚未檢查走完後是否會讓己方國王被將軍。
- `chess_game/moves.py`：`Move` 資料類別，描述一步棋的起點、終點、
  吃子、升變、易位、吃過路兵等旗標。
- `chess_game/rules.py`：規則層，包含攻擊格偵測（`is_square_attacked`）、
  將軍/將死/逼和判斷、把「虛擬合法走法」過濾成「真正合法走法」
  （`generate_legal_moves`），以及把一步棋套用到棋盤上（`apply_move`，
  內含易位、吃過路兵、升變、易位權與吃過路兵目標格的狀態更新）。
- `chess_game/game.py`：`Game` 類別，整合以上模組，對外提供
  `legal_moves_for(pos)`、`make_move(from_pos, to_pos)`、
  `is_game_over()` 等介面，並管理走棋歷史與遊戲狀態
  （進行中 / 將死 / 逼和）。
- `chess_game/gui/`：Pygame 圖形介面。`renderer.py` 負責繪製棋盤與棋子
  （若 `assets/images/` 無對應圖片，會退回畫圓圈+字母的佔位圖形）；
  `app.py` 負責事件迴圈與滑鼠點擊選子/走棋的互動邏輯。

## 座標系統

- `board.grid[row][col]`
- `row == 0` 對應棋盤最上方（黑方底線，第 8 列）
- `row == 7` 對應棋盤最下方（白方底線，第 1 列）
- `col == 0` 對應 a 檔，`col == 7` 對應 h 檔
- 使用 `Board.square_to_pos("e4")` / `Board.pos_to_square((row, col))`
  在代數記譜與內部座標間轉換

## 目前已完成

- 標準初始棋局擺放
- 六種棋子完整走法邏輯（含吃過路兵、易位、兵升變）
- 將軍 / 將死 / 逼和偵測
- Pygame 圖形介面（點擊選子、顯示可走格提示）
- 命令列文字介面（輸入如 `e2e4` 的走法）
- 基礎單元測試（`tests/`）

## 待辦（TODO）/ 可擴充方向

- GUI 升變彈出選擇視窗（目前自動升為皇后）
- 三次重複局面和局、50 手和局規則
- 悔棋（undo）功能
- 走棋紀錄輸出為 PGN
- 正式棋子圖片素材（放入 `assets/images/`，檔名如 `wK.png`、`bQ.png`）
- AI / 電腦對手（例如 minimax + alpha-beta 剪枝）
- 西洋棋鐘計時器

## 開發慣例

- 目標 Python 版本：3.10+
- 新增功能請優先在 `tests/` 補上對應的 pytest 測試
- 修改規則邏輯（`rules.py` / `pieces.py`）後，務必執行 `pytest tests -v`
  確認既有測試（含經典的學者將死、逼和、吃過路兵測試）仍然通過
- 提交前建議先跑 `black .` 統一格式
