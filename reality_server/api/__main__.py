import uuid
import json
import os
import pandas as pd
from flask import make_response, abort, send_file
from datetime import datetime
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    DB_PATH,
    ALLOWED_CHARS,
    SYSTEM_NAME,
    XLSX_FOLDER
)
from ..server_utils.db_functions import query, insert, create_connection, run, query_to_df
from time import sleep

# TODO: consts page with all the things.
# TODO: save the queries not in the python file, in sql files.
# TODO: no special chars in url!
# TODO: context manager for the connect.
# TODO: change to db object. after all.


# ##################################################

def get_timeline_xlsx_file(timeline_url):
    if not _is_url_exists(timeline_url):
        return make_response(
            "URL: {url} Does not exists!".format(url=timeline_url), 201
        )
    clear_pass_files(XLSX_FOLDER, timeline_url)
    xlsx_file_path = _create_timeline_xlsx(timeline_url)
    print(xlsx_file_path)
    xlsx_file_name = os.path.basename(xlsx_file_path)
    print(xlsx_file_name)

    return send_file(xlsx_file_path,
                     attachment_filename=xlsx_file_name,
                     cache_timeout=-1,
                     as_attachment=True
                     )


def _create_timeline_xlsx(timeline_url):
    """
    queries the db and creates timeline xlsx
    returns the fill path of the created file
    :param timeline_url:
    :return:
    """

    events_query = """
    SELECT name, header, text, link, event_time, icon, insertion_time, e.create_user
FROM events_2 e
 INNER JOIN timeline_ids t
 ON (e.timeline_id = t.id)
 WHERE url = ?"""

    timeline_data_query = """
    SELECT name, url, description, create_time, create_user
    FROM timeline_ids
    WHERE url = ?
    """

    timeline_events_df = query_to_df(db_file=DB_PATH, query_string=events_query, args=[timeline_url])
    timeline_data_df = query_to_df(db_file=DB_PATH, query_string=timeline_data_query, args=[timeline_url])
    file_name = "{sys_name}_{timeline_name}@{time}.xlsx".format(sys_name=SYSTEM_NAME,
                                                               timeline_name=timeline_url,
                                                               time=datetime.today().strftime('%Y%m%d-%H%M%S'))
    xlsx_path = os.path.join(XLSX_FOLDER, file_name)

    writer = pd.ExcelWriter(xlsx_path, engine='xlsxwriter')
    timeline_events_df.to_excel(writer, sheet_name=f'{timeline_url}_events',index=False)
    timeline_data_df.to_excel(writer, sheet_name='Timeline_Data', index=False)

    writer.save()
    return xlsx_path


def clear_pass_files(folder, timeline_url):
    """
    clear pass xlsx files that was created by the system.
    :param folder:
    :param timeline_url:
    :return:
    """
    file_name = "{sys_name}_{timeline_name}@".format(sys_name=SYSTEM_NAME,
                                                     timeline_name=timeline_url,
                                                     )
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.startswith(file_name):
                os.remove(os.path.join(root, f))


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
    if results is None:
        return make_response(
            "Query Error!", 500
        )
    else:
        return results


def get_timeline(timeline_url):
    """
    returns all the events data of a timeline
    each event data is a json.dumps
    :param timeline_url:
    :return:
    """
    # sleep(2)
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "URL '{url}' does not exists!".format(url=timeline_url), 404
        )

    get_timeline_query = """
    SELECT *
      FROM events_2
	 WHERE timeline_id = ?
     ORDER BY event_time DESC """
    results = query(
        db_file=DB_PATH, query_string=get_timeline_query, args=[timeline_id]
    )
    if results is None:
        return make_response(
            "Query Error!", 500
        )
    else:
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
            "URL '{url}' does not exists!".format(url=timeline_url), 201
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
            "Requested URL: {url} already exists!".format(url=url), 201
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
