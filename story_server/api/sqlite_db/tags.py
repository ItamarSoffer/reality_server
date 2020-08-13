from flask import make_response
from story_server.api.__main__ import APP_DB
from story_server.server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
)
import uuid
from ...server_utils.time_functions import get_timestamp
# from .posts import _add_tags
from ..jwt_functions import check_jwt, _search_in_sub_dicts, decrypt_auth_token
from .utils import _get_id_by_url
from .users_functions import PERMISSION_POWER, _check_permissions


TAGS_COLORS = ['#f5222d', '#fa541c', '#fa8c16', '#faad14', '#fadb14',
               '#a0d911', '#52c41a', '#13c2c2', '#40a9ff', '#2f54eb',
               '#722ed1', '#eb2f96',  "#808080", '#000000']


@check_jwt
def add_tag(timeline_url, **kargs):
    # check the user permissions
    story_id = _get_id_by_url(timeline_url)
    tag_name = _search_in_sub_dicts(kargs, "tag_name")
    if _is_tag_exists(story_id, tag_name):
        return make_response("Tag exists", 201)
    tag_color = _search_in_sub_dicts(kargs, "tag_color")
    tag_id = str(uuid.uuid4())
    if ',' in tag_name:
        return make_response("No comma in tags.", 201)

    # "STORY_TAGS": ['story_id', 'tag_id', 'tag_name', 'tag_color', 'create_time'],
    APP_DB.insert(table=TABLES_NAMES["STORY_TAGS"],
                  columns=TABLES_COLUMNS["STORY_TAGS"],
                  data=[story_id,
                        tag_id,
                        tag_name,
                        tag_color,
                        get_timestamp()
                        ])
    return make_response("created new tag", 200)


@check_jwt
def get_tags_by_timeline(timeline_url, **kargs):
    """
    returns all tags of story
    :param timeline_url:
    :param kargs:
    :return:
    """
    story_id = _get_id_by_url(timeline_url)
    tag_query = """
    with tags_counter AS (	
SELECT tag_id, count(*) as counter
FROM events_tags
 GROUP BY tag_id)
 SELECT s.tag_id, s.tag_name, s.tag_color, 
 CASE 
 WHEN c.counter is NULL THEN 0
 ELSE c.counter
 END AS counter
   FROM story_tags s
  LEFT OUTER JOIN tags_counter c
  ON s.tag_id = c.tag_id
      WHERE s.story_id = ?"""
    return APP_DB.query_to_json(tag_query, [story_id])


@check_jwt
def del_tag(timeline_url, tags_data):
    """
    deletes the tag from timeline and from all the events
    :param timeline_url:
    :param tags_data:
    :return:
    """
    jwt_token = _search_in_sub_dicts(tags_data, "jwt_token")
    user = decrypt_auth_token(jwt_token)
    if _check_permissions(timeline_url, user, return_level=True) < PERMISSION_POWER['write']:
        return make_response("User cant edit this story!", 201)
    else:
        tag_id = _search_in_sub_dicts(tags_data, "tag_id")
        story_id = _get_id_by_url(timeline_url)
        del_tag_events_query = """
        DELETE
        FROM events_tags
        WHERE story_id = ? AND tag_id = ?"""
        del_tag_story_query = """
        DELETE
        FROM story_tags
         WHERE story_id = ? AND tag_id = ?"""
        APP_DB.run(del_tag_events_query, [story_id, tag_id])
        APP_DB.run(del_tag_story_query, [story_id, tag_id])
        return make_response("Tag Deleted", 200)


def get_tags_by_event(event_id, **kargs):
    tag_query = """
    SELECT e.tag_id, s.tag_name, s.tag_color
  FROM events_tags e
 INNER JOIN story_tags s 
   ON s.tag_id = e.tag_id
   WHERE e.event_id = ?
          """
    return APP_DB.query_to_json(tag_query, [event_id])


def _get_tag_by_story(story_id, tag_name):
    """
    checks by name if tag exists,
    if yes- inserts to the events_tags table.
    if not -creates in the story_tags, and then inserts to events_tags
    :param story_id:
    :param tag_name:
    :return:
    """
    tag_exists = _is_tag_exists(story_id, tag_name)

    if tag_exists:
        return tag_exists
    else:
        from random import randint
        tag_color = TAGS_COLORS[randint(0, len(TAGS_COLORS) - 1)]
        tag_id = str(uuid.uuid4())
        APP_DB.insert(table=TABLES_NAMES["STORY_TAGS"],
                      columns=TABLES_COLUMNS["STORY_TAGS"],
                      data=[story_id,
                            tag_id,
                            tag_name,
                            tag_color,
                            get_timestamp()
                            ])
        return tag_id


def _is_tag_exists(story_id, tag_name):
    q = """
        SELECT *
          FROM story_tags
          WHERE story_id = ? and (tag_name = ? OR tag_id = ?)"""
    result = APP_DB.query_to_json(q, [story_id, tag_name, tag_name])
    if result:
        return result[0]['tag_id']
    else:
        return None


def _add_tags(timeline_id, event_id, tags):
    if type(tags) == list:
        for tag_id in tags:
            APP_DB.insert(table=TABLES_NAMES["EVENTS_TAGS"],
                          columns=TABLES_COLUMNS["EVENTS_TAGS"],
                          data=[timeline_id, event_id, tag_id, get_timestamp()]
                          )


def _get_events_by_tags(story_id, tags):
    """
    return all event_id that has the one of the tags in them.
    :param story_id:
    :param tags:
    :return:
    """
    tags_query = """
    SELECT DISTINCT event_id
    FROM story_tags s 
    INNER JOIN events_tags t
    ON s.tag_id = t.tag_id
    WHERE s.story_id = ? 
	AND tag_name in ({tags_args})
  """.format(
        tags_args=",".join(["?" for val in tags])
    )
    results = APP_DB.query(query_string=tags_query, args=[story_id, *tags], return_headers=False)
    return [val[0] for val in results]



