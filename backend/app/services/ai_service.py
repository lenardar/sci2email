import json
from datetime import datetime, timezone
from urllib import request
from urllib.error import URLError

from app.core.config import settings
from sqlalchemy.orm import Session

from app.models import AppConfig, FeedEntry


def _fallback_bilingual(entry: FeedEntry) -> dict:
    en_title = entry.title_en or entry.title or "Untitled"
    en_summary = (entry.content_en or en_title).strip()[:400]
    return {
        "title_zh": en_title,
        "summary_en": en_summary,
        "summary_zh": en_summary,
    }


def _read_config(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not row:
        return default
    return row.value or default


def _get_ai_runtime_config(db: Session) -> dict:
    return {
        "ai_enabled": _read_config(db, "ai_enabled", str(settings.ai_enabled)).lower() in ("1", "true", "yes"),
        "ai_api_key": _read_config(db, "ai_api_key", settings.ai_api_key),
        "ai_base_url": _read_config(db, "ai_base_url", settings.ai_base_url),
        "ai_model": _read_config(db, "ai_model", settings.ai_model),
        "ai_timeout_seconds": int(_read_config(db, "ai_timeout_seconds", str(settings.ai_timeout_seconds))),
    }


def _call_ai(entry: FeedEntry, cfg: dict) -> dict:
    base_url = cfg["ai_base_url"].rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": cfg["ai_model"],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You summarize RSS content. Return strict JSON with keys: title_zh, summary_en, summary_zh.",
            },
            {
                "role": "user",
                "content": (
                    "Input article:\n"
                    f"English title: {entry.title_en or entry.title}\n"
                    f"English snippet: {entry.content_en[:2000]}\n\n"
                    "Requirements:\n"
                    "1) Keep original English title separately.\n"
                    "2) Generate Chinese translated title as title_zh.\n"
                    "3) Generate concise English summary with 2-4 bullet-like sentences in summary_en.\n"
                    "4) Generate Chinese summary in summary_zh aligned to summary_en.\n"
                    "5) Output valid JSON only."
                ),
            },
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {cfg['ai_api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=cfg["ai_timeout_seconds"]) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return {
        "title_zh": (parsed.get("title_zh") or "").strip(),
        "summary_en": (parsed.get("summary_en") or "").strip(),
        "summary_zh": (parsed.get("summary_zh") or "").strip(),
    }


def enrich_entry_bilingual(db: Session, entry: FeedEntry) -> None:
    cfg = _get_ai_runtime_config(db)

    if not cfg["ai_enabled"]:
        result = _fallback_bilingual(entry)
        entry.title_zh = result["title_zh"]
        entry.summary_en = result["summary_en"]
        entry.summary_zh = result["summary_zh"]
        entry.ai_status = "success"
        entry.ai_error = ""
        entry.ai_updated_at = datetime.now(timezone.utc)
        return

    if not cfg["ai_api_key"]:
        result = _fallback_bilingual(entry)
        entry.title_zh = result["title_zh"]
        entry.summary_en = result["summary_en"]
        entry.summary_zh = result["summary_zh"]
        entry.ai_status = "success"
        entry.ai_error = "ai_api_key not set; fallback used"
        entry.ai_updated_at = datetime.now(timezone.utc)
        return

    try:
        result = _call_ai(entry, cfg)
        entry.title_zh = result["title_zh"] or entry.title_en or entry.title
        entry.summary_en = result["summary_en"] or (entry.content_en or "")[:400]
        entry.summary_zh = result["summary_zh"] or entry.summary_en
        entry.ai_status = "success"
        entry.ai_error = ""
    except (URLError, KeyError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        fallback = _fallback_bilingual(entry)
        entry.title_zh = fallback["title_zh"]
        entry.summary_en = fallback["summary_en"]
        entry.summary_zh = fallback["summary_zh"]
        entry.ai_status = "failed"
        entry.ai_error = str(exc)[:500]
    finally:
        entry.ai_updated_at = datetime.now(timezone.utc)
