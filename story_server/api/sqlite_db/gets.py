from flask import make_response, send_file
import os
from datetime import datetime
import pandas as pd
from story_server.api.__main__ import APP_DB
from story_server.server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    SYSTEM_NAME,
    XLSX_FOLDER,
    IMPORT_XLSX_FOLDER
)
import uuid
from ...server_utils.time_functions import get_timestamp
# from .posts import _add_tags
from ..jwt_functions import check_jwt, _search_in_sub_dicts, decrypt_auth_token

TAGS_COLORS = ['#f5222d', '#fa541c', '#fa8c16', '#faad14', '#fadb14',
               '#a0d911', '#52c41a', '#13c2c2', '#40a9ff', '#2f54eb',
               '#722ed1', '#eb2f96',  "#808080", '#000000']


@check_jwt
def get_all_timelines(num=None, **kargs):
    """
    returns all the data from the timeline_ids table, for the main cards view.
    :return:
    """
    timelines_query = """
    WITH event_counter AS 
    (
    SELECT timeline_id, count(*) as counter
      FROM events
     GROUP BY timeline_id
      )
      SELECT t.*, counter
      FROM timeline_ids t
      LEFT OUTER JOIN event_counter e
      ON t.id = e.timeline_id
      ORDER BY create_time DESC
    """
    if num is None:
        results = APP_DB.query_to_json(timelines_query)
    else:
        timelines_query += " LIMIT ?"
        results = APP_DB.query_to_json(timelines_query, [num])
    if results is None:
        return make_response("Query Error!", 500)
    else:
        return results


@check_jwt
def get_timelines_by_user(num=None, **kargs):
    """
    returns all the timelines a specific user can access
    :return:
    """
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)
    timelines_query = """
        WITH event_counter AS 
    (
    SELECT timeline_id, count(*) as counter
      FROM events
     GROUP BY timeline_id
      )
SELECT id, url, username, role , t.description, t.name, t.create_user, e.counter
  FROM permissions p
  INNER JOIN  timeline_ids t
  ON t.id = p.timeline_id
  LEFT OUTER JOIN event_counter e 
  ON t.id = e.timeline_id
  WHERE username = ? and role != 'none'
    """
    if num is None:
        results = APP_DB.query_to_json(timelines_query, [username])
    else:
        timelines_query += " LIMIT ?"
        results = APP_DB.query_to_json(timelines_query, [num])
    if results is None:
        return make_response("Query Error!", 500)
    else:
        return results


@check_jwt
def get_timeline_basic_data(timeline_url, **kargs):
    """
    returns the basic timeline data.
    :param timeline_url:
    :return:
    """
    data_query = """
    SELECT *
      FROM timeline_ids
      WHERE url = ? """
    results = APP_DB.query_to_json(query_string=data_query, args=[timeline_url])
    return results


@check_jwt
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
    args = [timeline_id]

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
        search_string_query = \
            """AND (header LIKE '%{search_string}%'
            OR text LIKE '%{search_string}%'
            OR link LIKE '%{search_string}%')
            """\
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
     ORDER BY event_time DESC """\
        .format(min_time_string=min_time_string,
                max_time_string=max_time_string,
                search_string_query=search_string_query,
                events_tags_string_query=events_tags_string_query)
    results = APP_DB.query_to_json(query_string=get_timeline_query, args=args)
    if results is None:
        return make_response("Query Error!", 500)
    else:
        import time
        # start = time.perf_counter()
        for line in results:
            line['tags'] = get_tags_by_event(line['event_id'])
        end = time.perf_counter()
        # print("took: {} seconds".format(end-start))
        return {"events": results}


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


@check_jwt
def get_timeline_xlsx_file(timeline_url, **kwargs):
    if not _is_url_exists(timeline_url):
        return make_response(
            "URL: {url} Does not exists!".format(url=timeline_url), 201
        )
    _clear_pass_files(XLSX_FOLDER, timeline_url)
    xlsx_file_path = _create_timeline_xlsx(timeline_url)
    xlsx_file_name = os.path.basename(xlsx_file_path)

    return send_file(
        xlsx_file_path,
        attachment_filename=xlsx_file_name,
        cache_timeout=-1,
        as_attachment=True,
    )


# @check_jwt
def import_xlsx_file(timeline_url, **kwargs):
    print(kwargs)
    upfile_raw = _search_in_sub_dicts(kwargs, 'upfile')

    file_name = '{timeline_url}_upload_{time}.xlsx'\
        .format(timeline_url=timeline_url,
                time=datetime.today().strftime("%Y%m%d-%H%M%S"))
    output_file =os.path.join(IMPORT_XLSX_FOLDER, file_name)

    with open(output_file, 'wb') as f:
        f.write(upfile_raw.read())

    xlsx_data = pd.concat(pd.read_excel(output_file, sheet_name=None), ignore_index=True)
    columns = xlsx_data.columns.tolist()
    print(columns)
    valid_column_names = ["title", "content", "link", "event_time", "color", "icon", "create_user", "tags"]
    if 'title' not in columns:
        print("missing title field")
        return make_response({"code": 201, 'message': "missing title field"}, 201)
    elif 'event_time' not in columns:
        print("missing event_time field")
        return make_response({"code": 201, 'message': "missing event_time field"}, 201)
    elif not all(elem in valid_column_names for elem in columns):
        print("There are non valid field names")
        return make_response({"code": 201, 'message': "There are non valid field names"}, 201)
    else:
        timeline_id = _get_id_by_url(timeline_url)
        for index in range(len(xlsx_data)):
            event_id = str(uuid.uuid4())
            line = xlsx_data.iloc[index]

            tags = _extract_field_from_df_line(line, "tags", None)
            # move to another function.
            header = _extract_field_from_df_line(line, "title")
            text = _extract_field_from_df_line(line, "content", '')
            link = _extract_field_from_df_line(line, "link", None)
            event_time = _extract_field_from_df_line(line, "event_time")
            frame_color = _extract_field_from_df_line(line, "color", 'rgb(33, 150, 243)')
            icon = _extract_field_from_df_line(line, "icon", '')
            create_user = _extract_field_from_df_line(line, "create_user", 'XLSX')
            insertion_time = get_timestamp()
            APP_DB.insert(
                table=TABLES_NAMES["EVENTS"],
                columns=TABLES_COLUMNS["EVENTS"],
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
            _insert_tags_from_xlsx(timeline_id, event_id, tags)
        return make_response({"status": 'done',
                              "code": 200,
                              "message": "Added {} new events to timeline".format(len(xlsx_data))},
                             200)


def _insert_tags_from_xlsx(timeline_id, event_id, tags):
    """
    for each tag:
    checks by name if it exists,
    if yes- inserts to the events_tags table.
    if not -creates in the story_tags, and then inserts to events_tags
    :param timeline_id:
    :param event_id:
    :param tags:
    :return:
    """
    tags = tags.split(",")
    for tag_name in tags:
        if len(tag_name) > 0:
            tag_id = _get_tag_by_story(timeline_id, tag_name.strip())
            _add_tags(timeline_id, event_id, [tag_id])


def _extract_field_from_df_line(line, field, default_val=None):
    """
    extracts the field and handle key error.
    if KetError- return default val
    :param line:
    :param field:
    :param default_val:
    :return:
    """
    try:
        return line[field]
    except KeyError:
        return default_val


def _create_timeline_xlsx(timeline_url):
    """
    queries the db and creates timeline xlsx
    returns the fill path of the created file
    :param timeline_url:
    :return:
    """

    events_query = """
    SELECT name, header as 'title', text as 'content', link, event_time, icon, 
    frame_color as 'color', insertion_time, e.create_user
    FROM events e
    INNER JOIN timeline_ids t
    ON (e.timeline_id = t.id)
    WHERE url = ?"""

    timeline_data_query = """
    SELECT name, url, description, create_time, create_user
    FROM timeline_ids
    WHERE url = ?
    """
    # TODO: join on the event_id, with XML CONCAT for the tags.
    timeline_events_df = APP_DB.query_to_df(
        query_string=events_query, args=[timeline_url]
    )
    timeline_data_df = APP_DB.query_to_df(
        query_string=timeline_data_query, args=[timeline_url]
    )
    file_name = "{sys_name}_{timeline_name}@{time}.xlsx".format(
        sys_name=SYSTEM_NAME,
        timeline_name=timeline_url,
        time=datetime.today().strftime("%Y%m%d-%H%M%S"),
    )
    xlsx_path = os.path.join(XLSX_FOLDER, file_name)

    writer = pd.ExcelWriter(xlsx_path, engine="xlsxwriter")
    timeline_events_df.to_excel(
        writer, sheet_name="{timeline_url}_events".format(timeline_url=timeline_url), index=False
    )
    # timeline_data_df.to_excel(writer, sheet_name="Timeline_Data", index=False)

    writer.save()
    return xlsx_path


def _clear_pass_files(folder, timeline_url):
    """
    clear pass xlsx files that was created by the system.
    :param folder:
    :param timeline_url:
    :return:
    """
    file_name = "{sys_name}_{timeline_name}@".format(
        sys_name=SYSTEM_NAME, timeline_name=timeline_url,
    )
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.startswith(file_name):
                os.remove(os.path.join(root, f))


def _get_id_by_url(url):
    q = """
    SELECT id 
    FROM timeline_ids
    WHERE url = ?
    """
    results = APP_DB.query_to_json(q, [url])
    if results:
        return results[0]["id"]
    else:
        return None


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

    return APP_DB.query_to_json(url_query_check, [url])



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
          WHERE story_id = ? and tag_name = ?"""
    result = APP_DB.query_to_json(q, [story_id, tag_name])
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

