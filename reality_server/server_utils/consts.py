TABLES_COLUMNS = {
    "TIMELINE_IDS": ["name", "id", "url", "create_time", "create_user"],
    "EVENTS": [
        "timeline_id",
        "event_id",
        "header",
        "text",
        "link",
        "event_time",
        "insertion_time",
        "create_user",
    ],
    "EVENTS_DESIGN": [
        "event_id",
        "text_color",
        "background_color",
        "frame_color",
        "icon_color",
        "icon"
    ],
    "USERS": ["username", "password"],
}


TABLES_NAMES = {
    "TIMELINE_IDS": "timeline_ids",
    "EVENTS": "events",
    "EVENTS_DESIGN": "events_design",
    "USERS": "users",
}

RESERVED_TIMELINE_NAMES = ["add", "delete", "del", ".", "?", "/"]

SMALL_ABC = [chr(i) for i in range(ord("a"), ord("z") + 1)]
CAPITAL_ABC = [chr(i) for i in range(ord("A"), ord("Z") + 1)]
NUMS = [str(i) for i in range(0, 10)]

ALLOWED_CHARS = SMALL_ABC + CAPITAL_ABC + NUMS + ["_", "-", "(", ")"]

DB_PATH = r"C:\Scripts\Reality\sqlite_db\timeline.db"
