import sqlite3
import uuid
import json
from flask import make_response, abort
from datetime import datetime


DB_PATH = r"C:\Scripts\Reality\sqlite_db\timeline.db"

# TODO: move db functions to db_utils
# TODO: consts page with all the things.
# TODO: save the queries not in the python file, in sql files.
# TODO: package- reality. write setup.py
# TODO: context manager for the connect.
# TODO: change to db object. after all.

# ###############################################################
# ############                CONSTS                #############
# ###############################################################



TABLES_COLUMNS = {
    "TIMELINE_IDS": ["name", "id", "url", "create_time", "create_user"],
    "EVENTS": ['timeline_id', 'event_id', 'event_data', 'event_time', 'insertion_time', 'create_user'],
    "USERS": ["username", "password"]
    }


TABLES_NAMES = {
    "TIMELINE_IDS": "timeline_ids",
    "EVENTS": "events",
    "USERS": "users",
}

RESERVED_TIMELINE_NAMES = ["add", 'delete', 'del', '.', '?']


# ##################################################
#checked
def login(username, password):
    """
    checks if the username and password matches and can connect to system.
    returns 200 if success and 404 if not (no permissions or wrong password)
    :param username: string
    :param password: string
    :return:
    """
    con = create_connection(DB_PATH)
    users_query = """
    SELECT *
    FROM users 
    where username= ? """
    results = query(con, users_query, [username])
    if len(results) == 0:
        return make_response(
            "{user} has no permissions".format(user=username), 404
        )
    else:
        if results[0][1] != password:
            return make_response(
                "Wrong Password!".format(user=username), 404
            )
        else:
            return make_response(
            "{user} logged in successfully".format(user=username), 200

        )


#checked
def get_all_names():
    """
    returns all the data from the timeline_ids table, for the main cards view.
    :return: 
    """
    con = create_connection(DB_PATH)
    timelines_query = """
    SELECT *
      FROM timeline_ids
    """
    results = query(con, timelines_query)
    return results


#checked
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
    results = query(db_file=DB_PATH,
                    query_string=get_timeline_query,
                    args=[timeline_id])
    events = []
    for res in results:
        events.append(json.loads(res['event_data']))
    return events


#checked
def add_event(timeline_url, new_event):  # things!
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
    new_event.pop('user', None)
    text_event_data = json.dumps(new_event)

    insert(DB_PATH,
           table=TABLES_NAMES["EVENTS"],
           columns=TABLES_COLUMNS["EVENTS"],
           data=[timeline_id, event_id, text_event_data, event_time, insertion_time, create_user]
           )
    return make_response(
        f"added new record to '{timeline_url}'!", 200
    )
    # print(timeline_url)
    # print(new_event)
    # print(type(new_event))


#checked
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
        return make_response(
            "illegal url! Please select another", 404
        )
    create_time = get_timestamp()
    # uniq id:
    timeline_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, url))
    # insert record
    insert(DB_PATH,
           table=TABLES_NAMES["TIMELINE_IDS"],
           columns=TABLES_COLUMNS["TIMELINE_IDS"],
           data=[name, timeline_id, url, create_time, create_user]
           )
    return make_response(
        f"new Timeline '{name}' created!", 200
    )

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
        return results[0]['id']
    else:
        return None


# ##############################################
# #########        DB FUNCTIONS        #########
# ##############################################

# change to context manager.
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn


def run(db_file, query, keep_open=False):
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query)
    except Exception as e:
        print(e)
    finally:
        if not keep_open:
            connection.close()


def insert(db_file, table, columns, data, keep_open=False):
    insertion_query = """ 
    INSERT INTO {table_name}({columns})
    VALUES({data})
    """
    lined_columns = ','.join([str(val) for val in columns])
    lined_data = ','.join(["?" for val in columns])
    query = insertion_query.format(table_name=table,
                                   columns=lined_columns,
                                   data=lined_data)
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query, data)
        connection.commit()
    except Exception as e:
        print(f"Tried to run:\n {query}")
        print(f"Error: {e}")
    finally:
        if not keep_open:
            connection.close()


# maybe change to 2 functions: one returns data and and headers and one changes to dicts.
def query(db_file, query_string, args=[], keep_open=False):
    """
    query the data from the db.
    returns a list of dicts.
    :param db_file:
    :param query_string:
    :param args:
    :param keep_open: dont close the connection to db.
    :return:
    """
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query_string, args)
        headers = [description[0] for description in c.description]
        raw_results = c.fetchall()
        results = []
        for record in raw_results:
            dict_record = {}
            for i in range(len(headers)):
                dict_record[headers[i]] = record[i]
            results.append(dict_record)
        return results
    except Exception as e:
        print(e)
    finally:
        if not keep_open:
            connection.close()
