# 西洋棋引擎（Stockfish）

「人 vs 電腦」模式需要 [Stockfish](https://stockfishchess.org/) 這個西洋棋引擎，
但它的執行檔太大（超過 100MB），不適合放進版本控制，所以這個資料夾不會被
提交到 Git（`.gitignore` 已排除，只保留這份說明文件）。

## 安裝步驟（Windows）

1. 到 Stockfish 官方 GitHub Releases 下載最新版：
   <https://github.com/official-stockfish/Stockfish/releases>
   選擇 `stockfish-windows-x86-64-universal.zip`（或符合你系統的版本）。
2. 解壓縮後，把裡面的執行檔重新命名為 `stockfish.exe`，放到：

   ```
   chess-game/
   └── engines/
       └── stockfish/
           └── stockfish.exe
   ```

3. 啟動遊戲、在對局設定畫面選擇「人 vs 電腦」即可。若找不到執行檔，
   遊戲會顯示錯誤訊息並停留在設定畫面，不會直接崩潰。

## 其他作業系統 / 自訂路徑

- macOS / Linux：下載對應平台的版本，一樣放到
  `engines/stockfish/stockfish`（不需要 `.exe` 副檔名），並確認有執行權限
  （`chmod +x`）。
- 若想放在別的位置，可以在建立 `UciEngine` 時傳入 `path` 參數
  （見 `chess_game/engine.py` 的 `DEFAULT_ENGINE_PATH`）。

## 授權

Stockfish 採用 [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html) 授權，
完全免費、開放原始碼。本專案僅透過標準 UCI 協定（文字指令）與獨立的
Stockfish 子程序溝通，不修改、不重新散布其原始碼。
