from flask import request, jsonify, render_template
from services import process_event, get_events
import json
import hmac
import hashlib
import os

GITHUB_SECRET = os.environ.get("GITHUB_SECRET")


def register_routes(app):

    @app.route("/")
    def home():
        return "hii"

    @app.route("/webhook", methods=["POST"])
    def webhook():
        signature = request.headers.get("X-Hub-Signature-256")

        if not signature:
            return jsonify({"error": "Missing signature"}), 403

        # Get raw request body
        payload = request.data

        # Create HMAC
        mac = hmac.new(
            GITHUB_SECRET.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        )

        expected_signature = "sha256=" + mac.hexdigest()

        # Secure compare
        if not hmac.compare_digest(expected_signature, signature):
            return jsonify({"error": "Invalid signature"}), 403

        event_type = request.headers.get("X-GitHub-Event")
        json_payload = request.json

        process_event(event_type, json_payload)

        return jsonify({"status": "received"}), 200

    # polling api 
    @app.route("/events", methods=["GET"])
    def get_event():
        minutes_param = request.args.get("minutes")
        return jsonify(get_events(minutes_param))
    
    
    @app.route("/dashboard")    
    def dashboard():
        return render_template("dashboard.html")