import uuid
import json
from flask import make_response, abort
from datetime import datetime
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    DB_PATH,
)
from ..server_utils.db_functions import query, insert, create_connection, run


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


def get_all_names():
    """
    returns all the data from the timeline_ids table, for the main cards view.
    :return: 
    """
    timelines_query = """
    SELECT *
      FROM timeline_ids
    """
    results = query(DB_PATH, timelines_query)
    return results


def get_timeline(timeline_url):
    """
    returns all the events data of a timeline
    each event data is a json.dumps
    :param timeline_url:
    :return:
    """
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "url '{url}' does not exists!".format(url=timeline_url), 404
        )

    get_timeline_query = """
    SELECT event_data 
      FROM events
     WHERE timeline_id = ? 
     ORDER BY event_time DESC """
    results = query(
        db_file=DB_PATH, query_string=get_timeline_query, args=[timeline_id]
    )
    events = []
    for res in results:
        events.append(json.loads(res["event_data"]))
    return {"events": events}


def add_event(timeline_url, new_event):
    """
    adds new event to timeline.
    :param timeline_url: the url of the timeline to add to.
    :param new_event: a dict with the params of the event. it contains:
        - main header
        - date
        - user
        - text
        - icon
        - can get more data.
    in the yml it is defined what must be.


    :return:
    """
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "url '{url}' does not exists!".format(url=timeline_url), 404
        )
    create_user = new_event.get("user")
    event_time = new_event.get("date")
    event_id = str(uuid.uuid4())
    insertion_time = get_timestamp()
    new_event.pop("user", None)
    text_event_data = json.dumps(new_event)

    insert(
        DB_PATH,
        table=TABLES_NAMES["EVENTS"],
        columns=TABLES_COLUMNS["EVENTS"],
        data=[
            timeline_id,
            event_id,
            text_event_data,
            event_time,
            insertion_time,
            create_user,
        ],
    )
    return make_response(f"added new record to '{timeline_url}'!", 200)
    # print(timeline_url)
    # print(new_event)
    # print(type(new_event))


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
            "requested url: {url} already exists!".format(url=url), 404
        )
    if url.lower() in RESERVED_TIMELINE_NAMES:
        return make_response("illegal url! Please select another", 404)
    create_time = get_timestamp()
    # uniq id:
    timeline_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, url))
    # insert record
    insert(
        DB_PATH,
        table=TABLES_NAMES["TIMELINE_IDS"],
        columns=TABLES_COLUMNS["TIMELINE_IDS"],
        data=[name, timeline_id, url, create_time, create_user],
    )
    return make_response(f"new Timeline '{name}' created!", 200)


# ##############################################
# #########           UTILS            #########
# ##############################################


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
