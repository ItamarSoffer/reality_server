import uuid
import json
from flask import make_response, abort
from datetime import datetime
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    DB_PATH,
    ALLOWED_CHARS
)
from ..server_utils.db_functions import query, insert, create_connection, run
from time import sleep

# TODO: consts page with all the things.
# TODO: save the queries not in the python file, in sql files.
# TODO: no special chars in url!
# TODO: context manager for the connect.
# TODO: change to db object. after all.


# ##################################################


def login(username, password):
    """
    checks if the username and password matches and can connect to system.
    returns 200 if success and 404 if not (no permissions or wrong password)
    in the UNIT, this will change to the LDAP authentication.
    :param username: string
    :param password: string
    :return:
    """
    users_query = """
    SELECT *
    FROM users 
    where username= ? """
    results = query(DB_PATH, users_query, [username])
    if len(results) == 0:
        return make_response("{user} has no permissions".format(user=username), 404)
    else:
        if results[0]["password"] != password:
            return make_response("Wrong Password!".format(user=username), 404)
        else:
            return make_response(
                "{user} logged in successfully".format(user=username), 200
            )


def get_all_names(num=None):
    """
    returns all the data from the timeline_ids table, for the main cards view.
    :return: 
    """

    timelines_query = """
    SELECT *
      FROM timeline_ids
      ORDER BY create_time DESC
    """
    if num is None:
        results = query(DB_PATH, timelines_query)
    else:
        timelines_query += ' LIMIT ?'
        results = query(DB_PATH, timelines_query, [num])
    return results


def get_timeline(timeline_url):
    """
    returns all the events data of a timeline
    each event data is a json.dumps
    :param timeline_url:
    :return:
    """
    sleep(2)
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "url '{url}' does not exists!".format(url=timeline_url), 404
        )

    get_timeline_query = """
    SELECT *
      FROM events_2
	 WHERE timeline_id = ?
     ORDER BY event_time DESC """
    results = query(
        db_file=DB_PATH, query_string=get_timeline_query, args=[timeline_id]
    )
    return {"events": results}


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
            "url '{url}' does not exists!".format(url=timeline_url), 201
        )
    event_id = str(uuid.uuid4())

    _add_event_data(timeline_id=timeline_id,
                    event_id=event_id,
                    new_event=new_event)

    return make_response(f"added new record to '{timeline_url}'!", 200)


def _add_event_data(timeline_id, event_id, new_event):
    """
    gets the timeline_id, event_id and the new event data.
    inserts the data of the new event to EVENTS_2 table
    :param timeline_id:
    :param event_id:
    :param new_event:
    :return:
    """
    header = new_event.get("header")
    text = new_event.get("text")
    link = new_event.get("link", None)
    event_time = f'{new_event.get("date")} {new_event.get("hour", "")}'
    frame_color = new_event.get("frame_color", 'rgb(33, 150, 243)')
    icon = new_event.get("icon", "")
    insertion_time = get_timestamp()
    create_user = new_event.get("user")

    insert(
        DB_PATH,
        table=TABLES_NAMES["EVENTS_2"],
        columns=TABLES_COLUMNS["EVENTS_2"],
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
            "Requested url: {url} already exists!".format(url=url), 201
        )
    elif not _check_allowed_chars(url, ALLOWED_CHARS):
        return make_response(
            "The name has invalid characters." +
            " Enter letters, numbers, hyphens or brackets.", 201
        )
    elif url.lower() in RESERVED_TIMELINE_NAMES:
        return make_response("Illegal url! Please select another", 201)
    create_time = get_timestamp()
    # uniq id:
    timeline_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, url))
    # insert record
    # insert(
    #     DB_PATH,
    #     table=TABLES_NAMES["TIMELINE_IDS"],
    #     columns=TABLES_COLUMNS["TIMELINE_IDS"],
    #     data=[name, timeline_id, url, create_time, create_user],
    # )
    return make_response(f"new Timeline '{name}' created!", 200)


# ##############################################
# #########           UTILS            #########
# ##############################################

def _check_allowed_chars(string, allowed_chars):
    """
    checks if all chars in string are in allowed_chars list
    :param string: string to check
    :param allowed_chars: list of allowed chars
    :return: bool
    """
    is_cleared = [c in allowed_chars for c in string]
    return all(is_cleared)


def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def _is_url_exists(url):
    """
    Checks if the url already exists.
    :param url:
    :return: True if the url exists, false if not.
    """
    url_query_check = """
    SELECT id
    FROM timeline_ids
    WHERE url = ? """

    return query(DB_PATH, url_query_check, [url])


def _get_id_by_url(url):
    q = """
    SELECT id 
    FROM timeline_ids
    WHERE url = ?
    """
    results = query(DB_PATH, q, [url])
    if results:
        return results[0]["id"]
    else:
        return None
