import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

# ---- Mongo Setup ----
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# Indian timezone (UTC+5:30)
INDIAN_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def convert_to_indian_time(utc_datetime):
    """Convert UTC datetime to Indian timezone"""
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    return utc_datetime.astimezone(INDIAN_TIMEZONE)


def parse_github_timestamp(raw_timestamp: str) -> datetime:
   
    if not raw_timestamp:
        raise ValueError("Missing timestamp")

    ts = raw_timestamp.strip()

    # Normalize trailing 'Z' (Zulu / UTC) to an explicit +00:00 offset
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"

    dt = datetime.fromisoformat(ts)

    # Ensure we are always working in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt


# ---- Business Logic ----
def process_event(event_type, payload):

    if event_type == "push":

        author = payload["pusher"]["name"]
        to_branch = payload["ref"].split("/")[-1]
        raw_timestamp = payload["head_commit"]["timestamp"]

        document = {
            "event_type": "push",
            "author": author,
            "from_branch": None,
            "to_branch": to_branch,
            "timestamp": parse_github_timestamp(raw_timestamp),
        }

        collection.insert_one(document)

    elif event_type == "pull_request":

        action = payload.get("action")
        pr = payload["pull_request"]

        author = pr["user"]["login"]
        from_branch = pr["head"]["ref"]
        to_branch = pr["base"]["ref"]

        if action == "opened":
            raw_timestamp = pr["created_at"]

            document = {
                "event_type": "pull_request",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": parse_github_timestamp(raw_timestamp),
            }

            collection.insert_one(document)

        elif action == "closed" and pr["merged"]:
            raw_timestamp = pr["merged_at"]

            document = {
                "event_type": "merge",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": parse_github_timestamp(raw_timestamp),
            }

            collection.insert_one(document)


def get_events(minutes=None):
    try:
        minutes_value = int(minutes) if minutes is not None else 15
    except (TypeError, ValueError):
        minutes_value = 15

    if minutes_value <= 0:
        minutes_value = 15

    cutoff_utc = datetime.now(timezone.utc) - timedelta(minutes=minutes_value)

    documents = collection.find({"timestamp": {"$gte": cutoff_utc}}).sort(
        "timestamp", -1
    )

    result = []

    for doc in documents:
        if doc["event_type"] == "push":
            message = f'{doc["author"]} pushed to {doc["to_branch"] }'
        elif doc["event_type"] == "merge":
            message = f'{doc["author"]} merged branch {doc["from_branch"]} to {doc["to_branch"]  }'
        elif doc["event_type"] == "pull_request":
            message = f'{doc["author"]} opened pull request from {doc["from_branch"]} to {doc["to_branch"]}'
        else:
            continue

        result.append(
            {
                "event_type": doc["event_type"],
                "message": message,
                "timestamp": convert_to_indian_time(doc["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )

    return result