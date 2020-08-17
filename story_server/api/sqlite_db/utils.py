from ...api.__main__ import APP_DB

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


def _check_allowed_chars(string, allowed_chars):
    """
    checks if all chars in string are in allowed_chars list
    :param string: string to check
    :param allowed_chars: list of allowed chars
    :return: bool
    """
    is_cleared = [c in allowed_chars for c in string]
    return all(is_cleared)


def _not_valid_sql_input(sql_input):
    """
    checks that the sql is valis and no bas searches
    :param sql_input:
    :return:
    """
    BAD_SQL = ["%", "'", '"', ';', "#", "?", "-"]
    BAD_SQL = [val.encode('utf-8') for val in BAD_SQL]
    is_bad_sql = [c in BAD_SQL for c in sql_input]
    return any(is_bad_sql)

