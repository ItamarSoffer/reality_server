from flask import make_response

from .users_functions import check_jwt, _search_in_sub_dicts, decrypt_auth_token
from .utils import _get_id_by_url
from ..__main__ import APP_DB
from ...server_utils.consts import TABLES_NAMES, TABLES_COLUMNS
from ...server_utils.time_functions import get_timestamp


@check_jwt(log=True)
def add_favorite(timeline_url, **kargs):
    """
    Adds a story to favorite list.
    TODO: UNIQ index on story_id and username.
    :param timeline_url: Story URL
    :param kargs: jwt token
    :return:
    """

    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)
    story_id = _get_id_by_url(timeline_url)

    if story_id is None:
        return make_response("Non Valid Story!", 201)
    APP_DB.insert(table=TABLES_NAMES['FAVORITES'],
                  columns=TABLES_COLUMNS['FAVORITES'],
                  data=[story_id, username, get_timestamp()])
    print("added to favorites list")
    return make_response("Added story to favorites", 200)


@check_jwt(log=True)
def del_favorite(timeline_url, **kargs):
    """
    :param timeline_url: Story URL
    :param kargs: jwt token
    :return:
    """
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)
    story_id = _get_id_by_url(timeline_url)
    if story_id is None:
        return make_response("Non Valid Story!", 201)

    del_favorite_query = """
    DELETE
    FROM favorites 
    WHERE story_id = ? AND username = ? """
    APP_DB.run(del_favorite_query, args=[story_id, username])
    return make_response("Removed from favorites", 200)


@check_jwt()
def get_favorites(**kargs):
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)
    favorites_query = """
    SELECT *
      FROM favorite_stories_view 
       WHERE username = ?"""
    results = APP_DB.query_to_json(favorites_query, args=[username])
    return results
