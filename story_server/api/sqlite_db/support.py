from flask import make_response
from ..__main__ import APP_DB
from ..jwt_functions import check_jwt, decrypt_auth_token, _search_in_sub_dicts
from ...server_utils.consts import (
    TABLES_COLUMNS,
    TABLES_NAMES,
)
from ...server_utils.time_functions import get_timestamp


@check_jwt(log=True)
def contact_support(request_data, **kargs):
    """
    Handles the Contact form.
    Saves issue data in DB and sends mail.
    :param request_data: dict with data from frontend
    :param kargs:
    :return:
    """
    jwt_token = _search_in_sub_dicts(request_data, 'jwt_token')
    username = decrypt_auth_token(jwt_token)
    title = _search_in_sub_dicts(request_data, 'title')
    content = _search_in_sub_dicts(request_data, 'content')
    APP_DB.insert(table=TABLES_NAMES['SUPPORT_REQUESTS'],
                  columns=TABLES_COLUMNS['SUPPORT_REQUESTS'],
                  data=[username, title, content, get_timestamp()])
    # TODO: send mail to me, cc the person who sent.
    return make_response('Request has been sent.', 200)
