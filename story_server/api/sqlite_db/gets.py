from flask import make_response, send_file
import os
from datetime import datetime
import pandas as pd
from story_server.api.__main__ import APP_DB
from story_server.server_utils.consts import (
    SYSTEM_NAME,
    XLSX_FOLDER,
)

from ..jwt_functions import check_jwt, _search_in_sub_dicts, decrypt_auth_token


@check_jwt
def get_all_timelines(num=None, **kargs):
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
        results = APP_DB.query_to_json(timelines_query)
    else:
        timelines_query += " LIMIT ?"
        results = APP_DB.query_to_json(timelines_query, [num])
    if results is None:
        return make_response("Query Error!", 500)
    else:
        return results


@check_jwt
def get_timelines_by_user(username, num=None, **kargs):
    """
    returns all the timelines a specific user can access
    :return:
    """
    # TODO:
    jwt_token = _search_in_sub_dicts(kargs, "jwt_token")
    username = decrypt_auth_token(jwt_token)
    print(f"username: {username}")

    timelines_query = """
SELECT id, url, username, role , t.description, t.name, t.create_user
  FROM permissions p
  INNER JOIN  timeline_ids t
  ON t.id = p.timeline_id
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
    # sleep(2)
    timeline_id = _get_id_by_url(url=timeline_url)
    if timeline_id is None:
        return make_response(
            "URL '{url}' does not exists!".format(url=timeline_url), 404
        )

    get_timeline_query = """
    SELECT *
      FROM events
	 WHERE timeline_id = ?
     ORDER BY event_time DESC """
    results = APP_DB.query_to_json(query_string=get_timeline_query, args=[timeline_id])
    if results is None:
        return make_response("Query Error!", 500)
    else:
        return {"events": results}


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


def _create_timeline_xlsx(timeline_url):
    """
    queries the db and creates timeline xlsx
    returns the fill path of the created file
    :param timeline_url:
    :return:
    """

    events_query = """
    SELECT name, header, text, link, event_time, icon, insertion_time, e.create_user
FROM events e
 INNER JOIN timeline_ids t
 ON (e.timeline_id = t.id)
 WHERE url = ?"""

    timeline_data_query = """
    SELECT name, url, description, create_time, create_user
    FROM timeline_ids
    WHERE url = ?
    """

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
        writer, sheet_name=f"{timeline_url}_events", index=False
    )
    timeline_data_df.to_excel(writer, sheet_name="Timeline_Data", index=False)

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
