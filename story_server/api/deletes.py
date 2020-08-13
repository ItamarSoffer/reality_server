from .__main__ import MODE

if MODE == "SQLITE":
    from .sqlite_db.story import delete_timeline
    from .sqlite_db.event import delete_event
    # from .sqlite_db.deletes import _check_permission_by_event
    # from .sqlite_db.deletes import _check_permission_by_timeline_id
