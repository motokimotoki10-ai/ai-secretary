# AI秘書 v5.7 引き継ぎメモ

## 正本

```text
C:\Users\USER\OneDrive\ドキュメント\AI研究所作り\ai_secretary_v01
```

作業対象はこのフォルダのみ。

## 現在のバージョン

```text
AI Secretary v5.7
```

## 完成固定

AI Secretary v5.7 を、プレゼント版の完成候補として固定。

- PWA対応済み
- iPhoneホーム画面追加案内対応済み
- アプリ風ホーム対応済み
- 上部固定ヘッダー対応済み
- 下部固定タブメニュー対応済み
- ようこそガイド対応済み
- アプリ情報ページ対応済み
- 更新履歴ページ対応済み
- お知らせ・今後の機能ページ対応済み

今後は小改善、文言調整、デザイン調整、不具合修正を中心にする。
大きな新機能はAI Secretary本体へ混ぜず、別プロジェクトとして作る。

## 技術構成

- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
- PWA対応
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
- iPhoneホーム画面追加案内
- アプリ風ホーム画面
- 上部固定ヘッダー
- 下部固定タブメニュー
- ようこそガイド
- アプリ情報ページ
- 更新履歴ページ
- お知らせ・今後の機能ページ
- 見やすさ設定
- テキスト入力
- ToDo抽出、保存、完了、削除
- 期限抽出、優先順位A/B/C
- 今日の重要タスク表示
- 期限通知
- 予定候補抽出、保存、一覧表示、削除
- 近い予定表示
- Googleカレンダー連携準備画面
- Googleカレンダー予定登録
- Googleカレンダー予定表示
- 音声入力
- 録音メモ、録音保存
- Whisper文字起こし
- 文字起こし結果編集
- 文字起こし履歴保存、削除
- 会話からToDo候補、予定候補を抽出
- AI要約
- 今日の秘書レポート
- 秘書からの提案
- 秘書に相談
- 音声計算機
- お金管理
- 天気
- 移動サポート
- 運気カレンダー
- 文章作成
- 保存済みデータからの文章候補提案
- AI拡張設定
- カメラ記録入口
- 名刺OCR本体
- 名刺OCR結果の候補自動入力
- 写真を撮る・選ぶ案内
- 連絡先候補保存
- 連絡先一覧、検索、削除
- 連絡帳用出力
- VCFダウンロード

## 未完成

- Googleカレンダー双方向同期
- LINE連携
- AI API連携
- ローカルAI本体

## 別プロジェクト扱い

次はAI Secretary本体に混ぜない。

- YouTube自動投稿
- ホームページ制作
- 見積書アプリ
- 請求書アプリ

## DB一覧

- `secretary_tasks`
- `secretary_schedule`
- `secretary_transcripts`
- `secretary_contacts`
- `secretary_money`

DB構造変更なし。

## 主要ファイル

- `app.py`
  - Flask本体、DB処理、抽出ロジック、OCR、要約、相談、移動サポート、VCF出力
- `templates/index.html`
  - ページ全体、PWAメタ情報、固定ヘッダー、下部タブ
- `templates/components/home.html`
  - ホーム構成、主要カード、分類メニュー
- `templates/welcome_guide.html`
  - 初回利用者向けガイド
- `templates/app_info.html`
  - アプリ情報
- `templates/update_history.html`
  - 更新履歴
- `templates/future_features.html`
  - お知らせ・今後の機能
- `templates/components/deadline_notifications.html`
  - 期限通知
- `templates/components/google_calendar_connect.html`
  - Googleカレンダー連携準備
- `templates/components/schedule_list.html`
  - 予定一覧、Googleカレンダー登録準備ボタン
- `templates/components/contact_list.html`
  - 連絡先一覧、検索、連絡帳用出力、VCFダウンロード
- `templates/components/travel_support.html`
  - 移動サポート
- `templates/components/document_writer.html`
  - 文章作成、文章候補提案
- `templates/components/recording_memo.html`
  - 録音、文字起こし、編集、要約、整理
- `static/style.css`
  - 全体デザイン、スマホ対応
- `static/google_calendar.js`
  - Googleカレンダー案内表示
- `static/travel.js`
  - 移動サポート
- `static/business_card_ocr.js`
  - 名刺OCR、連絡先保存、検索、連絡帳用出力
- `static/recording.js`
  - 録音、文字起こし、編集、整理、保存
- `static/summary.js`
  - 要約処理
- `static/writer.js`
  - 文章生成、候補反映、コピー

## 今後方針

- 小改善
- デザイン調整
- 文言調整
- iPhone実機での見やすさ調整
- 不具合修正
- 任意連携の説明整理

大きな追加機能は別フォルダ・別アプリで作成する。

## 注意

- Google API/OAuth土台、予定登録、予定表示は実装済み。双方向同期は未実装。
- ローカルAI本体は未導入。
- YouTube自動投稿、ホームページ制作、請求書アプリ、見積書アプリは別プロジェクト扱い。
- 触る正本は `ai_secretary_v01` のみ。
- 触らない: `パイソンAI.py`、`bot.py`、`研究所Bot`

## 作業後チェック

1. 保存
2. `python -m py_compile app.py`
3. `python app.py` 起動確認
4. `http://127.0.0.1:5000` 表示確認
5. 必要なら iPhone で `http://192.168.11.5:5000` 確認
