TABLES_COLUMNS = {
    "TIMELINE_IDS": ["name", "id", "url", "create_time", "create_user"],
    "EVENTS": [
        "timeline_id",
        "event_id",
        "event_data",
        "event_time",
        "insertion_time",
        "create_user",
    ],
    "USERS": ["username", "password"],
}


TABLES_NAMES = {
    "TIMELINE_IDS": "timeline_ids",
    "EVENTS": "events",
    "USERS": "users",
}

RESERVED_TIMELINE_NAMES = ["add", "delete", "del", ".", "?"]

DB_PATH = r"C:\Scripts\Reality\sqlite_db\timeline.db"
