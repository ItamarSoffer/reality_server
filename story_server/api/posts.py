from .__main__ import MODE

if MODE == "SQLITE":
    from .sqlite_db.story import create_timeline
    from .sqlite_db.event import add_event
    # from .sqlite_db.posts import _add_event_data
    # from .sqlite_db.posts import _check_allowed_chars
    from .sqlite_db.tags import add_tag
    from .sqlite_db.tags import del_tag
    # new
    from .sqlite_db.tags import edit_tag
    from .sqlite_db.story import edit_name_description

