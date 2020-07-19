import uuid
from flask import make_response
from ..__main__ import APP_DB
from .gets import _get_id_by_url, _is_url_exists, _add_tags, _is_tag_exists
from ...server_utils.time_functions import get_timestamp
from ...server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    ALLOWED_CHARS,
)
from .users_functions import _add_permissions, _check_permissions, PERMISSION_POWER
from ..jwt_functions import check_jwt, decrypt_auth_token, _search_in_sub_dicts


@check_jwt
def create_timeline(new_timeline, **kargs):
    """
    creates a new timeline.
    makes sure that the url is not already taken
    :param new_timeline:
    :return:
    """
    name = new_timeline.get("name", None)
    url = new_timeline.get("url", None)
    description = new_timeline.get("description", None)

    jwt_token = _search_in_sub_dicts(new_timeline, "jwt_token")
    create_user = decrypt_auth_token(jwt_token)
    if _is_url_exists(url):
        return make_response(
            "Requested URL: {url} already exists!".format(url=url), 201
        )
    elif not _check_allowed_chars(url, ALLOWED_CHARS):
        return make_response(
            "The name has invalid characters."
            + " Enter letters, numbers, hyphens or brackets.",
            201,
        )
    elif url.lower() in RESERVED_TIMELINE_NAMES:
        return make_response("Illegal url! Please select another", 201)
    create_time = get_timestamp()
    # uniq id:
    timeline_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, url))
    # insert record
    APP_DB.insert(
        table=TABLES_NAMES["TIMELINE_IDS"],
        columns=TABLES_COLUMNS["TIMELINE_IDS"],
        data=[name, timeline_id, url, description, create_time, create_user],
    )
    _add_permissions(timeline_url=url,
                     username=create_user,
                     role="creator")
    return make_response("new Timeline '{name}' created!".format(name=name), 200)


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
        return _update_event(timeline_id, event_id, new_event)


def _update_event(timeline_id, event_id, new_event):
    _update_event_data(event_id, new_event)
    _update_event_tags(timeline_id, event_id, event_data=new_event)
    return make_response("Event has been updated", 200)


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
    update_query = """
    UPDATE events
    SET 
    header = ?,
    text = ?,
    link = ?,
    event_time = ?,
    frame_color = ?,
    icon = ?, 
    create_user = ?
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
    _add_tags(story_id, event_id, tags)


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
    _add_tags(timeline_id, event_id, tags)
    return make_response("added new record to '{timeline_url}'!".format(timeline_url=timeline_url), 200)


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
    icon = new_event.get("icon", "")
    insertion_time = get_timestamp()
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
        ],
    )
    print("inserted data")


@check_jwt
def add_tag(timeline_url, **kargs):
    # check the user permissions
    story_id = _get_id_by_url(timeline_url)
    tag_name = _search_in_sub_dicts(kargs, "tag_name")
    if _is_tag_exists(story_id, tag_name):
        return make_response("Tag exists", 201)
    tag_color = _search_in_sub_dicts(kargs, "tag_color")
    tag_id = str(uuid.uuid4())
    if ',' in tag_name:
        return make_response("No comma in tags.", 201)

    # "STORY_TAGS": ['story_id', 'tag_id', 'tag_name', 'tag_color', 'create_time'],
    APP_DB.insert(table=TABLES_NAMES["STORY_TAGS"],
                  columns=TABLES_COLUMNS["STORY_TAGS"],
                  data=[story_id,
                        tag_id,
                        tag_name,
                        tag_color,
                        get_timestamp()
                        ])
    return make_response("created new tag", 200)


def _check_allowed_chars(string, allowed_chars):
    """
    checks if all chars in string are in allowed_chars list
    :param string: string to check
    :param allowed_chars: list of allowed chars
    :return: bool
    """
    is_cleared = [c in allowed_chars for c in string]
    return all(is_cleared)
