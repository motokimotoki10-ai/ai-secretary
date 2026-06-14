# AI秘書 v4.8 引き継ぎメモ

## 正本

```text
C:\Users\USER\OneDrive\ドキュメント\AI研究所作り\ai_secretary_v01
```

作業対象はこのフォルダのみ。

## 現在のバージョン

```text
AI秘書 v4.8
```

## 技術構成

- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
- PWA最小対応
- iPhone同一Wi-Fiアクセス対応

## 起動

```powershell
python app.py
```

アクセス:

```text
PC: http://127.0.0.1:5000
iPhone: http://192.168.11.5:5000
```

## 完成済み機能

- 簡易利用キー
- PWA設定
- 見やすさ設定
- テキスト入力
- ToDo抽出
- 期限抽出
- 優先順位A/B/C
- タスク保存
- タスク完了
- タスク削除
- 今日の重要タスク表示
- 期限超過/今日までタスク表示
- 期限通知
- 音声入力
- カメラ記録入口
- 録音メモ
- 録音・文字起こし操作案内
- 録音保存
- Whisper文字起こし
- 文字起こし結果の編集
- 文字起こし履歴保存
- 会話履歴一覧
- 会話履歴削除
- 会話からToDo候補抽出
- 整理結果のToDo保存
- 予定候補抽出
- 予定候補保存
- 予定一覧DB保存
- 予定削除
- 近い予定表示
- 24時間以内予定の強調
- Googleカレンダー連携準備
- 名刺OCR本体
- 写真を撮る・選ぶ案内
- 名刺OCR結果の候補自動入力
- 名刺連絡先候補保存
- 連絡先一覧
- 連絡先検索
- 連絡帳用出力
- VCFダウンロード
- 連絡先削除
- 今日の秘書レポート
- 秘書からの提案
- 秘書に相談
- AI要約
- 音声計算機
- お金管理
- 天気
- 移動サポート
- 運気カレンダー
- 文章作成
- 保存済みデータからの文章候補提案
- AI拡張設定
- iPhone向け表示調整

## 未実装機能

- AI API連携の本格実装
- ローカルAI本体の導入
- 音声計算機
- お金管理
- 通知の本格実装
- OCR精度の本格チューニング
- 連絡先の編集
- 予定の編集
- データバックアップ/エクスポート

## DB一覧

DB:

```text
secretary.db
```

テーブル:

- `secretary_tasks`
  - ToDo、期限、優先順位、状態、元テキスト
- `secretary_schedule`
  - 予定タイトル、予定日時
- `secretary_transcripts`
  - 文字起こし履歴
- `secretary_contacts`
  - 連絡先
- `secretary_money`
  - 収入/支出、金額、内容、作成日時

DB構造はv3.3時点で変更不要。

## 主要ファイル一覧

- `app.py`
  - Flask本体、DB処理、抽出ロジック、OCR、要約、相談、秘書レポート
- `templates/index.html`
  - ページ全体
- `templates/components/home.html`
  - ホーム構成
- `templates/components/secretary_report.html`
  - 今日の秘書レポート、秘書提案
- `templates/components/deadline_notifications.html`
  - 期限通知
- `templates/components/secretary_consult.html`
  - 秘書に相談
- `templates/components/voice_calculator.html`
  - 音声計算機
- `templates/components/money_manager.html`
  - お金管理
- `templates/components/weather.html`
  - 天気
- `templates/components/travel_support.html`
  - 移動サポート
- `templates/components/fortune_calendar.html`
  - 運気カレンダー
- `templates/components/document_writer.html`
  - 文章作成、文章候補提案
- `templates/components/ai_extension_settings.html`
  - AI拡張設定、ローカルAI準備説明
- `templates/components/recording_memo.html`
  - 録音、文字起こし、編集、要約、整理、操作案内
- `templates/components/transcript_list.html`
  - 会話履歴
- `templates/components/business_card_ocr.html`
  - 名刺OCR、写真選択案内
- `templates/components/contact_list.html`
  - 連絡先一覧、検索、連絡帳用出力、VCFダウンロード
- `templates/components/google_calendar_connect.html`
  - Googleカレンダー連携準備案内
- `templates/components/schedule_list.html`
  - 予定一覧、Googleカレンダー登録準備ボタン
- `static/style.css`
  - 全体デザイン、スマホ対応
- `static/recording.js`
  - 録音、文字起こし、編集、整理、保存
- `static/summary.js`
  - 要約処理
- `static/consult.js`
  - 秘書相談、回答履歴
- `static/calculator.js`
  - 音声計算機
- `static/weather.js`
  - 天気取得
- `static/travel.js`
  - 移動サポート
- `static/google_calendar.js`
  - Googleカレンダー準備中表示
- `static/fortune.js`
  - 今月の運気一覧表示切り替え
- `static/writer.js`
  - 文章生成、候補反映、コピー
- `static/business_card_ocr.js`
  - 名刺OCR、連絡先保存、連絡先検索
- `static/license.js`
  - 利用キー
- `static/pwa.js`
  - Service Worker登録
- `static/manifest.json`
  - PWA manifest
- `static/service-worker.js`
  - PWAキャッシュ
- `requirements.txt`
  - Python依存
- `settings.json`
  - 利用キー、ブランド、秘書キャラ設定

## 注意点

- Tesseract OCR本体はPythonライブラリとは別にPCへ導入が必要。
- `pytesseract` と `Pillow` は `requirements.txt` に記載済み。
- 文字起こしは `openai-whisper` を使用。
- `uploads/audio/` に録音ファイルが残る。
- `secretary.db` は作業前にバックアップすると安全。
- `192.168.11.5` はPCのIPなので変わる可能性あり。
- 触らないもの:
  - `パイソンAI.py`
  - `bot.py`
  - `研究所Bot`

## 作業後チェック

1. 保存
2. `python -m py_compile app.py`
3. `python app.py` 起動確認
4. `http://127.0.0.1:5000` 表示確認
5. 必要なら iPhone で `http://192.168.11.5:5000` 確認

## 今後の候補

- v4.1 AI API連携
