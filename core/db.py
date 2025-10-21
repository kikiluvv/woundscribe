import json
import os
import datetime

DB_PATH = "data/patient_map.json"

def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def get_clinic(db, name):
    if name not in db:
        db[name] = {
            "clinic": "UnknownClinic",
            "last_updated": datetime.date.today().isoformat()
        }
    return db[name]["clinic"]
