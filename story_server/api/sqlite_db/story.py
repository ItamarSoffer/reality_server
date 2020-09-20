import uuid
import logging
from flask import make_response

from .tags import _get_events_by_tags, get_tags_by_event
from .users_functions import _add_permissions, PERMISSION_POWER, _check_permissions
from .utils import _get_id_by_url, _is_url_exists, _check_allowed_chars, _not_valid_sql_input
from ..__main__ import APP_DB
from ..jwt_functions import check_jwt, decrypt_auth_token, _search_in_sub_dicts
from ...html_parsers import HtmlParser, fetch_story_extra_data
from ...server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    RESERVED_TIMELINE_NAMES,
    ALLOWED_CHARS,
)
from ...server_utils.time_functions import get_timestamp


# ############### CREATES ###############
@check_jwt(log=True)
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
    return make_response("new Story '{name}' created!".format(name=name), 200)


# ############### GETS ###############


@check_jwt()
def get_all_timelines(num=None, **kargs):
    """
    returns all the data from the timeline_ids table, for the main cards view.
    :return:
    """
    search_string = _search_in_sub_dicts(kargs, search_key="search_string")
    search_string_query = ''
    if search_string is not None:
        # search_string = search_string.encode('utf-8')
        if _not_valid_sql_input(search_string):
            return make_response('Non Valid Search!', 201)
        search_string_query = \
            """WHERE (name LIKE '%{search_string}%'
            OR description LIKE '%{search_string}%')
            """ \
                .format(search_string=search_string)
    timelines_query = """
    WITH event_counter AS 
    (
    SELECT timeline_id, count(*) as counter, max(modify_time) AS max_modify
      FROM events
     GROUP BY timeline_id
      )
      SELECT t.*, counter,
          CASE
    WHEN max_modify IS NOT NULL THEN max_modify
    ELSE t.create_time
    END AS last_modify
      FROM timeline_ids t
      LEFT OUTER JOIN event_counter e
      ON t.id = e.timeline_id
      {search_string_query}
      ORDER BY create_time DESC
    """.format(search_string_query=search_string_query)

    if num is None:
        results = APP_DB.query_to_json(timelines_query)
    else:
        timelines_query += " LIMIT ?"
        results = APP_DB.query_to_json(timelines_query, [num])
    if results is None:
        return make_response("Query Error!", 500)
    else:
        for line in results:
            q = """
            SELECT display_name 
            FROM users 
            WHERE username = ?"""
            full_name = APP_DB.query_to_json(query_string=q, args=[line['create_user']])[0]['display_name']
            line['create_user'] = full_name
            line['last_modify'] = line['last_modify'][:19]
        return results


@check_jwt()
def get_timelines_by_user(num=None, **kargs):
    """
    returns all the timelines a specific user can access
    :return:
    """
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)

    search_string = _search_in_sub_dicts(kargs, search_key="search_string")
    search_string_query = ''
    if search_string is not None:
        # search_string = search_string.encode('utf-8')
        if _not_valid_sql_input(search_string):
            return make_response('Non Valid Search!', 201)
        search_string_query = \
            """AND(name LIKE '%{search_string}%'
            OR description LIKE '%{search_string}%')
            """ \
                .format(search_string=search_string)

    timelines_query = """
        WITH event_counter AS 
    (
    SELECT timeline_id, count(*) as counter, max(modify_time) AS max_modify
      FROM events
     GROUP BY timeline_id
      )
SELECT id, url, username, role , t.description, t.name, t.create_user, e.counter,
    CASE
    WHEN max_modify IS NOT NULL THEN max_modify
    ELSE t.create_time
    END AS last_modify
  FROM permissions p
  INNER JOIN  timeline_ids t
  ON t.id = p.timeline_id
  LEFT OUTER JOIN event_counter e 
  ON t.id = e.timeline_id
  WHERE username = ? and role != 'none'
  {search_string_query}
    """.format(search_string_query=search_string_query)
    if num is None:
        results = APP_DB.query_to_json(timelines_query, [username])
    else:
        timelines_query += " LIMIT ?"
        results = APP_DB.query_to_json(timelines_query, [num])
    if results is None:
        return make_response("Query Error!", 500)
    else:
        for line in results:
            q = """
            SELECT display_name 
            FROM users 
            WHERE username = ?"""
            full_name = APP_DB.query_to_json(query_string=q, args=[line['create_user']])[0]['display_name']
            line['create_user'] = full_name
            line['last_modify'] = line['last_modify'][:19]

        # in the front: it will be in response.data.results
        return make_response({"results": results}, 200)


@check_jwt()
def get_timeline_basic_data(timeline_url, **kargs):
    """
    returns the basic timeline data.
    :param timeline_url:
    :return:
    """
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    user = decrypt_auth_token(jwt_token)
    if _check_permissions(timeline_url, user, return_level=True) < PERMISSION_POWER['read']:
        return make_response(
            "User {user} has no read permissions".format(user=user), 201
        )
    data_query = """
    SELECT *
      FROM timeline_ids
      WHERE url = ? """
    results = APP_DB.query_to_json(query_string=data_query, args=[timeline_url])
    return results


@check_jwt(log=True)
def get_timeline(timeline_url, **kargs):
    """
    returns all the events data of a timeline
    each event data is a json.dumps
    :param timeline_url:
    :return:
    """
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "URL '{url}' does not exists!".format(url=timeline_url), 404
        )
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    user = decrypt_auth_token(jwt_token)
    if _check_permissions(timeline_url, user, return_level=True) < PERMISSION_POWER['read']:
        return make_response(
            "User {user} has no write permissions".format(user=user), 201
        )
    args = [timeline_id]

    fetch_extra_data = _search_in_sub_dicts(kargs, 'extra_data')

    min_time = _search_in_sub_dicts(kargs, "min_time")
    max_time = _search_in_sub_dicts(kargs, "max_time")
    search_string = _search_in_sub_dicts(kargs, "search_string")
    tags = _search_in_sub_dicts(kargs, "tags")

    min_time_string = ''
    max_time_string = ''
    search_string_query = ''
    events_tags_string_query = ''

    if min_time:
        min_time_string = "AND event_time >= ?"
        args.append(min_time)

    if max_time:
        max_time_string = "AND event_time <= ?"
        args.append(max_time)

    if search_string:
        # check against SQL injection
        # search_string = search_string.encode('utf-8')
        if _not_valid_sql_input(search_string):
            return make_response('Non Valid Search!', 201)
        search_string_query = \
            """AND (header LIKE '%{search_string}%'
            OR text LIKE '%{search_string}%'
            OR link LIKE '%{search_string}%')
            """ \
                .format(search_string=search_string)

    if tags:
        relevant_event_ids = _get_events_by_tags(timeline_id, tags)
        events_tags_string_query = \
            """AND (event_id in ({events_place}))
            """ \
                .format(events_place=",".join(["?" for val in relevant_event_ids]))
        args += relevant_event_ids

    get_timeline_query = """
    SELECT *
      FROM events
	 WHERE timeline_id = ?
	 {min_time_string}
	 {max_time_string}
	 {search_string_query}
	 {events_tags_string_query}
     ORDER BY event_time DESC """ \
        .format(min_time_string=min_time_string,
                max_time_string=max_time_string,
                search_string_query=search_string_query,
                events_tags_string_query=events_tags_string_query)
    results = APP_DB.query_to_json(query_string=get_timeline_query, args=args)
    if results is None:
        return make_response("Query Error!", 500)
    else:
        for line in results:
            line['tags'] = get_tags_by_event(line['event_id'])
        if fetch_extra_data:
            jwt_token = _search_in_sub_dicts(kargs, 'jwt_token')
            username = decrypt_auth_token(jwt_token)
            results = _fetch_extra_data(results, username)

        return {"events": results}


def _fetch_extra_data(events, username):
    multiprocess = True
    import time
    start = time.perf_counter()
    if multiprocess:
        events = fetch_story_extra_data(events, username)
    else:
        for line in events:
            if line['link']:
                extra_data_parser = HtmlParser(line['link'], username)
                extra_data = extra_data_parser.match_parser()
                if extra_data:
                    line['extra_data'] = extra_data
                    logging.info("fetched {} after {}".format(line['link'], time.perf_counter() - start))

    end = time.perf_counter()
    logging.info("took: {} seconds".format(end - start))
    return events



# ############### DELETES ###############

@check_jwt()
def delete_timeline(timeline_id, **kargs):
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)

    role = _check_permission_by_timeline_id(timeline_id, username)
    if not role:
        return make_response("User has no permissions or wrong timeline ID", 201)

    role = role[0][0]
    if PERMISSION_POWER[role] < PERMISSION_POWER['owner']:
        return make_response("User doesnt have permissions to delete story!", 201)
    else:
        delete_events_query = """
            DELETE
            FROM events
            WHERE timeline_id = ?"""
        APP_DB.run(delete_events_query, [timeline_id])
        delete_timeline_query = """
            DELETE
            FROM timeline_ids
            WHERE id = ?"""
        APP_DB.run(delete_timeline_query, [timeline_id])
        delete_permissions_query = """
                    DELETE
                    FROM permissions
                    WHERE timeline_id = ?"""
        APP_DB.run(delete_permissions_query, [timeline_id])
        delete_tags_query = """
                            DELETE
                            FROM story_tags
                            WHERE story_id = ?"""
        APP_DB.run(delete_tags_query, [timeline_id])
        delete_favorites_query = """
                                    DELETE
                                    FROM favorites
                                    WHERE story_id = ?"""
        APP_DB.run(delete_favorites_query, [timeline_id])

        return make_response("Story and its events deleted successfully", 200)


def _check_permission_by_timeline_id(event_id, username):
    query = """
      SELECT role
    FROM permissions p  
     WHERE username =? and timeline_id = ?"""
    return APP_DB.query(query, [username, event_id], return_headers=False)


# new
# ############### UPDATES ###############


@check_jwt
def edit_name_description(timeline_url, new_properties):
    """
    edits the name or the description of a story.
    gets name or description param, and runs the change.
    :param timeline_url:
    :param new_properties:
    :return:
    """
    story_id = _get_id_by_url(timeline_url)
    new_name = _search_in_sub_dicts(new_properties, "new_name")
    new_description = _search_in_sub_dicts(new_properties, "new_description")

    jwt_token = _search_in_sub_dicts(new_properties, "jwt_token")
    username = decrypt_auth_token(jwt_token)

    if _check_permissions(timeline_url, username, return_level=True) < PERMISSION_POWER['write']:
        return make_response('User has no edit permissions', 201)
    else:
        if new_name:
            return _update_story_name(story_id, new_name)
        else:
            # the description can be empty.
            return _update_story_description(story_id, new_description)


def _update_story_name(story_id, new_story_name):
    update_query = """
    UPDATE timeline_ids
    SET name = ?
    WHERE id = ?
    """
    APP_DB.run(update_query, args=[new_story_name, story_id])
    return make_response('Updated story name', 200)


def _update_story_description(story_id, new_story_description):
    update_query = """
    UPDATE timeline_ids
    SET description = ?
    WHERE id = ?
    """
    APP_DB.run(update_query, args=[new_story_description, story_id])
    return make_response('Updated story description', 200)