from flask import make_response
from .__main__ import APP_DB
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    ALLOWED_CHARS,

)
from ..server_utils.time_functions import get_timestamp
from .gets import _get_id_by_url


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
    where username = ? AND password = ? """

    results = APP_DB.query_to_json(users_query, [username, password])
    if results is None or len(results) == 0:
        return make_response(
            "{user} has no permissions or wrong password".format(user=username), 201
        )
    else:
        APP_DB.insert(
            table=TABLES_NAMES["CONNECTIONS"],
            columns=TABLES_COLUMNS["CONNECTIONS"],
            data=[username, get_timestamp()])
        return make_response("{user} logged in successfully".format(user=username), 200)


def _add_permissions(timeline_url, username, role):
    timeline_id = _get_id_by_url(timeline_url)
    APP_DB.insert(table=TABLES_NAMES["PERMISSIONS"],
                  columns=TABLES_COLUMNS["PERMISSIONS"],
                  data=[
                      timeline_id,
                      timeline_url,
                      username,
                      role,
                      get_timestamp()
                  ])


def check_permissions(timeline_url, username):
    """

    :param timeline_url:
    :param username:
    :return:
    """
    permissions_query = """
    SELECT username, role
      FROM permissions
      WHERE timeline_url = ? AND username = ? """
    results = APP_DB.query_to_json(permissions_query, [timeline_url, username])
    print(results)
    if not results:
        return make_response("No Permissions!", 201)
    else:
        return results[0]
