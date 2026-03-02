from flask import request, jsonify, render_template
from services import process_event, get_events
import json


def register_routes(app):

    @app.route("/")
    def home():
        return "hii"

    @app.route("/webhook", methods=["POST"])
    def webhook():
        event_type = request.headers.get("X-GitHub-Event")
        payload = request.json
        event_type = request.headers.get("X-GitHub-Event")
        payload = request.json
        process_event(event_type, payload)

        return jsonify({"status": "received"}), 200
    

    
        # print("Event Type:", event_type)
        # print("Payload:")
        # print(json.dumps(payload, indent=2))
        # process_event(event_type, payload)

            
    # polling api 
    @app.route("/events", methods=["GET"])
    def get_event():
        return jsonify(get_events())
    
    
    @app.route("/dashboard")    
    def dashboard():
        return render_template("dashboard.html")
    
    