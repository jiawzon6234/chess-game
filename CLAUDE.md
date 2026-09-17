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

- `chess_game/constants.py`：棋盤大小、顏色、視窗大小等常數。`WINDOW_SIZE`
  是棋盤/選單內容的正方形大小；實際視窗 `WINDOW_WIDTH`/`WINDOW_HEIGHT`
  在左右各加上 `SIDE_MARGIN_WIDTH` 的黑色留白區（見 `gui/app.py`）。
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
  `is_game_over()`、`undo()` / `can_undo()`、`tick(elapsed_seconds)`
  等介面，並管理走棋歷史與遊戲狀態（進行中 / 將死 / 逼和 / 三次重複
  局面和局 / 50 手和局規則 / 超時判負）。三次重複局面透過
  `position_history`（局面雜湊 → 出現次數）判斷；50 手和局規則沿用
  `board.halfmove_clock`（`rules.apply_move` 已在兵move/吃子時重置、
  其餘走法遞增）。悔棋採「每步走棋前先把 `board.clone()`、
  `clock.snapshot()` 等狀態存進 `_undo_stack`」的快照法，而非寫反向
  套用邏輯；`undo()` 不受 `is_game_over()` 限制，可悔掉導致將死/和局/
  超時的最後一步，雙方西洋棋鐘的剩餘時間也會一併還原。
- `chess_game/clock.py`：`ChessClock` 類別，追蹤雙方剩餘思考時間
  （預設每方 5 分鐘），由 `Game.tick()` 每幀呼叫推進目前輪到走棋一方
  的時間；歸零時記錄 `timed_out_color`，`Game.tick()` 據此把狀態設為
  `GameStatus.TIMEOUT` 並判對方獲勝。純邏輯層、不依賴 pygame，方便
  單元測試；CLI 模式因 `input()` 為阻塞式、無即時迴圈可驅動計時，
  目前只有 GUI 會呼叫 `tick()`。
- `chess_game/settings.py`：`Settings` 類別，管理音樂音量（`music_volume`）與
  音效音量（`sfx_volume`），存讀取於專案根目錄的 `settings.json`
  （執行期自動產生，已加入 `.gitignore`、不納入版本控制）。
- `chess_game/gui/`：Pygame 圖形介面。
  - `app.py`：主迴圈與畫面狀態機（`Screen.MENU` / `SETTINGS` / `PLAYING`），
    負責開始畫面、設定畫面、棋盤事件（滑鼠選子走棋、`R` 重新開始、
    `Ctrl+Z` 悔棋、`Esc` 回主選單）、兵升變彈出選擇視窗、背景音樂與
    音效播放時機的串接。新開局/重新開始/悔棋後會設定 `skip_next_tick`，
    避免把切換畫面當下經過的時間誤算進西洋棋鐘。
    - **版面**：選單/設定/棋盤內容統一畫在一張置中的 `content`
      （`WINDOW_SIZE x WINDOW_SIZE`）畫布上，再貼到實際視窗的中央；
      左右兩側留白區直接畫在真正的 `screen` 上，顯示黑方鐘（左上角，
      `_draw_black_clock`）、白方鐘（右下角，`_draw_white_clock`）、
      快捷鍵提示（右上角，`_draw_shortcut_hints`）。因為互動元件
      （按鈕/滑桿/棋盤格）的座標都以 `content` 為準，每幀事件迴圈一開
      頭會把滑鼠事件的 `event.pos` 平移 `-SIDE_MARGIN_WIDTH`，下游點擊
      判斷完全不需要另外處理留白區位移；`Button.draw()` 因此改為接受
      外部傳入、已平移過的 `mouse_pos`（而非直接呼叫
      `pygame.mouse.get_pos()`），避免 hover 判斷用到未平移的座標。
  - `renderer.py`：繪製棋盤與棋子（讀取 `assets/images/` 內的正式棋子
    圖片；若某檔案缺漏，該棋子會退回畫圓圈+字母的佔位圖形），並提供
    `render_piece_icon()` 供升變選擇視窗等場合繪製單一棋子圖示。
  - `fonts.py`：`get_font()`，依序嘗試系統中文字型（微軟正黑體等），
    避免預設 Arial 字型顯示中文時變成方框亂碼。
  - `screens.py`：選單／設定畫面共用的 `Button`、`Slider` UI 元件。
  - `sound_effects.py`：`SoundEffects` 類別，載入並播放四種音效
    （按鈕、走棋、重新開始、棋局結束）。

## 素材與授權

- `assets/images/menu_background.png`：開始畫面背景圖，由 Pygame 繪圖指令
  程序繪製產生（原創，非外部素材），細節見同目錄 `README.md`。
- `assets/images/{w,b}{P,N,B,R,Q,K}.png`：正式棋子圖片，取材自 CC0 授權的
  「2D Chess Pack」素材包並經去背處理，來源與處理方式見同目錄 `README.md`。
- `assets/audio/background_music.ogg`：背景音樂；`assets/audio/sfx/`：
  按鈕、走棋、重新開始、棋局結束四種音效。皆為 **CC0（公有領域）** 授權的
  外部素材，來源與作者標註於各自目錄的 `README.md`。
- 慣例：新增音樂/圖片等外部素材時，優先選擇 CC0 授權，並在同目錄
  `README.md` 記錄來源網址、作者與授權條款，方便日後追溯與替換。

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
- 開始畫面（標題 CHESS、「進入遊戲」／「設定」按鈕、程序繪製的背景封面圖）
- 設定畫面（音樂音量、音效音量各自獨立滑桿，即時套用並存檔）
- 背景音樂（開始畫面啟動時自動循環播放，CC0 素材）
- 音效（按鈕、走棋、重新開始、棋局結束，CC0 素材）
- 中文字型顯示修正（選單/設定畫面文字改用系統中文字型，避免亂碼）
- 正式棋子美術素材（取代圓圈+字母佔位圖形，CC0 素材）
- GUI 兵升變彈出選擇視窗（點選皇后/城堡/主教/騎士，取代自動升為皇后）
- 三次重複局面和局、50 手和局規則
- 悔棋（undo）功能（GUI：`Ctrl+Z`；CLI：輸入 `undo`；可多次悔棋，
  也可悔掉導致將死/和局/超時的最後一步）
- 西洋棋鐘計時器（GUI 限定；雙方各 5 分鐘，剩餘 ≤30 秒轉紅色警示；
  持棋時間歸零自動判負）
- 對局畫面兩側黑色留白區：黑方鐘（左上角）、白方鐘（右下角）、
  快捷鍵提示（右上角），棋盤內容置中不受遮擋
- 基礎單元測試（`tests/`，含 `test_game.py`／`test_clock.py`
  涵蓋上述和局規則、悔棋與西洋棋鐘）

## 待辦（TODO）/ 可擴充方向

- 走棋紀錄輸出為 PGN
- AI / 電腦對手（例如 minimax + alpha-beta 剪枝）

## 開發慣例

- 目標 Python 版本：3.10+
- 新增功能請優先在 `tests/` 補上對應的 pytest 測試
- 修改規則邏輯（`rules.py` / `pieces.py`）後，務必執行 `pytest tests -v`
  確認既有測試（含經典的學者將死、逼和、吃過路兵測試）仍然通過
- 提交前建議先跑 `black .` 統一格式
