from .__main__ import MODE

if MODE == "SQLITE":
    from .sqlite_db.favorites import add_favorite
    from .sqlite_db.favorites import del_favorite
    from .sqlite_db.favorites import get_favorites
