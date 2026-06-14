# AI秘書 プレゼント版

毎日の予定、メモ、会話、名刺、お金をまとめて整える、スマホ向けのAI秘書アプリです。

## すぐ使う手順

```powershell
python app.py
```

起動後、ブラウザで開きます。

```text
http://127.0.0.1:5000
```

iPhoneで使う場合は、PCと同じWi-Fiにつなぎ、PCのIPアドレスを使ったURLを開きます。

```text
例: http://192.168.xx.xx:5000
```

初回に利用キーを求められたら、設定済みの利用キーを入力します。

## 渡す相手向けの説明

このアプリは、予定確認、会話メモ、名刺登録、お金の記録をひとつにまとめたAI秘書です。

ホームのマイクから話しかけると、内容に応じて予定、支出、メモ、名刺などの候補を出します。
録音が使えない環境でも、文字入力や録音ファイル選択で使えます。

詳しい使い方は `プレゼント版_使い方メモ.md` を見てください。

---

# 詳細メモ

Python / Flask / SQLite で動くローカルAI秘書アプリです。
プレゼント用の完成候補として、外部設定なしでも基本機能を使える構成です。

現在到達点:

```text
AI Secretary v5.7
```

## 完成固定方針

AI Secretary v5.7 は、プレゼント版の完成候補として固定します。

- PWA対応済み
- iPhoneホーム画面追加案内対応済み
- アプリ風ホーム画面対応済み
- 固定ヘッダー、下部タブメニュー対応済み
- ようこそガイド、アプリ情報、更新履歴、お知らせページ対応済み
- 今後は小改善、文言調整、デザイン調整、不具合修正を中心に行う

大きな別機能はAI Secretary本体へ混ぜず、別プロジェクトとして作成します。

正本フォルダ:

```text
C:\Users\USER\OneDrive\ドキュメント\AI研究所作り\ai_secretary_v01
```

## 起動方法

初回またはライブラリ更新時:

```powershell
python -m pip install -r requirements.txt
```

起動:

```powershell
python app.py
```

アクセス:

```text
PC: http://127.0.0.1:5000
iPhone: http://192.168.11.5:5000
```

iPhoneアクセスはPCとiPhoneが同じWi-Fiにいる前提です。PC側IPが変わった場合はURLも変わります。

## 主要機能

### 外部設定なしで使える機能

- テキスト入力からToDo抽出
- 期限抽出
- 優先順位A/B/C付与
- タスク保存、完了、削除
- 今日の重要タスク表示
- 期限超過/今日までタスク表示
- 期限通知
- 音声入力
- カメラ記録入口
- 録音メモ
- 録音・文字起こし操作案内
- 録音保存
- Whisperによる文字起こし
- 文字起こし結果の編集
- 文字起こし履歴保存、削除
- 会話からToDo候補抽出
- 会話から予定候補抽出
- ToDo候補保存
- 予定候補保存、一覧表示、削除
- 近い予定表示
- Googleカレンダー連携準備画面
- 名刺OCR
- 写真を撮る・選ぶ案内
- 連絡先候補保存
- 連絡先一覧、検索、削除
- 連絡帳用出力、VCFダウンロード
- 今日の秘書レポート
- 秘書からの提案
- 秘書に相談
- 文字起こし/会話履歴のルールベース要約
- 音声計算機
- お金管理
- 天気
- 移動サポート
- 運気カレンダー
- 文章作成
- 保存済みデータからの文章候補提案
- AI拡張設定
- 見やすさ設定
- 簡易利用キー
- PWA最小対応

### 任意設定で使う機能・追加予定

- Googleカレンダー連携
  - 任意連携
  - Google設定なしでもアプリ本体は利用可能
  - AI秘書の予定をGoogleカレンダーへ登録
  - Googleカレンダーの今後の予定を画面表示
  - 本格同期や予定変更反映は今後追加予定
- OpenAI API連携
  - 任意追加予定
  - 現在は未接続
- ローカルAI連携
  - 任意追加予定
  - 現在は未接続

## フォルダ構成

```text
ai_secretary_v01/
  app.py
  secretary.db
  settings.json
  requirements.txt
  README.md
  HANDOFF_AI_SECRETARY_v3.3.md
  HANDOFF_AI_SECRETARY_v4.8.md
  templates/
    index.html
    components/
  static/
    style.css
    manifest.json
    service-worker.js
    pwa.js
    license.js
    voice.js
    recording.js
    summary.js
    consult.js
    calculator.js
    weather.js
    travel.js
    google_calendar.js
    fortune.js
    writer.js
    business_card_ocr.js
    camera.js
    display_settings.js
  uploads/
    audio/
  _runtime/
    bin/
```

## DB構成

DBファイル:

```text
secretary.db
```

主なテーブル:

- `secretary_tasks`
  - ToDo、期限、優先順位、状態、元テキストを保存
- `secretary_schedule`
  - 予定タイトル、予定日時を保存
- `secretary_transcripts`
  - 文字起こし履歴を保存
- `secretary_contacts`
  - 名刺/連絡先候補を保存
- `secretary_money`
  - 収入/支出、金額、内容を保存

## 利用キー

起動後、最初に利用キー入力画面が出ます。

ローカル利用では `settings.json`、公開利用では環境変数 `AI_SECRETARY_LICENSE_KEY` で管理します。
認証状態はブラウザの `localStorage` に保存されます。

## PWA

`static/manifest.json` と `static/service-worker.js` によりPWA対応しています。

スマホではホーム画面に追加するとアプリのように起動できます。
iPhone向けにSafariで「共有ボタン → ホーム画面に追加」する案内を表示しています。
オフライン完全対応ではなく、ローカルFlaskサーバー起動中の利用を前提にしています。

## アプリ風ホーム

プレゼント版として、Webページ風ではなくiPhoneアプリ風に近づけています。

- 上部固定ヘッダー
- 下部固定タブメニュー
- ホーム主要カード
- 利用ガイド、機能、設定・連携の分類メニュー
- スマホで押しやすいボタン配置

## 録音・文字起こし

録音メモでブラウザから音声録音できます。
画面内に録音開始、録音停止、録音保存、文字起こしの手順を表示しています。

流れ:

```text
録音開始
↓
録音停止
↓
録音を保存
↓
会話を文字にする
↓
文字起こし履歴へ保存
```

文字起こしには `openai-whisper` を使用します。音声変換用に `imageio-ffmpeg` と `_runtime/bin/ffmpeg.exe` を利用します。
文字起こし結果は画面上で修正でき、修正後の文章を要約と整理に利用できます。

## 名刺OCR

名刺画像を選択し、OCR実行で文字を読み取ります。
名刺OCRとカメラ記録では、iPhoneで写真を撮る、または写真を選ぶ操作案内を表示しています。
保存済み連絡先は連絡帳用の1画面表示とVCFダウンロードに対応しています。

使用ライブラリ:

- `pytesseract`
- `Pillow`

抽出対象:

- 氏名
- 会社名
- 電話番号
- メールアドレス

Tesseract OCR本体がPCに未導入の場合は、アプリ上で未導入案内を表示します。OCR後の候補は手動修正してから連絡先として保存できます。

## Googleカレンダー連携（任意・準備中）

Googleカレンダー連携はプレゼント用の必須機能ではありません。
設定しなくても、ToDo、予定管理、録音、文字起こし、連絡先、文章作成、お金管理などはそのまま使えます。

- Googleログイン開始ルートを実装済み
- OAuthコールバックルートを実装済み
- `google_calendar_token.json` の有無で接続状態を表示
- 予定一覧にGoogleカレンダーへ登録ボタンを表示
- AI秘書の予定をGoogleカレンダーへ片方向登録
- Googleカレンダーの今後の予定を表示
- AI秘書DBへの自動保存、双方向同期、予定変更反映は未実装

任意で使う場合の準備手順:

1. `pip install -r requirements.txt` を実行する
2. Google Cloud ConsoleでGoogle Calendar APIを有効化する
3. OAuthクライアントIDを作成する
4. リダイレクトURIに `http://127.0.0.1:5000/google-calendar/callback` を追加する
5. ダウンロードしたJSONを `google_client_secret.json` にリネームする
6. `google_client_secret.json` を正本フォルダ直下に配置する
7. アプリを起動し、「Googleログイン開始」を押す

必要ライブラリ:

- `google-api-python-client`
- `google-auth`
- `google-auth-oauthlib`

## AI秘書モード

AI APIは使わず、DB内の情報からルールベースで秘書機能を作っています。
OpenAI APIやローカルAIは任意追加予定です。現時点では外部AI設定なしで使えます。

今日の秘書レポート:

- 本日の予定
- 期限が近いタスク
- 最近の会話
- 最近の連絡先
- 今日やること

秘書からの提案:

- 期限が近いタスク
- 24時間以内の予定
- 未完了タスク件数
- 最近の会話内のToDo候補

秘書に相談:

- 質問入力に対してルールベースで回答
- 未完了タスク、期限付きタスク、近い予定、最近の会話、秘書提案を参照
- 回答履歴は画面内に最新5件まで表示

AI要約:

- 文字起こし結果または会話履歴を要約
- 最初の3文、ToDo候補、予定候補を使って構成

お金管理:

- 支出/収入を記録
- 今月の収入、支出、差額を表示
- 最新10件を表示
- 記録削除に対応

天気:

- 都市名からOpen-Meteoで天気を取得
- 今日と明日の天気、最高気温、最低気温を表示
- 更新時刻を表示

移動サポート:

- 岡山、大阪、名古屋、東京、福岡、鹿児島の主要都市に対応
- 新幹線、車、高速バス、飛行機の所要時間と料金目安を表示
- ルールベースでおすすめ移動手段を表示
- APIなし

運気カレンダー:

- 今日の日付、六曜、吉日を表示
- 一粒万倍日、天赦日、寅の日、巳の日などを表示
- 今月の運気一覧を表示
- APIなし、ローカル計算/データテーブル方式

文章作成:

- お礼、謝罪、営業、アポ依頼、面談後フォロー、自由入力に対応
- 相手名と内容からテンプレート文章を生成
- 生成文章のコピーに対応
- 最近の会話、連絡先、近い予定、ToDoからおすすめ文章を提案
- AI APIなし

AI拡張設定:

- 現在のAIモードを表示
- 標準モード、ローカルAIモード、OpenAI APIモードの選択肢を表示
- ローカルAIやOpenAI APIで将来できることを表示
- ローカルAI本体/API接続は任意追加予定
- 標準モードは外部設定なしで利用可能

## 別プロジェクト扱い

次の機能はAI Secretary本体には混ぜず、別プロジェクトとして作成します。

- YouTube自動投稿
- ホームページ制作
- 見積書アプリ
- 請求書アプリ

## 今後方針

AI Secretary v5.7 以降は、完成候補を壊さない範囲で進めます。

- 小改善
- デザイン調整
- 文言調整
- iPhone実機での見やすさ調整
- 不具合修正
- 任意連携の説明整理

大きな新機能追加は、必要に応じて別フォルダ・別アプリで作成します。

## 作業後チェック

```powershell
python -m py_compile app.py
python app.py
```

表示確認:

```text
http://127.0.0.1:5000
```

iPhone確認:

```text
http://192.168.11.5:5000
```

## 名刺OCRを使う準備

名刺OCRは、Pythonライブラリだけでは動きません。PC本体に `Tesseract OCR` を入れる必要があります。

すでに `requirements.txt` には以下を入れています。

- `pytesseract`
- `Pillow`

Windowsでの準備:

1. Tesseract OCR for Windows をインストールする
2. インストール時に日本語データを追加する
3. 例: `C:\Program Files\Tesseract-OCR\tesseract.exe` ができているか確認する
4. Windowsの環境変数 `Path` に `C:\Program Files\Tesseract-OCR` を追加する
5. PowerShellを開き直して、以下を確認する

```powershell
tesseract --version
```

日本語OCRも使う場合は、以下も確認します。

```powershell
tesseract --list-langs
```

`jpn` と `eng` が表示されれば準備完了です。

未導入のままOCR実行を押しても、アプリは落ちません。画面に「OCR本体が未導入です」と表示されます。  
その場合でも、名刺情報を手入力して連絡先保存、iPhone連絡帳用 `.vcf` 出力は使えます。

## URLで渡す公開方法

相手にURLを送るだけで使ってもらう場合は、Render公開を推奨します。

- HTTPS付きURLで開ける
- iPhoneのSafariで開ける
- ホーム画面に追加できる
- 無料プランから試せる
- Flaskアプリをそのまま公開しやすい

公開用の軽量設定として、以下を追加しています。

- `requirements-web.txt`
- `Procfile`
- `render.yaml`
- `URL公開_簡単メモ.md`

Renderでは以下の設定を使います。

```text
Build Command: pip install -r requirements-web.txt
Start Command: gunicorn app:app
```

Environment Variables に以下を設定します。

```text
AI_SECRETARY_LICENSE_KEY=相手に伝える利用キー
```

公開された `https://...onrender.com` のURLをiPhoneに送れば、Safariで開けます。
Safariの共有ボタンから「ホーム画面に追加」を選ぶと、アプリのように起動できます。

無料プランでは、しばらく使わないと休止し、次回表示に時間がかかることがあります。
保存データや録音ファイルを長く残したい場合は、有料プラン、永続ディスク、または外部DBを検討します。
