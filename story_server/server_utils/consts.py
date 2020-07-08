import sys
import os

SECRET_KEY = os.urandom(24)
TABLES_COLUMNS = {
    "TIMELINE_IDS": ["name", "id", "url", "create_time", "create_user"],
    "EVENTS_DESIGN": [
        "event_id",
        "text_color",
        "background_color",
        "frame_color",
        "icon_color",
        "icon",
    ],
    "USERS": ["username", "password"],
    "EVENTS": [
        "timeline_id",
        "event_id",
        "header",
        "text",
        "link",
        "event_time",
        "frame_color",
        "icon",
        "insertion_time",
        "create_user",
    ],
    "CONNECTIONS": ["user", "connection_time"],
    "PERMISSIONS": ["timeline_id", "timeline_url", "username", "role", "insertion_time"]
}


TABLES_NAMES = {
    "TIMELINE_IDS": "timeline_ids",
    "EVENTS_DESIGN": "events_design",
    "USERS": "users",
    "EVENTS": "events",
    "CONNECTIONS": "connections",
    "PERMISSIONS": "permissions"
}

RESERVED_TIMELINE_NAMES = ["add", "delete", "del", ".", "?", "/"]

SMALL_ABC = [chr(i) for i in range(ord("a"), ord("z") + 1)]
CAPITAL_ABC = [chr(i) for i in range(ord("A"), ord("Z") + 1)]
NUMS = [str(i) for i in range(0, 10)]

ALLOWED_CHARS = SMALL_ABC + CAPITAL_ABC + NUMS + ["_", "-", "(", ")"]

DB_PATH = r"C:\Scripts\Story\server\sqlite_db\timeline.db"

SYSTEM_NAME = "STORY"
if sys.platform.startswith("win"):
    XLSX_FOLDER = r"C:\Scripts\Story\xlsx_tmp"
else:
    XLSX_FOLDER = r'/mnt/data/xlsx_tmp'
