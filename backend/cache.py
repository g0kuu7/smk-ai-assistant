import time
from backend.utils import normalize_text

CACHE_TTL_SECONDS = 300  # 5 min
RESPONSE_CACHE = {}


def make_cache_key(client_id: str, message: str) -> str:
    normalized_message = normalize_text(message)
    return f"{client_id}::{normalized_message}"


def get_cached_response(client_id: str, message: str):
    key = make_cache_key(client_id, message)
    item = RESPONSE_CACHE.get(key)

    if not item:
        return None

    created_at = item["created_at"]
    if time.time() - created_at > CACHE_TTL_SECONDS:
        RESPONSE_CACHE.pop(key, None)
        return None

    return item["response"]


def set_cached_response(client_id: str, message: str, response: dict):
    key = make_cache_key(client_id, message)
    RESPONSE_CACHE[key] = {
        "created_at": time.time(),
        "response": response
    }