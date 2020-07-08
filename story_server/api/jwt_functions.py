import os
import jwt
import datetime
import functools
from flask import make_response

from ..server_utils.consts import SECRET_KEY


def generate_auth_token(user_id, ):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=0, minutes=10, seconds=20),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        return e


def check_auth_token(auth_token):
    """
    Decodes the auth token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, SECRET_KEY)
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'INVALID TOKEN: Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'INVALID TOKEN: Please log in again.'


def check_jwt(func):
    @functools.wraps(func)
    def run_if_valid_jwt(*args, **kargs):
        jwt_token = _search_in_sub_dicts(kargs, 'jwt_token')
        if jwt_token is None:
            return make_response("No JWT was supllied!", 400)
        auth_check = check_auth_token(str.encode(jwt_token))
        if not auth_check.startswith("INVALID TOKEN"):
            return func(*args, **kargs)
        else:
            return make_response(auth_check, 401)

    return run_if_valid_jwt


def _search_in_sub_dicts(main_dict, search_key):
    """
    searches key in dict of dicts
    :param main_dict:
    :param search_key:
    :return:
    """
    for key, value in main_dict.items():
        if key == search_key:
            return value
        elif type(value) == dict:
            return _search_in_sub_dicts(value, search_key)
    return None


@check_jwt
def basic_jwt_check(**kargs):
    from ..server_utils.time_functions import get_timestamp
    print (get_timestamp())
    return make_response('JWT token is valid.', 200)


@check_jwt
def checker(*args, **kargs):
    print("IN FUNC")
    print("ARGS", str(args))
    print("KARGS", str(kargs))
