from flask import Blueprint, jsonify, request

from backend.ai_engine import generate_answer
from backend.cache import get_cached_response, set_cached_response
from backend.rate_limit import is_rate_limited


api_blueprint = Blueprint("api", __name__)


FALLBACK_REPLY = (
    "Atsiprašome, šiuo metu nepavyko gauti atsakymo. "
    "Pabandykite dar kartą po kelių minučių arba pasinaudokite SMK svetainėje pateikta informacija."
)

FALLBACK_LINKS = [
    {
        "label": "SMK svetainė",
        "url": "https://smk.lt/",
    },
    {
        "label": "Kontaktai",
        "url": "https://smk.lt/kontaktai/",
    },
]


@api_blueprint.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Backend serveris veikia."
    })


@api_blueprint.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "reply": "Įrašykite klausimą, ir pabandysiu padėti.",
            "links": []
        })

    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({
            "reply": "Įrašykite klausimą, ir pabandysiu padėti.",
            "links": []
        })

    client_id = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr or "anonymous"
    )

    cached = get_cached_response(client_id, message)

    if cached is not None:
        return jsonify(cached)

    if is_rate_limited(client_id):
        return jsonify({
            "reply": (
                "Per trumpą laiką išsiųsta per daug užklausų. "
                "Pabandykite dar kartą po minutės."
            ),
            "links": []
        })

    try:
        result = generate_answer(message, history)

        if not result or "reply" not in result:
            result = {
                "reply": FALLBACK_REPLY,
                "links": FALLBACK_LINKS,
            }

        set_cached_response(client_id, message, result)

        return jsonify(result)

    except Exception as error:
        print("[CHAT ERROR]", repr(error))

        return jsonify({
            "reply": FALLBACK_REPLY,
            "links": FALLBACK_LINKS,
        })