
from flask import make_response, send_file
from ..server_utils.consts import (
    DB_PATH,
)
from ..server_utils import Database

APP_DB = Database(db_file=DB_PATH)


from time import sleep


# TODO: consts page with all the things.
# TODO: save the queries not in the python file, in sql files.
# TODO: no special chars in url!
# TODO: context manager for the connect.


# ##################################################


def get_all_names(num=None):
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
        results = query(DB_PATH, timelines_query)
    else:
        timelines_query += ' LIMIT ?'
        results = query(DB_PATH, timelines_query, [num])
    if results is None:
        return make_response(
            "Query Error!", 500
        )
    else:
        return results

