# 棋子圖片素材

目前程式在找不到圖片時，會自動以「圓圈 + 字母」的方式繪製棋子作為佔位圖形，
遊戲仍可正常執行與遊玩。

若之後想使用正式的棋子圖片，請將 PNG 檔放到這個資料夾，並依照以下命名規則：

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

放入圖片後不需要修改任何程式碼，`chess_game/gui/renderer.py` 會自動偵測並載入。

# 開始畫面背景圖

`menu_background.png` 是開始畫面（主選單）的背景圖，由 `chess_game/gui/app.py`
啟動時自動載入並顯示。這是用 Pygame 繪圖指令程序產生的原創圖片（漸層夜色背景、
淡淡的棋盤地板紋理、左右兩尊金色國王／皇后剪影、暈影效果），沒有版權疑慮，
若想更換，直接以同檔名 PNG 覆蓋即可，不需修改程式碼。
