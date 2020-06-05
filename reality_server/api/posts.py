import uuid
from flask import make_response
from .__main__ import APP_DB
from .gets import _get_id_by_url, _is_url_exists
from ..server_utils.time_functions import get_timestamp
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    ALLOWED_CHARS,
)
from .users_functions import _add_permissions


def create_timeline(new_timeline):
    """
    creates a new timeline.
    makes sure that the url is not already taken
    :param new_timeline:
    :return:
    """
    name = new_timeline.get("name", None)
    url = new_timeline.get("url", None)
    create_user = new_timeline.get("create_user", None)
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
        data=[name, timeline_id, url, create_time, create_user],
    )
    _add_permissions(timeline_url=url,
                     username=create_user,
                     role="owner")
    return make_response(f"new Timeline '{name}' created!", 200)


def add_event(timeline_url, new_event):
    """
    adds new event to timeline.
    :param timeline_url: the url of the timeline to add to.
    :param new_event: a dict with the params of the event. it contains:
        - header
        - text
        - date
        - user

        Additional that can be input:
        - link
        - text_color
        - background_color
        - frame_color
        - icon
    in the yml it is defined what must be.


    :return:
    """
    # TODO: check the inputs that is valid.
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "URL '{url}' does not exists!".format(url=timeline_url), 201
        )
    event_id = str(uuid.uuid4())

    _add_event_data(timeline_id=timeline_id, event_id=event_id, new_event=new_event)

    return make_response(f"added new record to '{timeline_url}'!", 200)


def _add_event_data(timeline_id, event_id, new_event):
    """
    gets the timeline_id, event_id and the new event data.
    inserts the data of the new event to EVENTS table
    :param timeline_id:
    :param event_id:
    :param new_event:
    :return:
    """
    header = new_event.get("header")
    text = new_event.get("text")
    link = new_event.get("link", None)
    event_time = f'{new_event.get("date")} {new_event.get("hour", "")}'
    frame_color = new_event.get("frame_color", "rgb(33, 150, 243)")
    icon = new_event.get("icon", "")
    insertion_time = get_timestamp()
    create_user = new_event.get("user")

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


def _check_allowed_chars(string, allowed_chars):
    """
    checks if all chars in string are in allowed_chars list
    :param string: string to check
    :param allowed_chars: list of allowed chars
    :return: bool
    """
    is_cleared = [c in allowed_chars for c in string]
    return all(is_cleared)
