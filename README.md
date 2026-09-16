# Chess Game（西洋棋遊戲）

使用 Python + Pygame 開發的西洋棋遊戲。棋盤規則（走法、將軍、將死、逼和、
易位、吃過路兵、兵升變）皆為從零實作，未依賴 `python-chess` 等現成套件，
方便深入理解與自由客製化規則邏輯。

本專案預計搭配 **VS Code** 與 **Claude Code** 進行開發（詳見 `CLAUDE.md`）。

## 目前功能

- 標準西洋棋初始擺位
- 六種棋子完整走法規則
- 將軍 / 將死 / 逼和偵測
- 特殊規則：易位（Castling）、吃過路兵（En Passant）、兵升變（Promotion）
- Pygame 圖形介面：點擊選子、顯示可走格提示、按 `R` 重新開始
- 命令列（CLI）文字介面：輸入如 `e2e4` 的走法
- 基礎單元測試（pytest）

## 環境需求

- Python 3.10 以上
- pip

## 安裝步驟

```bash
# 1. 建立虛擬環境
python -m venv venv

# 2. 啟用虛擬環境
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. 安裝套件（開發用，含 pytest / black / flake8）
pip install -r requirements-dev.txt

# 若只想安裝執行遊戲所需的套件
pip install -r requirements.txt
```

## 執行遊戲

```bash
# 圖形介面（預設）
python main.py

# 命令列文字介面
python main.py --mode cli
```

圖形介面操作方式：點擊己方棋子選取，會以綠色高亮顯示所有合法可走的格子，
再點擊目標格子即可完成走棋；按 `R` 鍵可重新開始一局。

## 執行測試

```bash
pytest tests -v
```

## 專案結構

```
chess-game/
├── main.py                  # 程式進入點（GUI / CLI 切換）
├── chess_game/
│   ├── constants.py          # 棋盤與畫面常數設定
│   ├── board.py               # 棋盤狀態（棋子擺放、易位權、吃過路兵目標格）
│   ├── pieces.py               # 棋子定義與各棋子的走法產生邏輯
│   ├── moves.py                  # Move 資料結構（描述一步棋）
│   ├── rules.py                    # 完整規則邏輯（將軍/將死/逼和、合法走法過濾）
│   ├── game.py                       # Game 類別：整合以上模組、管理回合與遊戲狀態
│   └── gui/
│       ├── app.py                      # Pygame 事件迴圈與互動邏輯
│       └── renderer.py                  # 棋盤與棋子繪製
├── assets/images/            # 棋子圖片素材（可選，見資料夾內 README）
├── tests/                    # pytest 單元測試
├── requirements.txt          # 執行期套件
├── requirements-dev.txt      # 開發期套件（pytest / black / flake8）
└── .vscode/                  # VS Code 專案設定（直譯器、除錯設定、建議延伸套件）
```

## 待辦事項 / 未來可擴充方向

- GUI 兵升變彈出選擇視窗（目前自動升為皇后）
- 三次重複局面和局、50 手和局規則
- 悔棋（undo）功能
- 走棋紀錄輸出為 PGN 格式
- 正式棋子美術素材
- AI 電腦對手（例如 minimax + alpha-beta 剪枝）
- 西洋棋鐘計時器

## 授權

本專案僅為個人 / 學習用途的專案框架，可自由修改與擴充。
