import os
import requests
from flask import Flask, request, abort

app = Flask(__name__)

# --- Config (set these as environment variables, don't hardcode secrets) ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# Optional shared secret: TradingView will send this in the request body/query
# if you add it, so randoms hitting your public URL can't spam your Telegram.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


@app.route("/", methods=["GET"])
def health():
    return "ok", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    if not BOT_TOKEN or not CHAT_ID:
        return "Server not configured: missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID", 500

    raw_body = request.get_data(as_text=True)

    # Optional secret check -- put {"secret": "yourvalue", ...} in your
    # TradingView alert message, or append ?secret=yourvalue to the webhook URL.
    if WEBHOOK_SECRET:
        secret_in_query = request.args.get("secret")
        if secret_in_query != WEBHOOK_SECRET and WEBHOOK_SECRET not in raw_body:
            abort(403)

    message = raw_body.strip() or "(empty alert payload)"

    resp = requests.post(
        TELEGRAM_API_URL,
        json={"chat_id": CHAT_ID, "text": message},
        timeout=10,
    )

    if resp.status_code != 200:
        # Log to stdout so it shows up in your host's logs
        print(f"Telegram send failed: {resp.status_code} {resp.text}")
        return "Telegram send failed", 502

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
