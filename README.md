# 今日の見出し ─ 日・米・中

日本・アメリカ・中国の新聞各紙の見出しだけを1枚のWebページにまとめ、**毎朝7時(日本時間)に自動更新**する仕組みです。

- 動作はすべてあなたのGitHubアカウント上で完結します(**Claudeや他の外部サービスに依存しません**)
- 完全無料(GitHubの無料枠内で動きます)
- 止めたいとき・変えたいときは、いつでも自分で操作できます

---

## 初回セットアップ(約5分・1回だけ)

### 1. GitHubにリポジトリを作る

1. [github.com](https://github.com) にログイン(アカウントがなければ無料登録)
2. 右上の「+」→「New repository」
3. Repository name に `news-digest` など好きな名前を入力
4. **Public** を選択(無料アカウントでGitHub Pagesを使うにはPublicが必要です)
5. 「Create repository」をクリック

### 2. ファイルをアップロードする

1. 作成したリポジトリのページで「uploading an existing file」リンクをクリック
   (見当たらない場合は「Add file」→「Upload files」)
2. このフォルダの中身をすべてドラッグ&ドロップ
   - `fetch_headlines.py`
   - `feeds.json`
   - `README.md`
   - `.github` フォルダ(この中の `workflows/daily.yml` が大事です)
   - ※ ブラウザによっては `.github` フォルダごとドラッグできないことがあります。その場合は「Add file」→「Create new file」でファイル名に `.github/workflows/daily.yml` と入力し、中身をコピペしてください
3. 「Commit changes」をクリック

### 3. GitHub Pages を有効にする

1. リポジトリの「Settings」→ 左メニューの「Pages」
2. 「Build and deployment」の Source を **「GitHub Actions」** に変更

### 4. 動作確認(手動で1回実行)

1. リポジトリの「Actions」タブを開く
2. 初回は「I understand my workflows, go ahead and enable them」を押して有効化
3. 左の「毎朝の見出し更新」→ 右側の「Run workflow」→ 緑のボタンをクリック
4. 1〜2分待つと完了し、`https://あなたのユーザー名.github.io/リポジトリ名/` でページが見られます
5. このURLをブックマークすれば、あとは毎朝開くだけです

---

## 日々の使い方

なにもしなくてOKです。毎朝7時ごろ(日本時間)に自動で最新の見出しに更新されます。ブックマークしたページを1日1回開いてください。

※ GitHubの仕様上、実行が数分〜30分ほど遅れることがあります。

---

## 止め方(いつでも・完全に自分で操作できます)

**一時停止したいとき:**
「Actions」タブ → 左の「毎朝の見出し更新」→ 右上の「…」→「Disable workflow」
(再開は同じ場所の「Enable workflow」)

**完全にやめたいとき:**
「Settings」→ 一番下の「Delete this repository」でリポジトリごと削除

Claudeの契約状況とは無関係に動き続け、止めるのもGitHub上の操作だけです。

---

## カスタマイズ

### 新聞を追加・削除する

`feeds.json` をGitHub上で直接編集します(ファイルを開いて鉛筆アイコン)。

- 一時的に外したい新聞は `"enabled": true` を `false` に
- 追加したい場合は同じ形式で1行足すだけ:

```json
{ "name": "新聞名", "url": "RSSフィードのURL", "enabled": true }
```

### 見出しの件数を変える

`feeds.json` の先頭にある `"max_items_per_feed": 8` の数字を変更します。

### 更新時刻を変える

`.github/workflows/daily.yml` の `cron: "0 22 * * *"` を編集します。
**時刻はUTC(日本時間−9時間)** で指定します。例:

| 日本時間 | 設定値 |
|---|---|
| 朝6時 | `"0 21 * * *"` |
| 朝7時 | `"0 22 * * *"` |
| 朝8時 | `"0 23 * * *"` |
| 正午 | `"0 3 * * *"` |

---

## 知っておくと良いこと・トラブル対応

**一部の新聞が「取得失敗」と表示される**
新聞社がフィードのURLを変更・廃止した可能性があります。ページ全体は動き続けるので、`feeds.json` からその新聞を外すか、新しいURLに差し替えてください。「(新聞名) RSS」で検索すると新しいURLが見つかることがあります。

**読売・日経・産経について**
この3紙は公式のRSS配信がない(または限定的な)ため、有志によるミラー(rss.wor.jp)のフィードを初期設定にしています。個人利用の範囲でお使いください。ミラーが停止した場合は `feeds.json` から差し替え・削除できます。

**60日間リポジトリに変更がないと、GitHubが自動実行を一時停止します**
その際はGitHubからメールが届くので、メール内のリンクまたは「Actions」タブの「Enable workflow」ボタンを1回押せば再開します。

**見出しの著作権**
見出しは各新聞社に帰属します。このページは個人で確認する用途を想定しています。

---

## ファイル構成

| ファイル | 役割 |
|---|---|
| `fetch_headlines.py` | 見出しを取得してHTMLページを生成(Python標準ライブラリのみ) |
| `feeds.json` | どの新聞から取得するかの設定 |
| `.github/workflows/daily.yml` | 毎朝の自動実行スケジュール |
| `site/index.html` | 生成される見出しページ(自動生成なので編集不要) |
