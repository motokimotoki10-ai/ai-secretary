# AI Secretary URL公開メモ

## おすすめ

一番簡単なのは Render です。

- URLを送るだけで使える
- HTTPSが自動で付く
- iPhoneで開ける
- Safariからホーム画面に追加できる
- 無料プランから試せる

## 公開手順

1. この `ai_secretary_v01` フォルダをGitHubへアップロードします。
2. Renderで「New Web Service」を選びます。
3. GitHubのAI Secretaryフォルダを選びます。
4. Build Command に以下を入れます。

```text
pip install -r requirements-web.txt
```

5. Start Command に以下を入れます。

```text
gunicorn app:app
```

6. Environment Variables に以下を入れます。

```text
AI_SECRETARY_LICENSE_KEY=相手に伝える利用キー
```

7. 公開された `https://...onrender.com` のURLをiPhoneへ送ります。
8. iPhoneではSafariで開き、「共有」から「ホーム画面に追加」を選びます。

## 無料プランの注意

Render無料プランは、しばらく使わないと休止します。
久しぶりに開いた時は、最初の表示に少し時間がかかることがあります。

無料枠では保存データや録音ファイルの扱いに注意が必要です。
商品版として長く使う場合は、有料プラン、永続ディスク、または外部DBを検討してください。

## iPhoneの音声について

音声入力や録音はHTTPSのURLで開く方が動きやすくなります。
Renderの公開URLはHTTPSなので、ローカルの `http://127.0.0.1:5000` よりiPhone向きです。

ただし、iPhoneの機種やSafari設定によっては、直接録音が使えない場合があります。
その場合でも、文字入力、録音ファイル選択、ボイスメモで録音したファイルの利用はできます。

## 今回追加した公開用ファイル

- `requirements-web.txt`
- `Procfile`
- `render.yaml`
- `.gitignore`

通常のローカル起動は今まで通りです。

```powershell
python app.py
```
