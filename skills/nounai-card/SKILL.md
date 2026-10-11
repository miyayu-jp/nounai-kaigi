---
name: nounai-card
description: 脳内会議が終わったあと、会議の「前」と「後」の頭の中を並べた脳内メーカー風カード（1200x675、Xに貼れるPNG）を1枚作って返す。部品は公開リポジトリ miyayu-jp/nounai-kaigi から取ってくる。
---
# 脳内会議カード

## いつ使うか
脳内会議が終わり、本人が自分で選択肢を選んだあと。会議の前と後のキャラの割合、吹き出しの一言、本人の選択がそろったとき。

## 手順
1. 部品を用意する（初回だけ）。作業フォルダ（例：`~/nounai-kaigi`）に `card.py` がなければ取ってくる。
   ```
   git clone https://github.com/miyayu-jp/nounai-kaigi.git ~/nounai-kaigi
   ```
   git が使えないときは https://github.com/miyayu-jp/nounai-kaigi/archive/refs/heads/main.zip をダウンロードして展開し、中の `nounai-kaigi-main` フォルダを作業フォルダにする。
2. Python の準備（初回だけ）。作業フォルダで:
   ```
   python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
   ```
   日本語フォントが必要。Mac はヒラギノを自動で使う。Linux は `fonts-noto-cjk`。見つからないときは環境変数 `NOUNAI_FONT` にフォントファイルのパスを入れる。APIキーは不要。
3. 会議の結果を JSON に書く（形は `examples/sample_meeting.json` と同じ）。
   - `worry`：悩みの一言
   - `before` / `after`：`weights`（キャラ名と割合。合計100でなくてよい）と `quote`（`{"name": キャラ名, "text": 一言}`、吹き出しは1つ）
   - `conclusion`：本人が選んだこと
   - `image`：任意。「その後の様子」の画像のパス（JSONからの相対パスでよい）
   - キャラ：感情・理性・不安・愛・めんどくさい・ボケ・ツッコミ・議長・ミライ。それ以外の名前は代わりのキャラで描かれる。議長は割合に入れても数えず、司会として小さく座る。
4. 作業フォルダで `. .venv/bin/activate && python3 card.py 会議結果.json card.png` を実行（1〜2秒）。
5. できた `card.png` をユーザーに返す。

## 使うときのお願い
- カードは、本人が自分で選んだあとに作る。結論を Bot が決めたように書かない（決めるのは本人）。
- 本人がとてもつらそうなときは、カードを作らずに話を聞き、身近な人や専門の相談窓口に相談するよう勧める。
