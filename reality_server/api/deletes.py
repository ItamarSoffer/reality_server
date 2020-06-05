from flask import make_response
from .__main__ import APP_DB
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    ALLOWED_CHARS,

)
from ..server_utils.time_functions import get_timestamp
from .users_functions import check_permissions


def delete_timeline(timeline_id, username):
    pass


def delete_event(event_id, username):
    role = _check_permission_by_event(event_id, username)
    print(role)

    if not role:
        print(1)
        return make_response("User has no permissions or wrong event ID", 201)

    role = role[0][0]
    if role == 'read':
        print(2)
        return make_response("User doesnt have permissions to delete events!", 201)
    elif role in ['owner', 'write']:
        print(3)
        print(3)
        delete_query = """
        DELETE
        FROM events
        WHERE event_id = ?"""
        APP_DB.run(delete_query, [event_id])
        return make_response("Event deleted successfully", 200)


def _check_permission_by_event(event_id, username):
    query = """
    SELECT DISTINCT role
  FROM permissions p 
  INNER JOIN events e
   ON p.timeline_id = e.timeline_id 
   WHERE username =? and event_id = ?"""
    return APP_DB.query(query, [username, event_id], return_headers=False)


def _get_timeline_by_event(event_id):
    query = """SELECT timeline_id
    from events
    WHERE event_id = ?
    """
    return APP_DB.query(query, [event_id])[0]