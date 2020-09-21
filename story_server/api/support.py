from .__main__ import MODE

if MODE == "SQLITE":
    from .sqlite_db.support import contact_support