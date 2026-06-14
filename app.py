from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import calendar
import json
import os
import re
import shutil
import sqlite3
from urllib.parse import quote, urlencode
from urllib.request import urlopen
import uuid
from pathlib import Path

from flask import Flask, Response, g, jsonify, redirect, render_template, request, send_from_directory, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "secretary.db"
SETTINGS_PATH = BASE_DIR / "settings.json"
GOOGLE_CLIENT_SECRET_PATH = BASE_DIR / "google_client_secret.json"
GOOGLE_TOKEN_PATH = BASE_DIR / "google_calendar_token.json"
UPLOAD_AUDIO_DIR = BASE_DIR / "uploads" / "audio"
RUNTIME_BIN_DIR = BASE_DIR / "_runtime" / "bin"
WHISPER_MODEL_NAME = "tiny"
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
COMPANY_KEYWORDS = (
    "株式会社",
    "有限会社",
    "合同会社",
    "合名会社",
    "合資会社",
    "会社",
    "Inc",
    "INC",
    "Corp",
    "Corporation",
    "Co.",
    "Ltd",
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-\s]?)?(?:0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|\d{2,4}[-\s]\d{2,4}[-\s]\d{3,4})"
)
NUMBER_TRANSLATION = str.maketrans("０１２３４５６７８９，．", "0123456789,.")
WEATHER_CODE_LABELS = {
    0: "快晴",
    1: "晴れ",
    2: "一部くもり",
    3: "くもり",
    45: "霧",
    48: "霧氷",
    51: "弱い霧雨",
    53: "霧雨",
    55: "強い霧雨",
    61: "弱い雨",
    63: "雨",
    65: "強い雨",
    71: "弱い雪",
    73: "雪",
    75: "強い雪",
    80: "弱いにわか雨",
    81: "にわか雨",
    82: "強いにわか雨",
    95: "雷雨",
    96: "雷雨・ひょう",
    99: "強い雷雨・ひょう",
}
JAPAN_CITY_LOCATIONS = {
    "岡山": {"name": "岡山市", "admin1": "岡山県", "country": "日本", "latitude": 34.6551, "longitude": 133.9195},
    "岡山市": {"name": "岡山市", "admin1": "岡山県", "country": "日本", "latitude": 34.6551, "longitude": 133.9195},
    "東京": {"name": "東京", "admin1": "東京都", "country": "日本", "latitude": 35.6762, "longitude": 139.6503},
    "東京都": {"name": "東京", "admin1": "東京都", "country": "日本", "latitude": 35.6762, "longitude": 139.6503},
    "福岡": {"name": "福岡市", "admin1": "福岡県", "country": "日本", "latitude": 33.5902, "longitude": 130.4017},
    "福岡市": {"name": "福岡市", "admin1": "福岡県", "country": "日本", "latitude": 33.5902, "longitude": 130.4017},
}
TRAVEL_CITY_ALIASES = {
    "岡山": "岡山",
    "岡山市": "岡山",
    "大阪": "大阪",
    "大阪市": "大阪",
    "名古屋": "名古屋",
    "名古屋市": "名古屋",
    "東京": "東京",
    "東京都": "東京",
    "福岡": "福岡",
    "福岡市": "福岡",
    "鹿児島": "鹿児島",
    "鹿児島市": "鹿児島",
}
TRAVEL_DISTANCE_KM = {
    frozenset(("岡山", "大阪")): 180,
    frozenset(("岡山", "名古屋")): 365,
    frozenset(("岡山", "東京")): 675,
    frozenset(("岡山", "福岡")): 280,
    frozenset(("岡山", "鹿児島")): 560,
    frozenset(("大阪", "名古屋")): 190,
    frozenset(("大阪", "東京")): 515,
    frozenset(("大阪", "福岡")): 610,
    frozenset(("大阪", "鹿児島")): 890,
    frozenset(("名古屋", "東京")): 350,
    frozenset(("名古屋", "福岡")): 790,
    frozenset(("名古屋", "鹿児島")): 1070,
    frozenset(("東京", "福岡")): 1070,
    frozenset(("東京", "鹿児島")): 1350,
    frozenset(("福岡", "鹿児島")): 290,
}
ROKUYO_LABELS = ["先勝", "友引", "先負", "仏滅", "大安", "赤口"]
ROKUYO_BASE_DATE = date(2026, 6, 13)
ROKUYO_OVERRIDES = {
    "2026-06-12": "赤口",
    "2026-06-13": "先勝",
    "2026-06-21": "大安",
    "2026-06-24": "友引",
    "2026-06-25": "先負",
}
LUCKY_DAY_TABLE = {
    "2026-06-12": ["一粒万倍日", "巳の日"],
    "2026-06-13": ["一粒万倍日"],
    "2026-06-21": ["寅の日"],
    "2026-06-24": ["一粒万倍日", "巳の日"],
    "2026-06-25": ["一粒万倍日"],
    "2026-07-06": ["一粒万倍日", "巳の日"],
    "2026-07-07": ["一粒万倍日"],
    "2026-07-19": ["天赦日", "一粒万倍日"],
    "2026-07-22": ["一粒万倍日"],
    "2026-07-31": ["一粒万倍日"],
    "2026-10-01": ["天赦日", "一粒万倍日"],
    "2026-12-16": ["天赦日", "一粒万倍日"],
}
FORTUNE_DESCRIPTIONS = {
    "大安": "物事を進めやすい吉日です。大切な用事に向いています。",
    "友引": "人との約束や連絡を意識するとよい日です。",
    "先勝": "午前中の行動が向きやすい日です。早めの着手がおすすめです。",
    "先負": "急がず落ち着いて進めるのに向いた日です。",
    "赤口": "大きな決断は慎重に。確認を丁寧にすると安心です。",
    "仏滅": "整理や見直しに向いた日です。無理な新規開始は控えめに。",
    "一粒万倍日": "新しいことを始めるのに良い日です。小さな一歩が育ちやすい日です。",
    "天赦日": "最上級の吉日とされます。新しい挑戦や大切な開始に向いています。",
    "寅の日": "金運や出発に良い日とされます。お金の見直しにも向いています。",
    "巳の日": "金運に縁がある日とされます。収支確認や財布の整理に向いています。",
}

app = Flask(__name__)
app.secret_key = os.environ.get("AI_SECRETARY_SECRET_KEY", "ai-secretary-local-dev-key")
whisper_model = None


PUBLIC_ENDPOINTS = {
    "static",
    "license_status",
    "verify_license",
    "apple_touch_icon",
    "admin_login",
}


AUDIO_EXTENSION_BY_MIME = {
    "audio/webm": ".webm",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
}


DEFAULT_SETTINGS = {
    "license_key": os.environ.get("AI_SECRETARY_LICENSE_KEY", ""),
    "brand": {
        "name": "AI秘書",
        "logo_path": "logo.png",
    },
    "design_theme": "dark-secretary",
    "current_character": "none",
    "characters": [
        {"id": "none", "name": "秘書なし", "image_path": ""},
        {"id": "female", "name": "女性秘書", "image_path": "characters/female.png"},
        {"id": "male", "name": "男性秘書", "image_path": "characters/male.png"},
    ],
}

DESIGN_THEMES = [
    {
        "id": "dark-secretary",
        "name": "ダーク秘書",
        "description": "黒と金を基調にした標準テーマ",
    },
    {
        "id": "gold",
        "name": "ゴールド",
        "description": "華やかで特別感のあるテーマ",
    },
    {
        "id": "cool-blue",
        "name": "クールブルー",
        "description": "知的で落ち着いた印象のテーマ",
    },
    {
        "id": "healing-green",
        "name": "癒しグリーン",
        "description": "やさしく穏やかな印象のテーマ",
    },
]


def load_settings():
    if not SETTINGS_PATH.exists():
        return json.loads(json.dumps(DEFAULT_SETTINGS, ensure_ascii=False))

    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as file:
            settings = json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SETTINGS

    merged_settings = {
        **DEFAULT_SETTINGS,
        **settings,
        "brand": {
            **DEFAULT_SETTINGS["brand"],
            **settings.get("brand", {}),
        },
        "characters": settings.get("characters") or DEFAULT_SETTINGS["characters"],
    }
    if merged_settings.get("design_theme") not in {theme["id"] for theme in DESIGN_THEMES}:
        merged_settings["design_theme"] = DEFAULT_SETTINGS["design_theme"]
    env_license_key = os.environ.get("AI_SECRETARY_LICENSE_KEY", "").strip()
    if env_license_key:
        merged_settings["license_key"] = env_license_key
    return merged_settings


def save_settings(settings):
    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)


def get_current_character(settings):
    current_id = settings.get("current_character", "none")
    for character in settings.get("characters", []):
        if character.get("id") == current_id:
            return character
    return DEFAULT_SETTINGS["characters"][0]


def is_license_approved():
    return session.get("license_approved") is True


def is_admin_approved():
    return session.get("admin_approved") is True


def get_admin_key():
    return os.environ.get("AI_SECRETARY_ADMIN_KEY", "").strip()


def normalize_date_text(value):
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return ""


def is_license_key_expired(expires_on):
    expires_on = str(expires_on or "").strip()
    if not expires_on:
        return False
    try:
        return date.fromisoformat(expires_on) < date.today()
    except ValueError:
        return True


def find_managed_license_key(input_key):
    init_db()
    row = get_db().execute(
        """
        SELECT *
        FROM secretary_license_keys
        WHERE license_key = ?
        """,
        (input_key,),
    ).fetchone()
    if not row:
        return None
    if int(row["is_active"]) != 1:
        return None
    if is_license_key_expired(row["expires_on"]):
        return None
    return row


def mark_license_key_used(license_id):
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
    db = get_db()
    db.execute(
        """
        UPDATE secretary_license_keys
        SET use_count = use_count + 1,
            last_used_at = ?
        WHERE id = ?
        """,
        (now_text, license_id),
    )
    db.commit()


def license_key_is_valid(input_key):
    input_key = str(input_key or "").strip()
    if not input_key:
        return False

    main_license_key = str(load_settings().get("license_key", "")).strip()
    if main_license_key and input_key == main_license_key:
        return True

    managed_license = find_managed_license_key(input_key)
    if managed_license:
        mark_license_key_used(managed_license["id"])
        return True

    return False


@app.before_request
def require_license():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if request.endpoint and request.endpoint.startswith("admin_"):
        if is_admin_approved():
            return None
        return redirect(url_for("admin_login"))

    if is_license_approved():
        return None

    if request.method != "GET":
        return jsonify({"ok": False, "message": "利用キーの確認が必要です。"}), 401

    return render_template("license_only.html", settings=load_settings()), 401


def get_google_oauth_flow(state=None):
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as error:
        raise RuntimeError(
            "外部予定表連携の準備が未完了です。必要な場合だけ、導入手順に沿って準備してください。"
        ) from error

    if not GOOGLE_CLIENT_SECRET_PATH.exists():
        raise FileNotFoundError(
            "外部予定表連携用の設定ファイルが見つかりません。必要な場合だけ、設定ファイルを正本フォルダへ配置してください。"
        )

    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRET_PATH),
        scopes=GOOGLE_CALENDAR_SCOPES,
        state=state,
    )
    flow.redirect_uri = url_for("google_calendar_callback", _external=True)
    return flow


def get_google_calendar_status():
    client_secret_exists = GOOGLE_CLIENT_SECRET_PATH.exists()
    token_exists = GOOGLE_TOKEN_PATH.exists()
    libraries_ready = True
    library_message = ""
    try:
        import google_auth_oauthlib.flow  # noqa: F401
        import google.oauth2.credentials  # noqa: F401
    except ImportError:
        libraries_ready = False
        library_message = "外部予定表連携の準備が未完了です。"

    return {
        "connected": token_exists,
        "label": "接続済み" if token_exists else "未連携",
        "client_secret_exists": client_secret_exists,
        "libraries_ready": libraries_ready,
        "library_message": library_message,
        "token_file": GOOGLE_TOKEN_PATH.name,
        "client_secret_file": GOOGLE_CLIENT_SECRET_PATH.name,
    }


def get_google_calendar_service():
    if not GOOGLE_TOKEN_PATH.exists():
        raise RuntimeError("外部予定表は未連携です。先に連携設定を完了してください。")

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as error:
        raise RuntimeError(
            "外部予定表連携の準備が未完了です。必要な場合だけ、導入手順に沿って準備してください。"
        ) from error

    credentials = Credentials.from_authorized_user_file(
        str(GOOGLE_TOKEN_PATH),
        GOOGLE_CALENDAR_SCOPES,
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        GOOGLE_TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials.valid:
        raise RuntimeError("外部予定表の認証が無効です。もう一度連携してください。")

    return build("calendar", "v3", credentials=credentials)


def build_google_calendar_event(schedule):
    scheduled_at = str(schedule["scheduled_at"] or "").strip()
    scheduled_datetime = parse_schedule_datetime(scheduled_at)
    if scheduled_datetime is None:
        raise ValueError("予定日時を外部予定表用に変換できませんでした。")

    is_date_only = re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", scheduled_at) is not None
    event = {
        "summary": str(schedule["title"] or "AI秘書の予定"),
        "description": "AI秘書から登録",
        "extendedProperties": {
            "private": {
                "ai_secretary_schedule_id": str(schedule["id"]),
            }
        },
    }
    if is_date_only:
        event["start"] = {"date": scheduled_datetime.date().isoformat()}
        event["end"] = {"date": (scheduled_datetime.date() + timedelta(days=1)).isoformat()}
    else:
        event["start"] = {
            "dateTime": scheduled_datetime.isoformat(),
            "timeZone": "Asia/Tokyo",
        }
        event["end"] = {
            "dateTime": (scheduled_datetime + timedelta(hours=1)).isoformat(),
            "timeZone": "Asia/Tokyo",
        }
    return event


def register_schedule_to_google_calendar(schedule):
    service = get_google_calendar_service()
    private_property = f"ai_secretary_schedule_id={schedule['id']}"
    existing = (
        service.events()
        .list(
            calendarId="primary",
            privateExtendedProperty=private_property,
            maxResults=1,
        )
        .execute()
    )
    if existing.get("items"):
        return {
            "ok": True,
            "message": "この予定はすでに外部予定表へ登録済みです。",
        }

    event = build_google_calendar_event(schedule)
    created = service.events().insert(calendarId="primary", body=event).execute()
    return {
        "ok": True,
        "message": "外部予定表へ登録しました。",
        "event_id": created.get("id", ""),
        "html_link": created.get("htmlLink", ""),
    }


def format_google_calendar_datetime(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if "T" not in text:
        return f"{text} 終日"

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text

    return parsed.strftime("%Y-%m-%d %H:%M")


def fetch_google_calendar_events(max_results=5):
    service = get_google_calendar_service()
    now_text = datetime.now().astimezone().isoformat()
    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now_text,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = []
    for event in result.get("items", []):
        start = event.get("start", {})
        start_value = start.get("dateTime") or start.get("date") or ""
        events.append(
            {
                "id": event.get("id", ""),
                "title": event.get("summary") or "無題の予定",
                "start": format_google_calendar_datetime(start_value),
                "link": event.get("htmlLink", ""),
            }
        )
    return events


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secretary_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                deadline TEXT NOT NULL,
                status TEXT NOT NULL,
                source_text TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secretary_tasks_list
            ON secretary_tasks(status, priority, deadline, created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secretary_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secretary_schedule_list
            ON secretary_schedule(scheduled_at, created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secretary_transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secretary_transcripts_list
            ON secretary_transcripts(created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secretary_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secretary_contacts_list
            ON secretary_contacts(created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secretary_money (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                memo TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secretary_money_list
            ON secretary_money(created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secretary_license_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT NOT NULL UNIQUE,
                memo TEXT NOT NULL DEFAULT '',
                expires_on TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                use_count INTEGER NOT NULL DEFAULT 0,
                last_used_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                disabled_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_secretary_license_keys_status
            ON secretary_license_keys(is_active, expires_on, created_at)
            """
        )


def next_weekday(base_date, weekday):
    days = (weekday - base_date.weekday()) % 7
    if days == 0:
        days = 7
    return base_date + timedelta(days=days)


def parse_deadline(text):
    today = date.today()
    if "今日" in text or "本日" in text:
        return today.isoformat()
    if "明日" in text:
        return (today + timedelta(days=1)).isoformat()
    if "明後日" in text:
        return (today + timedelta(days=2)).isoformat()
    if "来週" in text:
        return next_weekday(today, 4).isoformat()
    if "月末" in text:
        next_month = today.replace(day=28) + timedelta(days=4)
        return (next_month - timedelta(days=next_month.day)).isoformat()

    match = re.search(r"(\d{1,2})[/-](\d{1,2})", text)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = today.year
        try:
            parsed = date(year, month, day)
            if parsed < today:
                parsed = date(year + 1, month, day)
            return parsed.isoformat()
        except ValueError:
            return ""

    return ""


def classify_priority(text, deadline):
    urgent_words = ("今日", "本日", "至急", "急ぎ", "すぐ", "必ず")
    important_words = ("必要", "提案", "連絡", "修正", "確認", "提出", "支払い", "契約")
    if any(word in text for word in urgent_words):
        return "A"
    if deadline:
        return "B"
    if any(word in text for word in important_words):
        return "B"
    return "C"


def clean_title(text):
    title = text.strip()
    title = title.replace("作らないとな", "作成")
    title = title.replace("作らなきゃ", "作成")
    remove_words = (
        "今日中に",
        "今日",
        "本日",
        "明日までに",
        "明日",
        "来週までに",
        "来週",
        "月末までに",
        "月末",
        "しないとな",
        "しなきゃ",
        "したい",
        "必要",
    )
    for word in remove_words:
        title = title.replace(word, "")
    title = re.sub(r"\s+", " ", title).strip(" 。、,.")
    return title or text.strip()


def split_task_candidates(source_text):
    chunks = re.split(r"[。.!！?\n]+", source_text)
    tasks = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = re.split(r"[、,]|(?:\s+と\s+)|(?:\s+も\s+)", chunk)
        tasks.extend(part.strip() for part in parts if part.strip())
    return tasks


def split_conversation_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(r"[。！？!?\n]+", text)
        if sentence.strip()
    ]


def clean_conversation_candidate(text):
    cleaned = re.sub(r"^(えっと|あの|その|あと|それと|じゃあ|まず|次に)[、\s]*", "", text)
    cleaned = re.sub(r"(しないと|しなきゃ|する|やる|までに)$", "", cleaned)
    for word in ("今日中に", "今日までに", "明日までに", "来週までに", "月末までに"):
        cleaned = cleaned.replace(word, "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" 、。")


def unique_items(items):
    unique = []
    seen = set()
    for item in items:
        if item and item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def normalize_number_text(text):
    return str(text or "").translate(NUMBER_TRANSLATION).replace(",", "")


def parse_calculator_number(raw_value, unit=""):
    value_text = normalize_number_text(raw_value)
    try:
        value = Decimal(value_text)
    except InvalidOperation as error:
        raise ValueError("数字を読み取れませんでした。") from error

    clean_unit = str(unit or "").strip()
    if clean_unit in ("万円", "万"):
        return value * Decimal("10000")
    return value


def format_calculator_result(value, source_text):
    rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        integer_value = int(rounded)
        if ("万" in source_text) and integer_value % 10000 == 0:
            return f"{integer_value // 10000:,}万円"
        return f"{integer_value:,}円"

    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}円"


def calculate_voice_expression(text):
    source_text = normalize_number_text(text)
    compact_text = re.sub(r"\s+", "", source_text)
    amount_pattern = r"([0-9]+(?:\.[0-9]+)?)(万円|万|円)?"

    percent_match = re.search(
        rf"{amount_pattern}の([0-9]+(?:\.[0-9]+)?)%",
        compact_text,
    )
    if percent_match:
        base = parse_calculator_number(percent_match.group(1), percent_match.group(2))
        percent = parse_calculator_number(percent_match.group(3))
        return base * percent / Decimal("100")

    subtract_match = re.search(
        rf"{amount_pattern}から{amount_pattern}(?:引く|ひく|マイナス|-)",
        compact_text,
    )
    if subtract_match:
        left = parse_calculator_number(subtract_match.group(1), subtract_match.group(2))
        right = parse_calculator_number(subtract_match.group(3), subtract_match.group(4))
        return left - right

    add_match = re.search(
        rf"{amount_pattern}(?:に|と|\+|プラス|足す|たす){amount_pattern}(?:足す|たす)?",
        compact_text,
    )
    if add_match:
        left = parse_calculator_number(add_match.group(1), add_match.group(2))
        right = parse_calculator_number(add_match.group(3), add_match.group(4))
        return left + right

    multiply_count_match = re.search(
        rf"{amount_pattern}を([0-9]+(?:\.[0-9]+)?)(?:個|つ|倍)?",
        compact_text,
    )
    if multiply_count_match:
        left = parse_calculator_number(multiply_count_match.group(1), multiply_count_match.group(2))
        right = parse_calculator_number(multiply_count_match.group(3))
        return left * right

    multiply_match = re.search(
        rf"{amount_pattern}(?:かける|掛ける|×|x|X|\*){amount_pattern}",
        compact_text,
    )
    if multiply_match:
        left = parse_calculator_number(multiply_match.group(1), multiply_match.group(2))
        right = parse_calculator_number(multiply_match.group(3), multiply_match.group(4))
        return left * right

    divide_match = re.search(
        rf"{amount_pattern}(?:割る|わる|÷|/){amount_pattern}",
        compact_text,
    )
    if divide_match:
        left = parse_calculator_number(divide_match.group(1), divide_match.group(2))
        right = parse_calculator_number(divide_match.group(3), divide_match.group(4))
        if right == 0:
            raise ValueError("0では割れません。")
        return left / right

    raise ValueError("計算式を読み取れませんでした。")


def fetch_json_url(url, timeout=10):
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_weather_location(query):
    location = str(query or "").strip()
    if not location:
        raise ValueError("地域名を入力してください。")

    if location in JAPAN_CITY_LOCATIONS:
        return JAPAN_CITY_LOCATIONS[location]

    params = urlencode(
        {
            "name": location,
            "count": 5,
            "language": "ja",
            "format": "json",
            "countryCode": "JP",
        }
    )
    data = fetch_json_url(f"https://geocoding-api.open-meteo.com/v1/search?{params}")
    results = data.get("results") or []
    if not results:
        raise ValueError("地域が見つかりませんでした。")

    result = next(
        (
            item
            for item in results
            if location in str(item.get("name", "")) or location in str(item.get("admin1", ""))
        ),
        results[0],
    )
    return {
        "name": result.get("name") or location,
        "admin1": result.get("admin1") or "",
        "country": result.get("country") or "",
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }


def get_weather_label(code):
    return WEATHER_CODE_LABELS.get(int(code), "不明")


def fetch_weather_report(query):
    location = resolve_weather_location(query)
    params = urlencode(
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "timezone": "Asia/Tokyo",
            "forecast_days": 2,
        }
    )
    data = fetch_json_url(f"https://api.open-meteo.com/v1/forecast?{params}")
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []

    if len(times) < 1:
        raise ValueError("天気情報を取得できませんでした。")

    def build_day(index):
        return {
            "date": times[index],
            "weather": get_weather_label(codes[index]),
            "max_temp": max_temps[index],
            "min_temp": min_temps[index],
        }

    location_name = " / ".join(
        item for item in (location["name"], location["admin1"], location["country"]) if item
    )
    return {
        "location": location_name,
        "today": build_day(0),
        "tomorrow": build_day(1) if len(times) > 1 else None,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def resolve_travel_city(value):
    text = str(value or "").strip()
    if not text:
        return ""
    return TRAVEL_CITY_ALIASES.get(text, "")


def format_travel_time(hours):
    total_minutes = int(round(hours * 60 / 5) * 5)
    hour = total_minutes // 60
    minute = total_minutes % 60
    if hour and minute:
        return f"約{hour}時間{minute}分"
    if hour:
        return f"約{hour}時間"
    return f"約{minute}分"


def format_yen(value):
    return f"約{int(round(value / 100) * 100):,}円"


def build_travel_option(label, icon, hours, fee, reason_note=""):
    return {
        "label": label,
        "icon": icon,
        "time": format_travel_time(hours),
        "fee": format_yen(fee),
        "hours": hours,
        "reason_note": reason_note,
    }


def build_travel_support(origin_text, destination_text):
    origin = resolve_travel_city(origin_text)
    destination = resolve_travel_city(destination_text)
    if not origin or not destination:
        supported = "、".join(sorted(set(TRAVEL_CITY_ALIASES.values())))
        raise ValueError(f"対応都市は {supported} です。")
    if origin == destination:
        raise ValueError("出発地と目的地は別の都市を入力してください。")

    distance = TRAVEL_DISTANCE_KM.get(frozenset((origin, destination)))
    if not distance:
        raise ValueError("この都市間はまだ対応していません。")

    shinkansen = build_travel_option(
        "新幹線",
        "🚅",
        distance / 190 + 0.25,
        distance * 22 + 2500,
        "速く、時間が読みやすい移動です。",
    )
    car = build_travel_option(
        "車",
        "🚗",
        distance / 70 + 0.5,
        distance * 35 + 2500,
        "荷物が多い時や寄り道したい時に便利です。",
    )
    bus = build_travel_option(
        "高速バス",
        "🚌",
        distance / 75 + 1.0,
        distance * 8 + 1500,
        "料金を抑えたい時に向いています。",
    )
    plane = build_travel_option(
        "飛行機",
        "✈️",
        max(2.3, distance / 650 + 1.8),
        distance * 6 + 13000,
        "長距離では速い候補です。空港移動時間も見込みます。",
    )

    if distance >= 850:
        recommendation = plane
        reason = "長距離のため、飛行機が最も速く移動しやすい候補です。"
    else:
        recommendation = shinkansen
        reason = "最も速く、駅から駅まで移動しやすい候補です。"

    return {
        "origin": origin,
        "destination": destination,
        "distance": f"約{distance}km",
        "options": [shinkansen, car, bus, plane],
        "recommendation": {
            "label": recommendation["label"],
            "reason": reason,
        },
    }


def get_rokuyo(target_date):
    date_key = target_date.isoformat()
    if date_key in ROKUYO_OVERRIDES:
        return ROKUYO_OVERRIDES[date_key]

    days = (target_date - ROKUYO_BASE_DATE).days
    return ROKUYO_LABELS[days % len(ROKUYO_LABELS)]


def build_fortune_day(target_date):
    date_key = target_date.isoformat()
    rokuyo = get_rokuyo(target_date)
    lucky_days = LUCKY_DAY_TABLE.get(date_key, [])
    description_source = lucky_days[0] if lucky_days else rokuyo
    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "month_day": f"{target_date.month}/{target_date.day}",
        "rokuyo": rokuyo,
        "lucky_days": lucky_days,
        "description": FORTUNE_DESCRIPTIONS.get(description_source, "落ち着いて一日を整えましょう。"),
    }


def build_month_fortune(target_date):
    first_day = target_date.replace(day=1)
    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)
    days_count = (next_month - first_day).days
    month_days = []
    for offset in range(days_count):
        current = first_day + timedelta(days=offset)
        fortune = build_fortune_day(current)
        if fortune["lucky_days"] or fortune["rokuyo"] == "大安":
            month_days.append(fortune)
    return month_days


def build_fortune_calendar():
    today = date.today()
    return {
        "today": build_fortune_day(today),
        "month_days": build_month_fortune(today),
    }


def generate_document_text(kind, recipient, content):
    clean_kind = str(kind or "").strip()
    clean_recipient = str(recipient or "").strip()
    clean_content = str(content or "").strip()
    name_line = clean_recipient or "ご担当者様"
    body = clean_content or "詳細についてご確認をお願いいたします。"

    templates = {
        "お礼": (
            f"{name_line}\n\n"
            f"{body}\n\n"
            "本日はお忙しい中お時間をいただき、誠にありがとうございました。\n"
            "今後ともよろしくお願いいたします。"
        ),
        "謝罪": (
            f"{name_line}\n\n"
            f"{body}\n\n"
            "このたびはご迷惑をおかけし、誠に申し訳ございません。\n"
            "今後同じことがないよう、確認を徹底してまいります。"
        ),
        "営業": (
            f"{name_line}\n\n"
            "いつもお世話になっております。\n\n"
            f"{body}\n\n"
            "貴社のお役に立てる内容かと存じますので、ぜひ一度ご確認いただけますと幸いです。"
        ),
        "アポ依頼": (
            f"{name_line}\n\n"
            "いつもお世話になっております。\n\n"
            f"{body}\n\n"
            "ご都合のよい日時をいくつか頂戴できますでしょうか。\n"
            "何卒よろしくお願いいたします。"
        ),
        "面談後フォロー": (
            f"{name_line}\n\n"
            "本日はお時間をいただき、誠にありがとうございました。\n\n"
            f"{body}\n\n"
            "本日お話しした内容を踏まえ、引き続き進めてまいります。\n"
            "今後ともよろしくお願いいたします。"
        ),
        "自由入力": (
            f"{name_line}\n\n"
            f"{body}\n\n"
            "ご確認のほど、よろしくお願いいたします。"
        ),
    }
    return templates.get(clean_kind, templates["自由入力"])


def find_writer_person(text, contacts):
    for contact in contacts:
        name = str(contact["name"] or "").strip()
        if name and name in text:
            return name if name.endswith(("様", "さん")) else f"{name}様"

    match = re.search(r"([一-龥ぁ-んァ-ヶA-Za-z]{2,12})(さん|様)", text)
    if match:
        suffix = "様" if match.group(2) == "様" else "様"
        return f"{match.group(1)}{suffix}"

    first_contact = next((contact for contact in contacts if str(contact["name"] or "").strip()), None)
    if first_contact:
        name = str(first_contact["name"]).strip()
        return name if name.endswith(("様", "さん")) else f"{name}様"

    return ""


def add_writer_suggestion(suggestions, titles, title, kind, recipient, content):
    if title in titles:
        return
    suggestions.append(
        {
            "title": title,
            "kind": kind,
            "recipient": recipient,
            "content": content,
        }
    )
    titles.add(title)


def build_writer_suggestions(tasks, upcoming_schedules, transcripts, contacts):
    suggestions = []
    titles = set()
    recent_text = " ".join(str(row["content"] or "") for row in list(transcripts)[:3])
    todo_text = " ".join(str(row["title"] or "") for row in list(tasks)[:5])
    schedule_text = " ".join(str(row["title"] or "") for row in list(upcoming_schedules)[:3])
    source_text = " ".join([recent_text, todo_text, schedule_text]).strip()
    recipient = find_writer_person(source_text, contacts)
    meeting_words = ("打合せ", "打ち合わせ", "面談", "会議", "訪問")
    estimate_words = ("見積", "見積書", "提案", "資料")
    contact_words = ("連絡", "確認", "送付", "返信")

    if any(word in source_text for word in meeting_words):
        add_writer_suggestion(
            suggestions,
            titles,
            "打合せ後のお礼文",
            "お礼",
            recipient,
            "本日は打合せのお時間をいただきありがとうございました。",
        )
        add_writer_suggestion(
            suggestions,
            titles,
            "次回面談依頼文",
            "アポ依頼",
            recipient,
            "先日の内容を踏まえ、次回のお打合せ日程をご相談させてください。",
        )

    if any(word in source_text for word in estimate_words):
        add_writer_suggestion(
            suggestions,
            titles,
            "見積提出フォロー文",
            "面談後フォロー",
            recipient,
            "先日の打合せ内容を踏まえ、見積書についてご確認をお願いいたします。",
        )

    if upcoming_schedules:
        schedule = upcoming_schedules[0]
        add_writer_suggestion(
            suggestions,
            titles,
            "予定前の確認文",
            "アポ依頼",
            recipient,
            f"{schedule['title']}の件で、予定日時のご確認をお願いいたします。",
        )

    active_tasks = [task for task in tasks if task["status"] != "完了"]
    due_tasks = [task for task in active_tasks if task["deadline"]]
    due_tasks.sort(key=task_sort_key)
    if due_tasks:
        task = due_tasks[0]
        add_writer_suggestion(
            suggestions,
            titles,
            "やること確認フォロー文",
            "自由入力",
            recipient,
            f"{task['title']}について確認のご連絡です。",
        )

    if any(word in source_text for word in contact_words):
        add_writer_suggestion(
            suggestions,
            titles,
            "連絡確認文",
            "自由入力",
            recipient,
            "先日の件について、念のため確認のご連絡です。",
        )

    if not suggestions:
        add_writer_suggestion(
            suggestions,
            titles,
            "近況確認文",
            "自由入力",
            recipient,
            "先日の件についてご確認をお願いいたします。",
        )

    return suggestions[:5]


def extract_conversation_items(text):
    todo_items = []
    schedule_items = []
    schedule_pattern = re.compile(
        r"((今日|明日|明後日|来週|今週|月曜|火曜|水曜|木曜|金曜|土曜|日曜|[0-9０-９]{1,2}時).*(打ち合わせ|打合せ|会議|面談|訪問|予定)|(打ち合わせ|打合せ|会議|面談|訪問|予定))"
    )
    todo_pattern = re.compile(
        r"(しないと|しなきゃ|する|やる|までに|送る|送付|連絡|確認|作成|提出|支払い|予約|修正)"
    )

    for sentence in split_conversation_sentences(text):
        cleaned = clean_conversation_candidate(sentence)
        if schedule_pattern.search(sentence):
            schedule_items.append(cleaned)
        if todo_pattern.search(sentence):
            todo_items.append(cleaned)

    return {
        "todos": unique_items(todo_items),
        "schedules": unique_items(schedule_items),
    }


def guess_money_candidate(text):
    source_text = str(text or "").strip()
    amount_match = re.search(r"([0-9０-９,]+)\s*円", source_text)
    if not amount_match:
        return None

    amount = normalize_number_text(amount_match.group(1))
    money_type = "収入" if re.search(r"(収入|入金|給料|売上|振込|もらった)", source_text) else "支出"
    memo = source_text
    memo = re.sub(r"([0-9０-９,]+)\s*円", "", memo)
    memo = re.sub(r"(今日|本日|昨日|明日|の|は|を|で|に)", " ", memo)
    memo = re.sub(r"\s+", " ", memo).strip(" 、。")
    return {
        "type": money_type,
        "amount": amount,
        "memo": memo or source_text,
    }


def split_secretary_request_units(text):
    source_text = str(text or "").strip()
    if not source_text:
        return []

    normalized = re.sub(r"(それと|あと|加えて|ついでに)", "。", source_text)
    units = []
    for sentence in split_conversation_sentences(normalized):
        split_parts = re.split(
            r"[、,](?=.*(?:[0-9０-９,]+\s*円|名刺|連絡先|メモ|忘れ|予定|会議|会う|収入|入金|支出))",
            sentence,
        )
        for part in split_parts:
            clean_part = str(part or "").strip()
            if clean_part:
                units.append(clean_part)

    return unique_items(units or [source_text])


def is_schedule_request(text):
    source_text = str(text or "").strip()
    time_hint = re.search(
        r"(今日|明日|明後日|来週|今週|月曜|火曜|水曜|木曜|金曜|土曜|日曜|[0-9０-９]{1,2}時|[0-9０-９]{1,2}:[0-9０-９]{2})",
        source_text,
    )
    schedule_words = re.search(
        r"(予定|歯医者|病院|訪問|打ち合わせ|打合せ|会議|面談|予約|アポ|会う|行く|来る|ランチ|食事|商談)",
        source_text,
    )
    return bool(schedule_words and (time_hint or re.search(r"(予定|予約|アポ|会議|打ち合わせ|打合せ|訪問|面談)", source_text)))


def is_contact_request(text):
    source_text = str(text or "").strip()
    return bool(
        re.search(r"(名刺|連絡先|電話番号|電話|メール|メールアドレス|会社|取引先|担当者|登録)", source_text)
        or EMAIL_PATTERN.search(source_text)
        or PHONE_PATTERN.search(source_text)
    )


def is_conversation_log_request(text):
    source_text = str(text or "").strip()
    return bool(re.search(r"(会話|話|打ち合わせ内容|議事録|ログ|文字起こし|録音|保存|記録)", source_text))


def is_memo_request(text):
    source_text = str(text or "").strip()
    return bool(re.search(r"(メモ|覚えて|控えて|残して|記録して|保存して|忘れないように)", source_text))


def append_unique_candidate(candidates, candidate):
    key = (candidate["kind"], candidate["title"], candidate["url"])
    if any((item["kind"], item["title"], item["url"]) == key for item in candidates):
        return
    candidates.append(candidate)


def build_secretary_route_candidates(text):
    source_text = str(text or "").strip()
    candidates = []
    if not source_text:
        return candidates

    request_units = split_secretary_request_units(source_text)
    conversation_items = extract_conversation_items(source_text)
    todo_items = list(conversation_items["todos"])

    for unit in request_units:
        cleaned_unit = clean_conversation_candidate(unit)
        if not cleaned_unit:
            continue

        if is_schedule_request(unit) or unit in conversation_items["schedules"]:
            schedule_item = parse_schedule_item(unit)
            append_unique_candidate(
                candidates,
                {
                    "kind": "予定候補",
                    "title": schedule_item["title"],
                    "detail": f"{schedule_item['scheduled_at']} の予定として整理できます。",
                    "action_label": "予定追加へ",
                    "url": url_for("feature_page", feature_key="schedule-add"),
                },
            )

        money_candidate = guess_money_candidate(unit)
        if money_candidate:
            feature_key = "income" if money_candidate["type"] == "収入" else "expense"
            append_unique_candidate(
                candidates,
                {
                    "kind": f"{money_candidate['type']}候補",
                    "title": f"{money_candidate['memo']} {money_candidate['amount']}円",
                    "detail": "お金の記録画面で確認して保存できます。",
                    "action_label": f"{money_candidate['type']}登録へ",
                    "url": url_for("feature_page", feature_key=feature_key),
                },
            )

        if is_contact_request(unit):
            action_label = "連絡先確認へ" if re.search(r"(確認|探し|一覧|見る)", unit) else "名刺登録へ"
            anchor = "contactListSection" if action_label == "連絡先確認へ" else "businessCardSection"
            append_unique_candidate(
                candidates,
                {
                    "kind": "名刺・連絡先候補",
                    "title": cleaned_unit,
                    "detail": "名刺撮影、読み取り、手入力で連絡先候補を作れます。",
                    "action_label": action_label,
                    "url": f"{url_for('feature_page', feature_key='conversation')}#{anchor}",
                },
            )

        if is_conversation_log_request(unit) and not is_contact_request(unit):
            append_unique_candidate(
                candidates,
                {
                    "kind": "会話保存候補",
                    "title": cleaned_unit,
                    "detail": "会話整理画面で保存、要約、やること抽出ができます。",
                    "action_label": "会話整理へ",
                    "url": url_for("feature_page", feature_key="conversation"),
                },
            )

        if is_memo_request(unit):
            append_unique_candidate(
                candidates,
                {
                    "kind": "メモ保存候補",
                    "title": cleaned_unit,
                    "detail": "メモ入力から、やることや予定として整理できます。",
                    "action_label": "メモ保存へ",
                    "url": url_for("feature_page", feature_key="schedule-add"),
                },
            )

        if re.search(r"(忘れない|忘れん|買い物|買う|用意|準備|持っていく|やること|タスク|TODO|ToDo)", unit):
            todo_items.append(cleaned_unit)

    for todo in unique_items(todo_items)[:3]:
        append_unique_candidate(
            candidates,
            {
                "kind": "やること候補",
                "title": todo,
                "detail": "メモ整理画面でタスクとして保存できます。",
                "action_label": "やること追加へ",
                "url": url_for("feature_page", feature_key="schedule-add"),
            },
        )

    if not candidates:
        append_unique_candidate(
            candidates,
            {
                "kind": "相談候補",
                "title": source_text,
                "detail": "まずは秘書に相談として扱えます。必要なら予定、タスク、お金へ整理します。",
                "action_label": "秘書に相談",
                "url": url_for("feature_page", feature_key="conversation"),
            }
        )

    return candidates[:8]


def extract_tasks(source_text):
    tasks = []
    seen = set()
    for candidate in split_task_candidates(source_text):
        title = clean_title(candidate)
        if not title or title in seen:
            continue
        deadline = parse_deadline(candidate)
        priority = classify_priority(candidate, deadline)
        tasks.append(
            {
                "title": title,
                "priority": priority,
                "deadline": deadline,
                "status": "未着手",
                "source_text": source_text,
            }
        )
        seen.add(title)
    return tasks


def save_tasks(tasks):
    db = get_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for task in tasks:
        db.execute(
            """
            INSERT INTO secretary_tasks (
                created_at,
                title,
                priority,
                deadline,
                status,
                source_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                task["title"],
                task["priority"],
                task["deadline"],
                task["status"],
                task["source_text"],
            ),
        )
    db.commit()


def build_conversation_tasks(todo_items, source_text):
    tasks = []
    source_sentences = split_conversation_sentences(source_text)
    for item in todo_items:
        title = str(item or "").strip()
        if not title:
            continue
        source_sentence = next(
            (
                sentence
                for sentence in source_sentences
                if clean_conversation_candidate(sentence) == title or title in sentence
            ),
            "",
        )
        tasks.append(
            {
                "title": title,
                "priority": "B",
                "deadline": parse_deadline(source_sentence) or parse_deadline(title),
                "status": "未着手",
                "source_text": source_text,
            }
        )
    return tasks


def parse_schedule_item(item):
    text = str(item or "").strip()
    datetime_pattern = re.compile(
        r"((今日|明日|明後日|来週|今週)?(月曜|火曜|水曜|木曜|金曜|土曜|日曜)?[0-9０-９]{1,2}時([0-9０-９]{1,2}分)?|(今日|明日|明後日|来週|今週|月曜|火曜|水曜|木曜|金曜|土曜|日曜))"
    )
    matches = [match.group(0) for match in datetime_pattern.finditer(text) if match.group(0)]
    schedule_time = " ".join(dict.fromkeys(matches))
    title = text
    for match in matches:
        title = title.replace(match, "")
    title = re.sub(r"^[にの、\s]+|[にの、\s]+$", "", title)
    title = title or text
    return {
        "title": title,
        "scheduled_at": normalize_schedule_time(schedule_time),
    }


def normalize_schedule_time(schedule_time):
    text = str(schedule_time or "").strip()
    if not text:
        return "未設定"

    today = date.today()
    target_date = None
    weekday_map = {
        "月曜": 0,
        "火曜": 1,
        "水曜": 2,
        "木曜": 3,
        "金曜": 4,
        "土曜": 5,
        "日曜": 6,
    }
    if "今日" in text:
        target_date = today
    elif "明日" in text:
        target_date = today + timedelta(days=1)
    elif "明後日" in text:
        target_date = today + timedelta(days=2)
    else:
        for label, weekday in weekday_map.items():
            if label in text:
                target_date = next_weekday(today, weekday)
                break

    time_match = re.search(r"([0-9０-９]{1,2})時([0-9０-９]{1,2}分)?", text)
    if time_match:
        hour = int(time_match.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789")))
        minute_text = time_match.group(2)
        minute = 0
        if minute_text:
            minute = int(minute_text.replace("分", "").translate(str.maketrans("０１２３４５６７８９", "0123456789")))
        time_text = f"{hour:02d}:{minute:02d}"
    else:
        time_text = ""

    if target_date and time_text:
        return f"{target_date.isoformat()} {time_text}"
    if target_date:
        return target_date.isoformat()
    if time_text:
        return time_text
    return text


def fetch_tasks():
    return get_db().execute(
        """
        SELECT id, created_at, title, priority, deadline, status, source_text
        FROM secretary_tasks
        ORDER BY
            CASE priority
                WHEN 'A' THEN 1
                WHEN 'B' THEN 2
                ELSE 3
            END,
            CASE WHEN deadline = '' THEN 1 ELSE 0 END,
            deadline,
            id DESC
        """
    ).fetchall()


def fetch_schedules():
    return get_db().execute(
        """
        SELECT id, title, scheduled_at, created_at
        FROM secretary_schedule
        ORDER BY
            CASE WHEN scheduled_at = '未設定' THEN 1 ELSE 0 END,
            scheduled_at,
            id DESC
        """
    ).fetchall()


def fetch_schedule(schedule_id):
    return get_db().execute(
        """
        SELECT id, title, scheduled_at, created_at
        FROM secretary_schedule
        WHERE id = ?
        """,
        (schedule_id,),
    ).fetchone()


def parse_schedule_datetime(value, now=None):
    text = str(value or "").strip()
    if not text or text == "未設定":
        return None

    base_now = now or datetime.now()
    for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            parsed_date = datetime.strptime(text, fmt).date()
            return datetime.combine(parsed_date, datetime.min.time())
        except ValueError:
            pass

    time_match = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if time_match:
        scheduled_time = datetime.combine(
            base_now.date(),
            datetime.min.time(),
        ).replace(
            hour=int(time_match.group(1)),
            minute=int(time_match.group(2)),
        )
        if scheduled_time < base_now:
            scheduled_time += timedelta(days=1)
        return scheduled_time

    return None


def get_upcoming_schedules(schedules, now=None):
    base_now = now or datetime.now()
    upcoming = []
    for schedule in schedules:
        scheduled_at = schedule["scheduled_at"]
        scheduled_datetime = parse_schedule_datetime(scheduled_at, base_now)
        if scheduled_datetime is None:
            continue

        is_date_only = re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", scheduled_at.strip())
        if is_date_only:
            is_future = scheduled_datetime.date() >= base_now.date()
        else:
            is_future = scheduled_datetime >= base_now

        if not is_future:
            continue

        upcoming.append(
            {
                "id": schedule["id"],
                "title": schedule["title"],
                "scheduled_at": scheduled_at,
                "scheduled_datetime": scheduled_datetime,
                "is_within_24h": scheduled_datetime <= base_now + timedelta(hours=24),
            }
        )

    upcoming.sort(key=lambda item: (item["scheduled_datetime"], item["id"]))
    return upcoming[:5]


def parse_calendar_month(value, today=None):
    base_date = today or date.today()
    text = str(value or "").strip()
    if not text:
        return base_date.replace(day=1)
    try:
        return datetime.strptime(text, "%Y-%m").date().replace(day=1)
    except ValueError:
        return base_date.replace(day=1)


def shift_month(month_start, offset):
    month_index = month_start.month - 1 + offset
    year = month_start.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def make_schedule_calendar_nav(month_start, target):
    previous_month = shift_month(month_start, -1).strftime("%Y-%m")
    next_month = shift_month(month_start, 1).strftime("%Y-%m")
    today_month = date.today().strftime("%Y-%m")
    if target == "index":
        return {
            "previous_url": url_for("index", active_tab="schedule", calendar_month=previous_month),
            "next_url": url_for("index", active_tab="schedule", calendar_month=next_month),
            "today_url": url_for("index", active_tab="schedule", calendar_month=today_month),
        }
    return {
        "previous_url": url_for("feature_page", feature_key="schedule-list", calendar_month=previous_month),
        "next_url": url_for("feature_page", feature_key="schedule-list", calendar_month=next_month),
        "today_url": url_for("feature_page", feature_key="schedule-list", calendar_month=today_month),
    }


def build_schedule_dashboard(schedules, selected_month=None, today=None):
    base_date = today or date.today()
    month_start = (selected_month or base_date).replace(day=1)
    _, month_days = calendar.monthrange(month_start.year, month_start.month)
    month_end = month_start.replace(day=month_days)
    week_end = base_date + timedelta(days=6)
    parsed_schedules = []

    for schedule in schedules:
        scheduled_datetime = parse_schedule_datetime(schedule["scheduled_at"])
        schedule_date = scheduled_datetime.date() if scheduled_datetime else None
        item = {
            "id": schedule["id"],
            "title": schedule["title"],
            "scheduled_at": schedule["scheduled_at"],
            "scheduled_date": schedule_date,
            "scheduled_datetime": scheduled_datetime,
        }
        parsed_schedules.append(item)

    def schedule_sort_key(item):
        return (
            item["scheduled_datetime"] or datetime.max,
            item["id"],
        )

    parsed_schedules.sort(key=schedule_sort_key)
    by_date = {}
    for item in parsed_schedules:
        if item["scheduled_date"] is None:
            continue
        by_date.setdefault(item["scheduled_date"], []).append(item)

    leading_empty = month_start.weekday()
    cells = []
    for _ in range(leading_empty):
        cells.append(None)
    for day in range(1, month_days + 1):
        current_date = month_start.replace(day=day)
        day_schedules = by_date.get(current_date, [])
        cells.append(
            {
                "date": current_date,
                "day": day,
                "is_today": current_date == base_date,
                "is_past": current_date < base_date,
                "schedules": day_schedules,
            }
        )
    while len(cells) % 7:
        cells.append(None)

    weeks = [cells[index:index + 7] for index in range(0, len(cells), 7)]
    today_schedules = by_date.get(base_date, [])
    week_schedules = [
        item
        for item in parsed_schedules
        if item["scheduled_date"] and base_date <= item["scheduled_date"] <= week_end
    ]
    month_schedules = [
        item
        for item in parsed_schedules
        if item["scheduled_date"] and month_start <= item["scheduled_date"] <= month_end
    ]
    unscheduled = [item for item in parsed_schedules if item["scheduled_date"] is None]
    month_groups = []
    for current_date in sorted({item["scheduled_date"] for item in month_schedules if item["scheduled_date"]}):
        month_groups.append(
            {
                "date": current_date,
                "date_label": f"{current_date.month}/{current_date.day}",
                "is_today": current_date == base_date,
                "schedules": by_date.get(current_date, []),
            }
        )

    year_months = []
    for month in range(1, 13):
        current_month = date(month_start.year, month, 1)
        _, current_month_days = calendar.monthrange(current_month.year, current_month.month)
        current_month_end = current_month.replace(day=current_month_days)
        count = sum(
            1
            for item in parsed_schedules
            if item["scheduled_date"] and current_month <= item["scheduled_date"] <= current_month_end
        )
        year_months.append(
            {
                "month": month,
                "label": f"{month}月",
                "count": count,
                "is_current": current_month == month_start,
            }
        )

    return {
        "month_label": f"{month_start.year}年{month_start.month}月",
        "month_value": month_start.strftime("%Y-%m"),
        "year_label": f"{month_start.year}年",
        "weekday_labels": ["月", "火", "水", "木", "金", "土", "日"],
        "weeks": weeks,
        "today_schedules": today_schedules,
        "week_schedules": week_schedules,
        "month_schedules": month_schedules,
        "month_groups": month_groups,
        "year_months": year_months,
        "unscheduled": unscheduled,
    }


def task_sort_key(task):
    priority_order = {"A": 0, "B": 1, "C": 2}
    deadline = task["deadline"] or "9999-12-31"
    return (
        deadline,
        priority_order.get(task["priority"], 9),
        task["id"],
    )


def parse_task_deadline_date(value):
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    return None


def build_deadline_notifications(tasks):
    today = date.today()
    groups = {
        "overdue": {"label": "期限超過", "tasks": []},
        "today": {"label": "本日期限", "tasks": []},
        "within_3_days": {"label": "3日以内", "tasks": []},
    }

    for task in tasks:
        if task["status"] == "完了" or not task["deadline"]:
            continue

        deadline_date = parse_task_deadline_date(task["deadline"])
        if not deadline_date:
            continue

        task_item = {
            "id": task["id"],
            "title": task["title"],
            "deadline": task["deadline"],
            "priority": task["priority"],
            "days_left": (deadline_date - today).days,
        }

        if deadline_date < today:
            groups["overdue"]["tasks"].append(task_item)
        elif deadline_date == today:
            groups["today"]["tasks"].append(task_item)
        elif deadline_date <= today + timedelta(days=3):
            groups["within_3_days"]["tasks"].append(task_item)

    ordered_groups = []
    total_count = 0
    for key in ("overdue", "today", "within_3_days"):
        group = groups[key]
        group["tasks"].sort(key=lambda item: (item["deadline"], item["id"]))
        group["count"] = len(group["tasks"])
        total_count += group["count"]
        ordered_groups.append(group)

    return {
        "count": total_count,
        "groups": ordered_groups,
    }


def build_secretary_suggestions(active_tasks, due_tasks, upcoming_schedules, transcripts):
    suggestions = []
    today_text = date.today().isoformat()
    tomorrow_text = (date.today() + timedelta(days=1)).isoformat()

    close_due_task = next(
        (
            task
            for task in due_tasks
            if task["deadline"] and task["deadline"] <= tomorrow_text
        ),
        due_tasks[0] if due_tasks else None,
    )
    if close_due_task:
        suggestions.append(f"{close_due_task['title']}の期限が近づいています。")

    urgent_schedule = next(
        (schedule for schedule in upcoming_schedules if schedule["is_within_24h"]),
        None,
    )
    if urgent_schedule:
        suggestions.append(f"{urgent_schedule['title']}の事前準備をおすすめします。")

    if len(active_tasks) >= 5:
        suggestions.append(f"未完了タスクが{len(active_tasks)}件あります。優先順位を見直しましょう。")

    for transcript in list(transcripts)[:3]:
        todos = extract_conversation_items(transcript["content"])["todos"]
        if todos:
            suggestions.append(f"最近の会話に未処理のやること候補があります：{todos[0]}")
            break

    return suggestions[:3]


def extract_question_keywords(question):
    text = re.sub(r"[？?。、,.!！\s]", "", str(question or ""))
    stop_words = (
        "今日",
        "明日",
        "何から",
        "やれば",
        "いい",
        "ですか",
        "した方がいい",
        "するべき",
        "急ぐ",
        "必要",
        "準備",
    )
    for word in stop_words:
        text = text.replace(word, " ")
    return [word for word in re.split(r"[はをへにがのともでから\s]+", text) if len(word) >= 2]


def find_related_task(question, tasks):
    normalized_question = re.sub(r"\s+", "", str(question or ""))
    keywords = extract_question_keywords(question)
    for task in tasks:
        title = str(task["title"] or "")
        if title and title in normalized_question:
            return task
        if any(keyword in title or title in keyword for keyword in keywords):
            return task
    return None


def find_related_schedule(question, upcoming_schedules):
    normalized_question = re.sub(r"\s+", "", str(question or ""))
    keywords = extract_question_keywords(question)
    for schedule in upcoming_schedules:
        title = str(schedule["title"] or "")
        if title and title in normalized_question:
            return schedule
        if any(keyword in title or title in keyword for keyword in keywords):
            return schedule
    return None


def build_secretary_consultation(question, tasks, upcoming_schedules, transcripts, suggestions):
    text = str(question or "").strip()
    active_tasks = [task for task in tasks if task["status"] != "完了"]
    active_tasks.sort(key=task_sort_key)
    due_tasks = [task for task in active_tasks if task["deadline"]]
    due_tasks.sort(key=task_sort_key)
    related_task = find_related_task(text, active_tasks)
    related_schedule = find_related_schedule(text, upcoming_schedules)
    answer_parts = []

    if related_task:
        answer_parts.append(f"{related_task['title']}は確認した方がいいです。")
        if related_task["deadline"]:
            answer_parts.append(f"期限は{related_task['deadline']}です。")
        if related_task["priority"] == "A":
            answer_parts.append("優先度Aなので、早めに片付けるのがおすすめです。")

    if related_schedule:
        answer_parts.append(f"{related_schedule['title']}の準備をおすすめします。")
        answer_parts.append(f"予定は{related_schedule['scheduled_at']}です。")

    if not answer_parts:
        if due_tasks:
            task = due_tasks[0]
            answer_parts.append(f"おすすめは{task['title']}です。")
            answer_parts.append("期限が近づいています。")
        elif active_tasks:
            task = active_tasks[0]
            answer_parts.append(f"まずは{task['title']}から始めるのがおすすめです。")
        elif upcoming_schedules:
            schedule = upcoming_schedules[0]
            answer_parts.append(f"{schedule['title']}の事前準備をおすすめします。")
        else:
            answer_parts.append("今のところ急ぎのタスクや予定は少なそうです。")

    if "明日" in text or "準備" in text or "予定" in text:
        urgent_schedule = next(
            (schedule for schedule in upcoming_schedules if schedule["is_within_24h"]),
            upcoming_schedules[0] if upcoming_schedules else None,
        )
        if urgent_schedule and not related_schedule:
            answer_parts.append(f"また、{urgent_schedule['title']}の準備も見ておくと安心です。")

    if len(active_tasks) >= 5 and not any("未完了タスク" in part for part in answer_parts):
        answer_parts.append(f"未完了タスクが{len(active_tasks)}件あるので、優先度Aと期限付きから進めましょう。")

    if suggestions:
        suggestion = suggestions[0]
        if not any(suggestion.rstrip("。") in part for part in answer_parts):
            answer_parts.append(f"秘書レポートでは「{suggestion}」も出ています。")

    recent_todos = []
    for transcript in list(transcripts)[:3]:
        recent_todos.extend(extract_conversation_items(transcript["content"])["todos"])
    if recent_todos and ("会話" in text or "連絡" in text):
        answer_parts.append(f"最近の会話では「{recent_todos[0]}」も未処理候補です。")

    return "\n".join(answer_parts[:4])


def build_secretary_report(tasks, upcoming_schedules, transcripts, contacts):
    active_tasks = [task for task in tasks if task["status"] != "完了"]
    due_tasks = [task for task in active_tasks if task["deadline"]]
    due_tasks.sort(key=task_sort_key)
    today_actions = sorted(active_tasks, key=task_sort_key)[:3]
    suggestions = build_secretary_suggestions(
        active_tasks,
        due_tasks,
        upcoming_schedules,
        transcripts,
    )

    return {
        "upcoming_schedules": upcoming_schedules[:3],
        "due_tasks": due_tasks[:3],
        "recent_transcripts": list(transcripts)[:3],
        "recent_contacts": list(contacts)[:3],
        "today_actions": today_actions,
        "suggestions": suggestions,
    }


def build_rule_based_summary(text):
    source_text = str(text or "").strip()
    sentences = split_conversation_sentences(source_text)
    summary_sentences = sentences[:3]
    items = extract_conversation_items(source_text)

    if summary_sentences:
        summary_text = " ".join(summary_sentences)
    else:
        summary_text = "要約できる内容がありません。"

    return {
        "summary": summary_text,
        "important": summary_sentences,
        "todos": items["todos"],
        "schedules": items["schedules"],
    }


def save_schedules(schedules):
    db = get_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved = []
    for schedule in schedules:
        cursor = db.execute(
            """
            INSERT INTO secretary_schedule (
                title,
                scheduled_at,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                schedule["title"],
                schedule["scheduled_at"],
                created_at,
            ),
        )
        saved.append(
            {
                "id": cursor.lastrowid,
                "title": schedule["title"],
                "scheduled_at": schedule["scheduled_at"],
            }
        )
    db.commit()
    return saved


def delete_schedule(schedule_id):
    db = get_db()
    db.execute(
        """
        DELETE FROM secretary_schedule
        WHERE id = ?
        """,
        (schedule_id,),
    )
    db.commit()


def fetch_transcripts():
    return get_db().execute(
        """
        SELECT id, content, created_at
        FROM secretary_transcripts
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()


def save_transcript(content):
    text = str(content or "").strip()
    if not text:
        return None

    db = get_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db.execute(
        """
        INSERT INTO secretary_transcripts (
            content,
            created_at
        )
        VALUES (?, ?)
        """,
        (text, created_at),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "content": text,
        "created_at": created_at,
    }


def delete_transcript(transcript_id):
    db = get_db()
    db.execute(
        """
        DELETE FROM secretary_transcripts
        WHERE id = ?
        """,
        (transcript_id,),
    )
    db.commit()


def fetch_contacts():
    return get_db().execute(
        """
        SELECT id, name, company, phone, email, created_at
        FROM secretary_contacts
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()


def fetch_contact(contact_id):
    return get_db().execute(
        """
        SELECT id, name, company, phone, email, created_at
        FROM secretary_contacts
        WHERE id = ?
        """,
        (contact_id,),
    ).fetchone()


def fetch_contact_by_name(name):
    clean_name = str(name or "").strip()
    if not clean_name:
        return None
    return get_db().execute(
        """
        SELECT id, name, company, phone, email, created_at
        FROM secretary_contacts
        WHERE lower(name) = lower(?)
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (clean_name,),
    ).fetchone()


def escape_vcard_value(value):
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return (
        text.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def safe_vcard_filename(name):
    clean_name = re.sub(r'[\\/:*?"<>|]+', "_", str(name or "").strip())
    clean_name = clean_name.strip(" .")
    return clean_name or "contact"


def build_contact_vcard(contact):
    name = str(contact["name"] or "").strip()
    company = str(contact["company"] or "").strip()
    phone = str(contact["phone"] or "").strip()
    email = str(contact["email"] or "").strip()
    display_name = name or company or phone or email or "連絡先"
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{escape_vcard_value(display_name)}",
    ]
    if name:
        lines.append(f"N:{escape_vcard_value(name)};;;;")
    if company:
        lines.append(f"ORG:{escape_vcard_value(company)}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{escape_vcard_value(phone)}")
    if email:
        lines.append(f"EMAIL;TYPE=INTERNET:{escape_vcard_value(email)}")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def save_contact(contact):
    clean_contact = {
        "name": str(contact.get("name", "")).strip(),
        "company": str(contact.get("company", "")).strip(),
        "phone": str(contact.get("phone", "")).strip(),
        "email": str(contact.get("email", "")).strip(),
    }
    if not any(clean_contact.values()):
        return None

    db = get_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing_contact = fetch_contact_by_name(clean_contact["name"])
    if existing_contact:
        merged_contact = {
            "name": clean_contact["name"] or str(existing_contact["name"] or "").strip(),
            "company": clean_contact["company"] or str(existing_contact["company"] or "").strip(),
            "phone": clean_contact["phone"] or str(existing_contact["phone"] or "").strip(),
            "email": clean_contact["email"] or str(existing_contact["email"] or "").strip(),
        }
        db.execute(
            """
            UPDATE secretary_contacts
            SET name = ?,
                company = ?,
                phone = ?,
                email = ?
            WHERE id = ?
            """,
            (
                merged_contact["name"],
                merged_contact["company"],
                merged_contact["phone"],
                merged_contact["email"],
                existing_contact["id"],
            ),
        )
        db.commit()
        return {
            "id": existing_contact["id"],
            **merged_contact,
            "created_at": existing_contact["created_at"],
            "updated": True,
        }

    cursor = db.execute(
        """
        INSERT INTO secretary_contacts (
            name,
            company,
            phone,
            email,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            clean_contact["name"],
            clean_contact["company"],
            clean_contact["phone"],
            clean_contact["email"],
            created_at,
        ),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        **clean_contact,
        "created_at": created_at,
        "updated": False,
    }


def delete_contact(contact_id):
    db = get_db()
    db.execute(
        """
        DELETE FROM secretary_contacts
        WHERE id = ?
        """,
        (contact_id,),
    )
    db.commit()


def fetch_money_records(limit=10):
    return get_db().execute(
        """
        SELECT id, type, amount, memo, created_at
        FROM secretary_money
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def get_money_month_summary():
    month_prefix = datetime.now().strftime("%Y-%m")
    rows = get_db().execute(
        """
        SELECT type, amount
        FROM secretary_money
        WHERE created_at LIKE ?
        """,
        (f"{month_prefix}%",),
    ).fetchall()
    income = sum(row["amount"] for row in rows if row["type"] == "収入")
    expense = sum(row["amount"] for row in rows if row["type"] == "支出")
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
    }


def save_money_record(record):
    money_type = str(record.get("type", "")).strip()
    memo = str(record.get("memo", "")).strip()
    amount_text = normalize_number_text(record.get("amount", "")).strip()

    if money_type not in ("支出", "収入"):
        return None

    try:
        amount = int(Decimal(amount_text).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return None

    if amount <= 0:
        return None

    db = get_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db.execute(
        """
        INSERT INTO secretary_money (
            type,
            amount,
            memo,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (money_type, amount, memo, created_at),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "type": money_type,
        "amount": amount,
        "memo": memo,
        "created_at": created_at,
    }


def delete_money_record(record_id):
    db = get_db()
    db.execute(
        """
        DELETE FROM secretary_money
        WHERE id = ?
        """,
        (record_id,),
    )
    db.commit()


def clean_ocr_lines(text):
    lines = []
    for line in str(text or "").splitlines():
        clean_line = re.sub(r"\s+", " ", line).strip(" 　\t\r\n:：|")
        if clean_line:
            lines.append(clean_line)
    return lines


def is_noise_name_line(line):
    if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
        return True
    if any(keyword in line for keyword in COMPANY_KEYWORDS):
        return True
    if re.search(r"(TEL|Tel|tel|FAX|Fax|mail|Mail|Email|E-mail|URL|http|www\.)", line):
        return True
    if re.search(r"\d", line):
        return True
    return len(line) > 24


def guess_business_card_contact(text):
    lines = clean_ocr_lines(text)
    email_match = EMAIL_PATTERN.search(text or "")
    phone_match = PHONE_PATTERN.search(text or "")
    company = ""
    name = ""

    for line in lines:
        if any(keyword in line for keyword in COMPANY_KEYWORDS):
            company = line
            break

    for line in lines:
        if is_noise_name_line(line):
            continue
        name = line
        break

    return {
        "name": name,
        "company": company,
        "phone": phone_match.group(0).strip() if phone_match else "",
        "email": email_match.group(0).strip() if email_match else "",
    }


def run_business_card_ocr(image_file):
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as error:
        raise RuntimeError(
            "名刺読み取りの準備が未完了です。手入力で連絡先保存は使えます。"
        ) from error

    try:
        import pytesseract
        from pytesseract import TesseractError
        from pytesseract.pytesseract import TesseractNotFoundError
    except ImportError as error:
        raise RuntimeError(
            "名刺読み取りの準備が未完了です。手入力で連絡先保存は使えます。"
        ) from error

    try:
        image = Image.open(image_file.stream)
        image = image.convert("RGB")
    except UnidentifiedImageError as error:
        raise ValueError("画像ファイルを読み取れませんでした。") from error

    try:
        text = pytesseract.image_to_string(image, lang="jpn+eng")
    except TesseractNotFoundError as error:
        raise RuntimeError(
            "名刺読み取り本体が未導入です。手入力で連絡先保存は使えます。"
        ) from error
    except TesseractError:
        text = pytesseract.image_to_string(image, lang="eng")

    return str(text or "").strip()


def get_current_datetime_display():
    now = datetime.now()
    weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]
    hour = now.hour
    if 5 <= hour < 11:
        greeting = "おはようございます"
        message = "今日の予定と大切なことを、私がそっと整えます。"
    elif 11 <= hour < 16:
        greeting = "こんにちは"
        message = "午後のご予定も、必要なところから上品に整えます。"
    elif 16 <= hour < 19:
        greeting = "お疲れさまです"
        message = "今日の残りを確認しながら、落ち着いて整えましょう。"
    elif 19 <= hour < 24:
        greeting = "こんばんは"
        message = "夜は無理をせず、必要なことだけ一緒に片づけます。"
    else:
        greeting = "遅くまでお疲れさまです"
        message = "遅い時間です。大切なことだけ整えて、休む準備をしましょう。"
    return {
        "date": f"{now:%Y-%m-%d}（{weekday_labels[now.weekday()]}）",
        "time": f"{now:%H:%M}",
        "greeting": greeting,
        "message": message,
    }


def complete_task(task_id):
    db = get_db()
    db.execute(
        """
        UPDATE secretary_tasks
        SET status = '完了'
        WHERE id = ?
        """,
        (task_id,),
    )
    db.commit()


def delete_task(task_id):
    db = get_db()
    db.execute(
        """
        DELETE FROM secretary_tasks
        WHERE id = ?
        """,
        (task_id,),
    )
    db.commit()


def get_audio_extension(mime_type):
    clean_mime = (mime_type or "").split(";")[0].strip().lower()
    return AUDIO_EXTENSION_BY_MIME.get(clean_mime, ".webm")


def add_imageio_ffmpeg_to_path():
    try:
        import imageio_ffmpeg
    except ImportError:
        return

    source_path = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    RUNTIME_BIN_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = RUNTIME_BIN_DIR / "ffmpeg.exe"
    if not ffmpeg_path.exists():
        shutil.copyfile(source_path, ffmpeg_path)
    os.environ["PATH"] = f"{RUNTIME_BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"


def load_whisper_model():
    global whisper_model
    if whisper_model is None:
        try:
            import whisper
        except ImportError as error:
            raise RuntimeError(
                "文字起こし環境が未準備です。openai-whisper をインストールしてください。"
            ) from error

        add_imageio_ffmpeg_to_path()
        whisper_model = whisper.load_model(WHISPER_MODEL_NAME)
    return whisper_model


def transcribe_audio_file(file_name):
    safe_file_name = Path(str(file_name or "")).name
    if not safe_file_name:
        raise ValueError("文字起こし対象の録音ファイルがありません。")

    audio_path = UPLOAD_AUDIO_DIR / safe_file_name
    if not audio_path.exists():
        raise FileNotFoundError("録音ファイルが見つかりません。")

    model = load_whisper_model()
    try:
        result = model.transcribe(str(audio_path), language="ja", fp16=False)
    except FileNotFoundError as error:
        raise RuntimeError(
            "文字起こしに必要な音声変換処理が見つかりません。"
        ) from error
    text = str(result.get("text", "")).strip()
    return text or "文字起こし結果が空でした。"


@app.post("/license/verify")
def verify_license():
    data = request.get_json(silent=True) or {}
    input_key = str(data.get("license_key", "")).strip()

    if license_key_is_valid(input_key):
        session["license_approved"] = True
        return jsonify({"ok": True, "message": "利用できます。"})

    session.pop("license_approved", None)
    return jsonify({"ok": False, "message": "利用キーが正しくありません"}), 403


@app.get("/license/status")
def license_status():
    return jsonify({"ok": is_license_approved()})


def list_license_keys():
    init_db()
    rows = get_db().execute(
        """
        SELECT *
        FROM secretary_license_keys
        ORDER BY is_active DESC, created_at DESC
        """
    ).fetchall()
    return [
        {
            **dict(row),
            "is_expired": is_license_key_expired(row["expires_on"]),
        }
        for row in rows
    ]


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if is_admin_approved():
        return redirect(url_for("admin_users"))

    message = ""
    admin_key_ready = bool(get_admin_key())
    if request.method == "POST":
        input_key = str(request.form.get("admin_key", "")).strip()
        admin_key = get_admin_key()
        if admin_key and input_key == admin_key:
            session["admin_approved"] = True
            return redirect(url_for("admin_users"))
        message = "管理キーが正しくありません。"

    return render_template(
        "admin_login.html",
        settings=load_settings(),
        message=message,
        admin_key_ready=admin_key_ready,
    )


@app.get("/admin/users")
def admin_users():
    return render_template(
        "admin_users.html",
        settings=load_settings(),
        license_keys=list_license_keys(),
        main_license_enabled=bool(str(load_settings().get("license_key", "")).strip()),
    )


@app.post("/admin/users/add")
def admin_add_user():
    license_key = str(request.form.get("license_key", "")).strip()
    memo = str(request.form.get("memo", "")).strip()
    expires_on = normalize_date_text(request.form.get("expires_on", ""))

    if not license_key:
        return redirect(url_for("admin_users"))

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO secretary_license_keys (
                license_key,
                memo,
                expires_on,
                is_active,
                use_count,
                last_used_at,
                created_at,
                disabled_at
            )
            VALUES (?, ?, ?, 1, 0, '', ?, '')
            """,
            (
                license_key,
                memo,
                expires_on,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.execute(
            """
            UPDATE secretary_license_keys
            SET memo = ?,
                expires_on = ?,
                is_active = 1,
                disabled_at = ''
            WHERE license_key = ?
            """,
            (memo, expires_on, license_key),
        )
        db.commit()

    return redirect(url_for("admin_users"))


@app.post("/admin/users/<int:license_id>/disable")
def admin_disable_user(license_id):
    db = get_db()
    db.execute(
        """
        UPDATE secretary_license_keys
        SET is_active = 0,
            disabled_at = ?
        WHERE id = ?
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M"), license_id),
    )
    db.commit()
    return redirect(url_for("admin_users"))


@app.post("/admin/logout")
def admin_logout():
    session.pop("admin_approved", None)
    return redirect(url_for("admin_login"))


@app.route("/", methods=["GET", "POST"])
def index():
    init_db()
    source_text = ""
    extracted_tasks = []
    extracted_schedules = []
    saved = False
    if request.method == "POST":
        source_text = request.form.get("source_text", "").strip()
        if source_text:
            extracted_tasks = extract_tasks(source_text)
            if extracted_tasks:
                save_tasks(extracted_tasks)

            schedule_units = []
            conversation_items = extract_conversation_items(source_text)
            schedule_units.extend(conversation_items["schedules"])
            for unit in split_secretary_request_units(source_text):
                if is_schedule_request(unit):
                    schedule_units.append(unit)
            extracted_schedules = [
                parse_schedule_item(item)
                for item in unique_items(schedule_units)
                if str(item or "").strip()
            ]
            if extracted_schedules:
                save_schedules(extracted_schedules)

            saved = bool(extracted_tasks or extracted_schedules)

    tasks = fetch_tasks()
    schedules = fetch_schedules()
    upcoming_schedules = get_upcoming_schedules(schedules)
    selected_calendar_month = parse_calendar_month(request.args.get("calendar_month"))
    schedule_dashboard = build_schedule_dashboard(schedules, selected_calendar_month)
    schedule_calendar_nav = make_schedule_calendar_nav(selected_calendar_month, "index")
    transcripts = fetch_transcripts()
    contacts = fetch_contacts()
    money_records = fetch_money_records()
    money_summary = get_money_month_summary()
    fortune_calendar = build_fortune_calendar()
    secretary_report = build_secretary_report(
        tasks,
        upcoming_schedules,
        transcripts,
        contacts,
    )
    requested_tab = request.args.get("active_tab", "home")
    initial_tab = requested_tab if requested_tab in {"home", "schedule", "talk", "money", "settings"} else "home"
    active_tasks = [task for task in tasks if task["status"] == "未着手"]
    active_task_count = len(active_tasks)
    important_tasks = active_tasks[:3]
    deadline_notifications = build_deadline_notifications(tasks)
    today_text = date.today().isoformat()
    due_alert_tasks = [
        task
        for task in tasks
        if task["status"] != "完了"
        and task["deadline"]
        and task["deadline"] <= today_text
    ]
    settings = load_settings()
    current_datetime = get_current_datetime_display()
    google_calendar_status = get_google_calendar_status()
    google_calendar_events = []
    google_calendar_events_message = ""
    if google_calendar_status["connected"] and google_calendar_status["libraries_ready"]:
        try:
            google_calendar_events = fetch_google_calendar_events()
            if not google_calendar_events:
                google_calendar_events_message = "今後の外部予定表の予定はありません。"
        except Exception as error:
            google_calendar_events_message = f"外部予定表の予定を取得できませんでした: {error}"
    elif not google_calendar_status["connected"]:
        google_calendar_events_message = "外部予定表は未連携です。必要な場合だけ連携してください。"
    elif not google_calendar_status["libraries_ready"]:
        google_calendar_events_message = google_calendar_status["library_message"]

    return render_template(
        "index.html",
        source_text=source_text,
        extracted_tasks=extracted_tasks,
        extracted_schedules=extracted_schedules,
        tasks=tasks,
        schedules=schedules,
        schedule_dashboard=schedule_dashboard,
        schedule_calendar_nav=schedule_calendar_nav,
        upcoming_schedules=upcoming_schedules,
        transcripts=transcripts,
        transcript_count=len(transcripts),
        contacts=contacts,
        money_records=money_records,
        money_summary=money_summary,
        fortune_calendar=fortune_calendar,
        secretary_report=secretary_report,
        active_task_count=active_task_count,
        important_tasks=important_tasks,
        deadline_notifications=deadline_notifications,
        due_alert_tasks=due_alert_tasks,
        settings=settings,
        design_themes=DESIGN_THEMES,
        current_character=get_current_character(settings),
        current_datetime=current_datetime,
        google_calendar_status=google_calendar_status,
        google_calendar_message=request.args.get("google_calendar_message", ""),
        google_calendar_events=google_calendar_events,
        google_calendar_events_message=google_calendar_events_message,
        initial_tab=initial_tab,
        saved=saved,
    )


@app.route("/apple-touch-icon.png")
def apple_touch_icon():
    return send_from_directory(BASE_DIR / "static", "apple-touch-icon.png", mimetype="image/png")


FEATURE_PAGES = {
    "schedule-list": ("予定一覧", "近い予定と大切なタスクを、ひと目で確認できます。", "schedule"),
    "schedule-add": ("予定追加", "メモした内容から、予定やタスクを丁寧に整理します。", "schedule"),
    "alerts": ("通知・アラーム", "期限が近いものを見落とさないように確認します。", "schedule"),
    "recording": ("音声メモ", "録音できる時は録音し、難しい時は音声ファイルを選んで整理できます。", "talk"),
    "call-memo": ("通話メモ", "スピーカー通話をマイクで拾い、保存後に文字起こしできます。", "talk"),
    "transcripts": ("文字起こし履歴", "保存した会話を、必要な時に見返せます。", "talk"),
    "conversation": ("会話整理", "相談、要約、写真、名刺管理をまとめて扱えます。", "talk"),
    "expense": ("支出登録", "使ったお金を、すばやく分かりやすく記録します。", "money"),
    "income": ("収入登録", "入ったお金を記録し、今月の状況へ反映します。", "money"),
    "month-summary": ("今月集計", "今月のお金の流れを、落ち着いて確認できます。", "money"),
    "integration-settings": ("連携設定", "カレンダーやAI拡張は、必要な方だけ後から追加できます。", "settings"),
    "design-settings": ("見た目と使いやすさ", "テーマ、文字サイズ、ホーム画面追加をここで整えます。", "settings"),
}



@app.route("/feature/<feature_key>", methods=["GET", "POST"])
def feature_page(feature_key):
    if feature_key not in FEATURE_PAGES:
        return redirect(url_for("index"))

    init_db()
    source_text = ""
    extracted_tasks = []
    extracted_schedules = []
    saved = False
    if request.method == "POST":
        source_text = request.form.get("source_text", "").strip()
        if source_text:
            extracted_tasks = extract_tasks(source_text)
            if extracted_tasks:
                save_tasks(extracted_tasks)

            schedule_units = []
            conversation_items = extract_conversation_items(source_text)
            schedule_units.extend(conversation_items["schedules"])
            for unit in split_secretary_request_units(source_text):
                if is_schedule_request(unit):
                    schedule_units.append(unit)
            extracted_schedules = [
                parse_schedule_item(item)
                for item in unique_items(schedule_units)
                if str(item or "").strip()
            ]
            if extracted_schedules:
                save_schedules(extracted_schedules)

            saved = bool(extracted_tasks or extracted_schedules)

    tasks = fetch_tasks()
    schedules = fetch_schedules()
    upcoming_schedules = get_upcoming_schedules(schedules)
    selected_calendar_month = parse_calendar_month(request.args.get("calendar_month"))
    schedule_dashboard = build_schedule_dashboard(schedules, selected_calendar_month)
    schedule_calendar_nav = make_schedule_calendar_nav(selected_calendar_month, "feature")
    transcripts = fetch_transcripts()
    contacts = fetch_contacts()
    money_records = fetch_money_records()
    money_summary = get_money_month_summary()
    fortune_calendar = build_fortune_calendar()
    secretary_report = build_secretary_report(
        tasks,
        upcoming_schedules,
        transcripts,
        contacts,
    )
    active_tasks = [task for task in tasks if task["status"] == "未着手"]
    active_task_count = len(active_tasks)
    important_tasks = active_tasks[:3]
    deadline_notifications = build_deadline_notifications(tasks)
    today_text = date.today().isoformat()
    due_alert_tasks = [
        task
        for task in tasks
        if task["status"] != "完了"
        and task["deadline"]
        and task["deadline"] <= today_text
    ]
    settings = load_settings()
    current_datetime = get_current_datetime_display()
    google_calendar_status = get_google_calendar_status()
    google_calendar_events = []
    google_calendar_events_message = ""
    if google_calendar_status["connected"] and google_calendar_status["libraries_ready"]:
        try:
            google_calendar_events = fetch_google_calendar_events()
            if not google_calendar_events:
                google_calendar_events_message = "今後の外部予定表の予定はありません。"
        except Exception as error:
            google_calendar_events_message = f"外部予定表の予定を取得できませんでした: {error}"
    elif not google_calendar_status["connected"]:
        google_calendar_events_message = "外部予定表は未連携です。必要な場合だけ連携してください。"
    elif not google_calendar_status["libraries_ready"]:
        google_calendar_events_message = google_calendar_status["library_message"]

    feature_title, feature_lead, back_tab = FEATURE_PAGES[feature_key]
    return render_template(
        "feature_page.html",
        feature_key=feature_key,
        feature_title=feature_title,
        feature_lead=feature_lead,
        back_tab=back_tab,
        source_text=source_text,
        extracted_tasks=extracted_tasks,
        extracted_schedules=extracted_schedules,
        tasks=tasks,
        schedules=schedules,
        schedule_dashboard=schedule_dashboard,
        schedule_calendar_nav=schedule_calendar_nav,
        upcoming_schedules=upcoming_schedules,
        transcripts=transcripts,
        transcript_count=len(transcripts),
        contacts=contacts,
        money_records=money_records,
        money_summary=money_summary,
        fortune_calendar=fortune_calendar,
        secretary_report=secretary_report,
        active_task_count=active_task_count,
        important_tasks=important_tasks,
        deadline_notifications=deadline_notifications,
        due_alert_tasks=due_alert_tasks,
        settings=settings,
        design_themes=DESIGN_THEMES,
        current_character=get_current_character(settings),
        current_datetime=current_datetime,
        google_calendar_status=google_calendar_status,
        google_calendar_message=request.args.get("google_calendar_message", ""),
        google_calendar_events=google_calendar_events,
        google_calendar_events_message=google_calendar_events_message,
        saved=saved,
    )


@app.post("/settings/design-theme")
def save_design_theme_action():
    settings = load_settings()
    selected_theme = str(request.form.get("design_theme", "")).strip()
    theme_ids = {theme["id"] for theme in DESIGN_THEMES}
    if selected_theme in theme_ids:
        settings["design_theme"] = selected_theme
        save_settings(settings)
    return redirect(url_for("feature_page", feature_key="design-settings"))


@app.get("/future-features")
def future_features():
    settings = load_settings()
    return render_template(
        "future_features.html",
        settings=settings,
        current_character=get_current_character(settings),
        current_datetime=get_current_datetime_display(),
    )


@app.get("/update-history")
def update_history():
    settings = load_settings()
    history_items = [
        {
            "version": "v5.1",
            "label": "お知らせページの追加",
            "changes": [
                "今後の機能を確認できるページを追加",
                "ホームから更新情報へ移動しやすく整理",
            ],
        },
        {
            "version": "v5.0",
            "label": "外部予定表の任意連携",
            "changes": [
                "外部予定表連携を任意機能として準備",
                "外部予定表の確認に対応",
                "保存した予定の登録導線を追加",
            ],
        },
        {
            "version": "v6.0",
            "label": "プレゼント版AI秘書",
            "changes": [
                "アプリ風ホーム画面を整備",
                "秘書キャラと高級感あるテーマを追加",
                "名刺管理、写真、連絡先一覧を追加",
                "会話整理、録音、お金管理、文章作成を整理",
            ],
        },
    ]
    return render_template(
        "update_history.html",
        settings=settings,
        current_character=get_current_character(settings),
        current_datetime=get_current_datetime_display(),
        history_items=history_items,
    )


@app.get("/welcome-guide")
def welcome_guide():
    settings = load_settings()
    return render_template(
        "welcome_guide.html",
        settings=settings,
        current_character=get_current_character(settings),
        current_datetime=get_current_datetime_display(),
    )


@app.get("/app-info")
def app_info():
    settings = load_settings()
    return render_template(
        "app_info.html",
        settings=settings,
        current_character=get_current_character(settings),
        current_datetime=get_current_datetime_display(),
    )


@app.post("/tasks/<int:task_id>/complete")
def complete_task_action(task_id):
    init_db()
    complete_task(task_id)
    return redirect(url_for("index"))


@app.post("/tasks/<int:task_id>/delete")
def delete_task_action(task_id):
    init_db()
    delete_task(task_id)
    return redirect(url_for("index"))


@app.post("/contacts")
def save_contact_action():
    init_db()
    data = request.get_json(silent=True) or {}
    saved_contact = save_contact(data)
    if not saved_contact:
        return jsonify({"ok": False, "message": "保存する連絡先候補がありません。"}), 400

    return jsonify(
        {
            "ok": True,
            "message": "連絡先を更新しました" if saved_contact.get("updated") else "連絡先を保存しました",
            "contact": saved_contact,
        }
    )


@app.post("/contacts/<int:contact_id>/delete")
def delete_contact_action(contact_id):
    init_db()
    delete_contact(contact_id)
    return redirect(url_for("index"))


@app.get("/contacts/<int:contact_id>/vcf")
def contact_vcf_action(contact_id):
    init_db()
    contact = fetch_contact(contact_id)
    if not contact:
        return "連絡先が見つかりません。", 404

    vcard = build_contact_vcard(contact)
    file_name = f"{safe_vcard_filename(contact['name'] or contact['company'])}.vcf"
    return Response(
        vcard,
        content_type="text/vcard; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}",
        },
    )


@app.post("/money")
def save_money_action():
    init_db()
    saved_record = save_money_record(request.form)
    return redirect(url_for("index"))


@app.post("/money/<int:record_id>/delete")
def delete_money_action(record_id):
    init_db()
    delete_money_record(record_id)
    return redirect(url_for("index"))


@app.post("/business-card/ocr")
def business_card_ocr_action():
    image_file = request.files.get("image")
    if image_file is None:
        return jsonify({"ok": False, "message": "名刺画像がありません。"}), 400

    if not (image_file.mimetype or "").startswith("image/"):
        return jsonify({"ok": False, "message": "画像ファイルを選択してください。"}), 400

    try:
        text = run_business_card_ocr(image_file)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"ok": False, "message": str(error)}), 503

    contact = guess_business_card_contact(text)
    return jsonify(
        {
            "ok": True,
            "message": "読み取り結果を連絡先候補へ入力しました。必要に応じて修正して保存してください。",
            "text": text,
            "contact": contact,
        }
    )


@app.post("/schedules/<int:schedule_id>/delete")
def delete_schedule_action(schedule_id):
    init_db()
    delete_schedule(schedule_id)
    return redirect(url_for("index"))


@app.post("/schedules/<int:schedule_id>/google-calendar")
def register_schedule_google_calendar_action(schedule_id):
    init_db()
    schedule = fetch_schedule(schedule_id)
    if schedule is None:
        message = "予定が見つかりませんでした。"
    else:
        try:
            result = register_schedule_to_google_calendar(schedule)
            message = result.get("message", "外部予定表へ登録しました。")
        except (RuntimeError, ValueError) as error:
            message = str(error)
        except Exception as error:
            message = f"外部予定表への登録に失敗しました: {error}"

    return redirect(url_for("index", google_calendar_message=message, active_tab="schedule"))


@app.get("/google-calendar/login")
def google_calendar_login():
    try:
        flow = get_google_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
    except (RuntimeError, FileNotFoundError) as error:
        return redirect(url_for("index", google_calendar_message=str(error)))

    session["google_calendar_oauth_state"] = state
    return redirect(authorization_url)


@app.get("/google-calendar/callback")
def google_calendar_callback():
    state = session.get("google_calendar_oauth_state")
    if not state:
        return redirect(
            url_for(
                "index",
                google_calendar_message="外部予定表の認証状態を確認できませんでした。もう一度連携してください。",
            )
        )

    try:
        flow = get_google_oauth_flow(state=state)
        flow.fetch_token(authorization_response=request.url)
    except Exception as error:
        return redirect(
            url_for(
                "index",
                google_calendar_message=f"外部予定表の認証に失敗しました: {error}",
            )
        )

    credentials = flow.credentials
    GOOGLE_TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    session.pop("google_calendar_oauth_state", None)
    return redirect(
        url_for(
            "index",
            google_calendar_message="外部予定表に接続しました。",
        )
    )


@app.post("/transcripts/<int:transcript_id>/delete")
def delete_transcript_action(transcript_id):
    init_db()
    delete_transcript(transcript_id)
    return redirect(url_for("index"))


@app.post("/recordings")
def save_recording():
    audio_file = request.files.get("audio")
    if audio_file is None:
        return jsonify({"ok": False, "message": "音声データがありません。"}), 400

    audio_bytes = audio_file.read()
    if not audio_bytes:
        return jsonify({"ok": False, "message": "音声データが空です。"}), 400

    UPLOAD_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    extension = get_audio_extension(audio_file.mimetype)
    file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{extension}"
    save_path = UPLOAD_AUDIO_DIR / file_name
    save_path.write_bytes(audio_bytes)

    return jsonify(
        {
            "ok": True,
            "message": "録音を保存しました。",
            "file_name": file_name,
        }
    )


@app.post("/recordings/transcribe")
def transcribe_recording():
    data = request.get_json(silent=True) or {}
    file_name = data.get("file_name", "")

    try:
        text = transcribe_audio_file(file_name)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400
    except FileNotFoundError as error:
        return jsonify({"ok": False, "message": str(error)}), 404
    except RuntimeError as error:
        return jsonify({"ok": False, "message": str(error)}), 500
    except Exception:
        return jsonify({"ok": False, "message": "文字起こしに失敗しました。"}), 500

    transcript = save_transcript(text)
    return jsonify(
        {
            "ok": True,
            "message": "文字起こしが完了しました。",
            "text": text,
            "transcript": transcript,
        }
    )


@app.post("/conversation/organize")
def organize_conversation():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"ok": False, "message": "整理する文字起こし結果がありません。"}), 400

    result = extract_conversation_items(text)
    return jsonify(
        {
            "ok": True,
            "message": "整理が完了しました。",
            "todos": result["todos"],
            "schedules": result["schedules"],
        }
    )


@app.post("/conversation/summarize")
def summarize_conversation():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"ok": False, "message": "要約する文章がありません。"}), 400

    summary = build_rule_based_summary(text)
    return jsonify(
        {
            "ok": True,
            "message": "要約しました。",
            **summary,
        }
    )


@app.post("/secretary/consult")
def consult_secretary():
    init_db()
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"ok": False, "message": "相談内容を入力してください。"}), 400

    tasks = fetch_tasks()
    schedules = fetch_schedules()
    upcoming_schedules = get_upcoming_schedules(schedules)
    transcripts = fetch_transcripts()
    active_tasks = [task for task in tasks if task["status"] != "完了"]
    due_tasks = [task for task in active_tasks if task["deadline"]]
    due_tasks.sort(key=task_sort_key)
    suggestions = build_secretary_suggestions(
        active_tasks,
        due_tasks,
        upcoming_schedules,
        transcripts,
    )
    answer = build_secretary_consultation(
        question,
        tasks,
        upcoming_schedules,
        transcripts,
        suggestions,
    )
    return jsonify({"ok": True, "answer": answer})


@app.post("/secretary/route")
def route_secretary_request():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"ok": False, "message": "振り分ける内容を入力してください。"}), 400

    candidates = build_secretary_route_candidates(text)
    return jsonify(
        {
            "ok": True,
            "message": "候補を整理しました。",
            "candidates": candidates,
        }
    )


@app.post("/calculator/calculate")
def calculate_action():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"ok": False, "message": "計算する内容を入力してください。"}), 400

    try:
        value = calculate_voice_expression(text)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400

    return jsonify(
        {
            "ok": True,
            "result": format_calculator_result(value, text),
        }
    )


@app.post("/weather")
def weather_action():
    data = request.get_json(silent=True) or {}
    location = str(data.get("location", "")).strip()
    try:
        report = fetch_weather_report(location)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400
    except Exception:
        return jsonify({"ok": False, "message": "天気を取得できませんでした。"}), 500

    return jsonify({"ok": True, "weather": report})


@app.post("/travel/search")
def travel_search_action():
    data = request.get_json(silent=True) or {}
    origin = str(data.get("origin", "")).strip()
    destination = str(data.get("destination", "")).strip()
    try:
        travel = build_travel_support(origin, destination)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400

    return jsonify({"ok": True, "travel": travel})


@app.post("/writer/generate")
def writer_generate_action():
    data = request.get_json(silent=True) or {}
    kind = str(data.get("kind", "")).strip()
    recipient = str(data.get("recipient", "")).strip()
    content = str(data.get("content", "")).strip()
    if not kind:
        return jsonify({"ok": False, "message": "文章種別を選んでください。"}), 400

    text = generate_document_text(kind, recipient, content)
    return jsonify({"ok": True, "text": text})


@app.post("/writer/suggestions")
def writer_suggestions_action():
    init_db()
    tasks = fetch_tasks()
    schedules = fetch_schedules()
    upcoming_schedules = get_upcoming_schedules(schedules)
    transcripts = fetch_transcripts()
    contacts = fetch_contacts()
    suggestions = build_writer_suggestions(
        tasks,
        upcoming_schedules,
        transcripts,
        contacts,
    )
    return jsonify({"ok": True, "suggestions": suggestions})


@app.post("/conversation/save-todos")
def save_conversation_todos():
    init_db()
    data = request.get_json(silent=True) or {}
    todo_items = data.get("todos", [])
    source_text = str(data.get("source_text", "")).strip()

    if not isinstance(todo_items, list):
        return jsonify({"ok": False, "message": "保存するやること候補がありません。"}), 400

    tasks = build_conversation_tasks(todo_items, source_text)
    if not tasks:
        return jsonify({"ok": False, "message": "保存するやること候補がありません。"}), 400

    save_tasks(tasks)
    return jsonify(
        {
            "ok": True,
            "message": "保存しました",
            "saved_count": len(tasks),
        }
    )


@app.post("/conversation/save-schedules")
def save_conversation_schedules():
    init_db()
    data = request.get_json(silent=True) or {}
    schedule_items = data.get("schedules", [])

    if not isinstance(schedule_items, list):
        return jsonify({"ok": False, "message": "保存する予定候補がありません。"}), 400

    schedules = [
        parse_schedule_item(item)
        for item in schedule_items
        if str(item or "").strip()
    ]
    if not schedules:
        return jsonify({"ok": False, "message": "保存する予定候補がありません。"}), 400

    saved_schedules = save_schedules(schedules)
    return jsonify(
        {
            "ok": True,
            "message": "予定を保存しました",
            "schedules": saved_schedules,
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
