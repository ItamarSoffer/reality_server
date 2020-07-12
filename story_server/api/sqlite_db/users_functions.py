from flask import make_response
from ..__main__ import APP_DB
from ...server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
)
from ...server_utils.time_functions import get_timestamp
from .gets import _get_id_by_url, _is_url_exists

from ..jwt_functions import generate_auth_token, check_jwt, _search_in_sub_dicts, decrypt_auth_token

PERMISSION_POWER = {
    None: -1,
    'none': 0,
    'read': 1,
    'write': 2,
    'owner': 3,
    'creator': 4
}


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
        return generate_auth_token(username).decode('utf-8')
        # return make_response("{user} logged in successfully".format(user=username), 200)


def _add_permissions(timeline_url, username, role):
    timeline_id = _get_id_by_url(timeline_url)
    # deletes prev permissions:
    del_q = \
        """ DELETE
              FROM permissions
             WHERE timeline_url = ? and username = ? and role != 'owner'
        """
    APP_DB.run(del_q, [timeline_url, username])
    APP_DB.insert(table=TABLES_NAMES["PERMISSIONS"],
                  columns=TABLES_COLUMNS["PERMISSIONS"],
                  data=[
                      timeline_id,
                      timeline_url,
                      username,
                      role,
                      get_timestamp()
                  ])


def _check_permissions(timeline_url, username):
    """
    return the max permission level for a user
    (if the public has stronger permissions- he will get it)
    :param timeline_url:
    :param username:
    :return:
    """
    user_permissions_query = """
    SELECT username, role
      FROM permissions
      WHERE timeline_url = ? AND username = ? AND role != 'none' """

    public_permissions_query = """
    SELECT username, role
      FROM permissions
      WHERE timeline_url = ? AND username = 'public' AND role != 'none' """
    user_results = APP_DB.query_to_json(user_permissions_query, [timeline_url, username])
    public_results = APP_DB.query_to_json(public_permissions_query, [timeline_url])

    permission = _calc_max_permission(user_results, public_results)
    return {'username': username, 'role': permission}


def _calc_max_permission(*permissions_data):
    """
    calculated the max permission power by the data
    :param permissions_data: list of results for query, of usernames and roles.
    :return:
    """
    permissions_power = []
    for record in permissions_data:
        if record:
            permissions_power.append(PERMISSION_POWER[record[0]['role']])
        else:
            permissions_power.append(-1)
    max_permission = max(*permissions_power)
    return [key for key, value in PERMISSION_POWER.items() if value == max_permission][0]

@check_jwt
def check_permissions(timeline_url, **kargs):
    """

    :param timeline_url:
    :param username:
    :return:
    """
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)
    url_exists = _is_url_exists(timeline_url)
    if not url_exists:
        return make_response("URL does not exists!", 204)

    role = _check_permissions(timeline_url, username)
    if not role:
        return make_response("No Permissions!", 201)
    else:
        return role


def _user_has_story_permissions(username):
    return APP_DB.query(
        query_string="""
        SELECT username 
         FROM users
         WHERE username = ?""",
        args=[username]
    )[1]


def _is_owner(username, timeline_url):

    permissions = _check_permissions(username=username, timeline_url=timeline_url)
    if not permissions:
        return False
    else:
        return permissions == 'owner'


def _role_check(username, timeline_url, role):
    """
    checks if the user has the role for the timeline.
    :param username:
    :param timeline_url:
    :param role:
    :return:
    """
    permissions = _check_permissions(username=username, timeline_url=timeline_url)
    if not permissions:
        return False
    else:
        return permissions['role'] == role


@check_jwt
def set_permissions(timeline_url, permissions_data, **kargs):
    """
    sets permission to user.
    :param timeline_url:
    :param permissions_data: the data
    :return:
    """

    username = permissions_data.get("username")
    role = permissions_data.get("role")
    jwt_token = _search_in_sub_dicts(permissions_data, "jwt_token")
    adding_user = decrypt_auth_token(jwt_token)

    # check username has permissions to system.
    if role not in PERMISSION_POWER.keys():
        return make_response("non valid role type!", 201)
    elif not (_user_has_story_permissions(username) or username == 'public'):
        return make_response("User '{user}' has no permissions to Story!".format(user=username), 201)
    # never will be because the jwt auth.
    elif not _user_has_story_permissions(adding_user):
        return make_response("User '{user}' has no permissions to Story!".format(user=adding_user), 201)
    # checks he doesnt messes the permissions:
    elif _is_owner(username, timeline_url):
        return make_response("You are the owner, Do not mess with the permissions.", 201)
    # adds relevant permissions.
    elif _is_owner(adding_user, timeline_url):
        _add_permissions(timeline_url=timeline_url, username=username, role=role)
        return make_response("Permissions were set to {username}".format(username=username), 200)
    else:
        return make_response("Only owner can change permissions.", 201)


@check_jwt
def permitted_users(timeline_url, **kargs):
    """
    returns all users that has permissions, and roles
    :param timeline_url:
    :return:
    """
    query = """
    SELECT username, role
    FROM permissions
    WHERE timeline_url = ? and role != 'none'
    """
    return APP_DB.query_to_json(query, args=[timeline_url])