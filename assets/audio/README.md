# 背景音樂素材

`background_music.ogg` 為遊戲的背景音樂，會在 `chess_game/gui/app.py` 啟動時
自動循環播放，音量可在遊戲內「設定」畫面調整。

## 來源與授權

- 曲名：First Light Particles
- 作者：Yoiyami
- 來源：<https://opengameart.org/content/first-light-particles-%E2%80%93-cc0-atmospheric-pianoambient-track>
- 授權：[CC0 1.0（公有領域）](https://creativecommons.org/publicdomain/zero/1.0/)，
  可自由使用於個人或商業專案，不需標註來源（此處標註僅為感謝創作者）。
- 說明：柔和的鋼琴氛圍曲，原作者標註為 calm / peaceful / relaxing，適合作為
  西洋棋這類需要專注思考的遊戲的背景音樂。
- 備註：原始素材為 25.3MB 的 WAV 檔，為避免版本庫過大，已用 ffmpeg 轉為
  OGG Vorbis（約 1.1MB），音質幾乎無感差異。

若想更換背景音樂，直接以同檔名 `background_music.ogg` 覆蓋這個檔案即可，
不需修改程式碼。
