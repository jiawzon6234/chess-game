# 音效素材

以下四個短音效由 `chess_game/gui/sound_effects.py` 載入，並在對應的遊戲事件觸發：

| 檔名 | 觸發時機 |
| --- | --- |
| `click.ogg` | 按下選單／設定畫面上的按鈕 |
| `move.ogg` | 成功走一步棋 |
| `restart.ogg` | 遊戲中按下 `R` 重新開始 |
| `game_over.ogg` | 將死或逼和，棋局結束 |

音效音量可在遊戲內「設定」畫面獨立調整，與背景音樂音量分開控制。

## 來源與授權

- 素材包：Interface Sounds（`kenney_interfaceSounds.zip`）
- 作者：Kenney（<https://www.kenney.nl>）
- 來源：<https://opengameart.org/content/interface-sounds>
- 授權：[CC0 1.0（公有領域）](https://creativecommons.org/publicdomain/zero/1.0/)，
  可自由使用於個人或商業專案，不需標註來源（此處標註僅為感謝創作者）。
- 對應關係（素材包內原始檔名 → 本專案檔名）：
  - `click_001.ogg` → `click.ogg`
  - `drop_002.ogg` → `move.ogg`
  - `switch_004.ogg` → `restart.ogg`
  - `confirmation_002.ogg` → `game_over.ogg`

若想更換音效，直接以同檔名覆蓋對應檔案即可，不需修改程式碼。
