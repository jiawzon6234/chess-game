# 棋子圖片素材

`chess_game/gui/renderer.py` 會自動偵測並載入這個資料夾內對應檔名的 PNG，
若某個檔案不存在，該棋子會退回以「圓圈 + 字母」繪製的佔位圖形，遊戲仍可
正常執行與遊玩。目前已內建以下正式棋子圖片：

| 顏色 | 棋子 | 檔名 |
| --- | --- | --- |
| 白方 | 兵 (Pawn)   | `wP.png` |
| 白方 | 騎士 (Knight) | `wN.png` |
| 白方 | 主教 (Bishop) | `wB.png` |
| 白方 | 城堡 (Rook)   | `wR.png` |
| 白方 | 皇后 (Queen)  | `wQ.png` |
| 白方 | 國王 (King)   | `wK.png` |
| 黑方 | 兵 (Pawn)   | `bP.png` |
| 黑方 | 騎士 (Knight) | `bN.png` |
| 黑方 | 主教 (Bishop) | `bB.png` |
| 黑方 | 城堡 (Rook)   | `bR.png` |
| 黑方 | 皇后 (Queen)  | `bQ.png` |
| 黑方 | 國王 (King)   | `bK.png` |

若想更換成別的美術風格，直接以同檔名 PNG（建議帶透明背景）覆蓋即可，
不需修改任何程式碼。

## 來源與授權

- 素材包：2D Chess Pack（`sbs_-_2d_chess_pack.zip`，取用其中 `Top Down`
  塑膠材質（Plastic）棋子貼圖）
- 作者：Screaming Brain Studios
- 來源：<https://opengameart.org/content/2d-chess-pack>
- 授權：[CC0 1.0（公有領域）](https://creativecommons.org/publicdomain/zero/1.0/)，
  可自由使用於個人或商業專案，不需標註來源（此處標註僅為感謝創作者）。
- 處理方式：原始素材是一張 4x4 的貼圖（每格 128x128，多種棋子姿勢/角度），
  已用程式裁切出六種棋子各一張，並將原本的純色背景（黑／teal）去背為透明
  PNG（含邊緣去色暈處理），存成上表的檔名。

# 開始畫面背景圖

`menu_background.png` 是開始畫面（主選單）的背景圖，由 `chess_game/gui/app.py`
啟動時自動載入並顯示。這是用 Pygame 繪圖指令程序產生的原創圖片（漸層夜色背景、
淡淡的棋盤地板紋理、左右兩尊金色國王／皇后剪影、暈影效果），沒有版權疑慮，
若想更換，直接以同檔名 PNG 覆蓋即可，不需修改程式碼。
