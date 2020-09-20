import os
import uuid
from datetime import datetime
import logging

import pandas as pd
from flask import make_response, send_file
from story_server.api.__main__ import APP_DB
from story_server.server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
    SYSTEM_NAME,
    XLSX_FOLDER,
    IMPORT_XLSX_FOLDER
)

from .tags import _get_tag_by_story, _add_tags
from .utils import _is_url_exists, _get_id_by_url
# from .posts import _add_tags
from ..jwt_functions import check_jwt, _search_in_sub_dicts
from ...server_utils.time_functions import get_timestamp


@check_jwt(log=True)
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
    upfile_raw = _search_in_sub_dicts(kwargs, 'upfile')

    file_name = '{timeline_url}_upload_{time}.xlsx'\
        .format(timeline_url=timeline_url,
                time=datetime.today().strftime("%Y%m%d-%H%M%S"))
    output_file =os.path.join(IMPORT_XLSX_FOLDER, file_name)

    with open(output_file, 'wb') as f:
        f.write(upfile_raw.read())

    xlsx_data = pd.concat(pd.read_excel(output_file, sheet_name=None), ignore_index=True)
    columns = xlsx_data.columns.tolist()
    # logging.info(columns)
    valid_column_names = ["title", "content", "link", "event_time", "color", "icon", "create_user", "tags"]
    if 'title' not in columns:
        logging.warning("missing title field")
        return make_response({"code": 201, 'message': "missing title field"}, 201)
    elif 'event_time' not in columns:
        logging.warning("missing event_time field")
        return make_response({"code": 201, 'message': "missing event_time field"}, 201)
    elif not all(elem in valid_column_names for elem in columns):
        logging.warning("There are non valid field names")
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

