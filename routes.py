from flask import request, jsonify
from services import process_event

def register_routes(app):

    @app.route("/")
    def home():
        return "hii"

    @app.route("/webhook", methods=["POST"])
    def webhook():
        event_type = request.headers.get("X-GitHub-Event")
        payload = request.json

        process_event(event_type, payload)

        return jsonify({"status": "received"}), 200