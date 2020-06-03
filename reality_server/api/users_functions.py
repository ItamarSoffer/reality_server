from flask import make_response
from .__main__ import APP_DB
from ..server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    ALLOWED_CHARS,

)
from ..server_utils.time_functions import get_timestamp



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
    print(results)
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
