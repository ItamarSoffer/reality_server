
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


