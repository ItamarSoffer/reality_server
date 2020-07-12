from flask import make_response
from ..__main__ import APP_DB
from ..jwt_functions import check_jwt, decrypt_auth_token, _search_in_sub_dicts
from .users_functions import PERMISSION_POWER

@check_jwt
def delete_timeline(timeline_id, **kargs):
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)

    role = _check_permission_by_timeline_id(timeline_id, username)
    if not role:
        return make_response("User has no permissions or wrong timeline ID", 201)

    role = role[0][0]
    if PERMISSION_POWER[role] < PERMISSION_POWER['owner']:
        return make_response("User doesnt have permissions to delete timeline!", 201)
    else:
        delete_events_query = """
            DELETE
            FROM events
            WHERE timeline_id = ?"""
        APP_DB.run(delete_events_query, [timeline_id])
        delete_timeline_query = """
            DELETE
            FROM timeline_ids
            WHERE id = ?"""
        APP_DB.run(delete_timeline_query, [timeline_id])
        delete_permissions_query = """
                    DELETE
                    FROM permissions
                    WHERE timeline_id = ?"""
        APP_DB.run(delete_permissions_query, [timeline_id])

        return make_response("Timeline and its events deleted successfully", 200)


@check_jwt
def delete_event(event_id, **kargs):
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)

    role = _check_permission_by_event(event_id, username)
    if not role:
        return make_response("User has no permissions or wrong event ID", 201)

    role = role[0][0]
    if PERMISSION_POWER[role] < PERMISSION_POWER['write']:
        return make_response("User doesnt have permissions to delete events!", 201)
    else:
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


def _check_permission_by_timeline_id(event_id, username):
    query = """
      SELECT role
    FROM permissions p  
     WHERE username =? and timeline_id = ?"""
    return APP_DB.query(query, [username, event_id], return_headers=False)