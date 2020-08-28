import uuid
from flask import make_response
from ..__main__ import APP_DB
from ...server_utils.time_functions import get_timestamp
from ...server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
)
from .users_functions import _check_permissions, PERMISSION_POWER
from ..jwt_functions import check_jwt, decrypt_auth_token, _search_in_sub_dicts
from .utils import _get_id_by_url
from .tags import _get_tag_by_story, _add_tags, get_tags_by_event
from .story import _fetch_extra_data


@check_jwt
def add_event(timeline_url, new_event, **kargs):
    """
    adds and updates new event to timeline.
    :param timeline_url: the url of the timeline to add to.
    :param new_event: a dict with the params of the event. it contains:
        - header
        - text
        - date

        Additional that can be input:
        - link
        - text_color
        - background_color
        - frame_color
        - icon
    in the yml it is defined what must be.


    :return:
    """
    timeline_id = _get_id_by_url(url=timeline_url)
    jwt_token = _search_in_sub_dicts(new_event, "jwt_token")
    user = decrypt_auth_token(jwt_token)
    if timeline_id is None:
        return make_response(
            "URL '{url}' does not exists!".format(url=timeline_url), 201
        )
    elif _check_permissions(timeline_url, user, return_level=True) < PERMISSION_POWER['write']:
        return make_response(
            "User {user} has no write permissions".format(user=user), 201
        )

    event_id = _search_in_sub_dicts(new_event, "event_id")
    if event_id is None:
        return _create_new_event(timeline_url=timeline_url, new_event=new_event)
    else:
        print("UPDATE MODE")
        return _update_event(timeline_id, event_id, new_event, jwt_token)


def _update_event(timeline_id, event_id, new_event, jwt_token):
    _update_event_data(event_id, new_event)
    _update_event_tags(timeline_id, event_id, event_data=new_event)
    updated_event = _get_single_event(event_id, jwt_token)
    return make_response(
        {"message": "Event has been updated", "eventData": updated_event}, 200)


def _update_event_data(event_id, event_data):
    jwt_token = _search_in_sub_dicts(event_data, "jwt_token")
    create_user = decrypt_auth_token(jwt_token)
    header = event_data.get("header")
    text = event_data.get("text")
    link = event_data.get("link", None)
    event_time = '{date} {hour}'.format(date=event_data.get("date"),
                                        hour=event_data.get("hour", ""))
    frame_color = event_data.get("frame_color", "rgb(33, 150, 243)")
    icon = event_data.get("icon", "")
    modify_time = get_timestamp()
    update_query = """
    UPDATE events
    SET 
    header = ?,
    text = ?,
    link = ?,
    event_time = ?,
    frame_color = ?,
    icon = ?, 
    create_user = ?,
    modify_time = ?
    WHERE event_id =  ?"""
    APP_DB.run(query=update_query,
               args=[
                   header,
                   text,
                   link,
                   event_time,
                   frame_color,
                   icon,
                   create_user,
                   modify_time,
                   event_id
               ])


def _update_event_tags(story_id, event_id, event_data):
    """
    deletes previous tags, updates new.
    :param story_id:
    :param event_id:
    :param event_data:
    :return:
    """
    # delete tags
    # write new
    delete_tags_query = """
    DELETE
    FROM events_tags
    WHERE event_id = ?"""
    APP_DB.run(query=delete_tags_query, args=[event_id])
    tags = event_data.get("tags", [])
    tags_ids = []
    for tag_name in tags:
        tags_ids.append(_get_tag_by_story(story_id, tag_name))
    _add_tags(story_id, event_id, tags_ids)


def _create_new_event(timeline_url, new_event):
    """
    creates the new event and adds it to db
    :param timeline_id:
    :param event_id:
    :param new_event:
    :param jwt_token:
    :return:
    """
    timeline_id = _get_id_by_url(url=timeline_url)
    event_id = str(uuid.uuid4())
    jwt_token = _search_in_sub_dicts(new_event, "jwt_token")
    _add_event_data(timeline_id=timeline_id, event_id=event_id, new_event=new_event, jwt_token=jwt_token)
    tags = _search_in_sub_dicts(new_event, "tags")
    if tags:
        tags_ids = []
        for tag_name in tags:
            tags_ids.append(_get_tag_by_story(timeline_id, tag_name))
        _add_tags(timeline_id, event_id, tags_ids)
    updated_event = _get_single_event(event_id, jwt_token)
    return make_response({
        "message": "added new record to '{timeline_url}'!".format(timeline_url=timeline_url),
        "eventData": updated_event},
        200)


def _add_event_data(timeline_id, event_id, new_event, jwt_token):
    """
    gets the timeline_id, event_id and the new event data.
    inserts the data of the new event to EVENTS table
    :param timeline_id:
    :param event_id:
    :param new_event:
    :param jwt_token:
    :return:
    """
    header = new_event.get("header")
    text = new_event.get("text")
    link = new_event.get("link", None)
    event_time = '{date} {hour}'.format(date=new_event.get("date"),
                                        hour=new_event.get("hour", ""))
    frame_color = new_event.get("frame_color", "rgb(33, 150, 243)")
    if frame_color is None:
        frame_color = "rgb(33, 150, 243)"
    icon = new_event.get("icon", "")
    insertion_time = get_timestamp()
    modify_time = get_timestamp()
    create_user = decrypt_auth_token(jwt_token)
    APP_DB.insert(
        table=TABLES_NAMES["EVENTS"],
        columns=TABLES_COLUMNS["EVENTS"],
        data=[
            timeline_id,
            event_id,
            header,
            text,
            link,
            event_time,
            frame_color,
            icon,
            insertion_time,
            create_user,
            modify_time
        ],
    )
    print("inserted data")


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
        delete_tags_query = """
                DELETE
                FROM events_tags
                WHERE event_id = ?"""
        APP_DB.run(delete_tags_query, [event_id])
        return make_response("Event deleted successfully", 200)


def _check_permission_by_event(event_id, username):
    query = """
    SELECT DISTINCT role
  FROM permissions p 
  INNER JOIN events e
   ON p.timeline_id = e.timeline_id 
   WHERE username =? and event_id = ?"""
    return APP_DB.query(query, [username, event_id], return_headers=False)


def _get_single_event(event_id, jwt_token):
    """
    returns a single event data
    :param event_id:
    :return:
    """
    query = """
    SELECT *
      FROM events
      WHERE event_id = ?
    """
    result = APP_DB.query_to_json(query, args=[event_id])
    username = decrypt_auth_token(jwt_token)
    result = _fetch_extra_data(result, username)
    result = result[0]
    result['tags'] = get_tags_by_event(event_id)
    return result

