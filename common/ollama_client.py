import json
import re
import requests
from common.config import OLLAMA_URL, OLLAMA_MODEL, REQUEST_TIMEOUT
from common.logger import get_logger
from common.retry import with_retry

logger = get_logger("ollama_client")

def _clean_json_response(raw: str) -> str:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    cleaned = cleaned.replace("```", "").strip()
    match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    return cleaned

def _call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 8192
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()

    data = response.json()
    raw_text = data.get("response", "").strip()

    if not raw_text:
        done_reason = data.get("done_reason", "unknown")
        thinking_preview = data.get("thinking", "")[:100]
        raise ValueError(
            f"Empty response. done_reason={done_reason} | "
            f"thinking_preview={thinking_preview}"
        )

    return raw_text

def call_ollama_json(prompt: str, label: str = "") -> list | dict:
    def _attempt():
        raw = _call_ollama(prompt)
        cleaned = _clean_json_response(raw)
        return json.loads(cleaned)

    return with_retry(_attempt, label=label or "ollama_json")

def call_ollama_raw(prompt: str, label: str = "") -> str:
    return with_retry(_call_ollama, prompt, label=label or "ollama_raw")
