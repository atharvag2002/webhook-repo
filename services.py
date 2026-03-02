import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ---- Mongo Setup ----
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]


# ---- Business Logic ----
def process_event(event_type, payload):

    if event_type == "push":

        author = payload["pusher"]["name"]
        to_branch = payload["ref"].split("/")[-1]
        timestamp = payload["head_commit"]["timestamp"]

        document = {
            "event_type": "push",
            "author": author,
            "from_branch": None,
            "to_branch": to_branch,
            "timestamp": datetime.fromisoformat(timestamp)
        }

        collection.insert_one(document)

    elif event_type == "pull_request":

        action = payload.get("action")

        # Brownie point: merge detection
        if action == "closed" and payload["pull_request"]["merged"]:

            author = payload["pull_request"]["user"]["login"]
            from_branch = payload["pull_request"]["head"]["ref"]
            to_branch = payload["pull_request"]["base"]["ref"]
            timestamp = payload["pull_request"]["merged_at"]

            document = {
                "event_type": "merge",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": datetime.fromisoformat(timestamp)
            }

            collection.insert_one(document)

def get_events():
    documents = collection.find().sort("timestamp", -1)

    result = []

    for doc in documents:
        if doc["event_type"] == "push":
            message = f'{doc["author"]} pushed to {doc["to_branch"]} on {doc["timestamp"]}'
        elif doc["event_type"] == "merge":
            message = f'{doc["author"]} merged branch {doc["from_branch"]} to {doc["to_branch"]} on {doc["timestamp"]}'
        else:
            continue

        result.append(message)

    return result