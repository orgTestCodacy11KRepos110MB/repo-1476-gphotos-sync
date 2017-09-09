#!/usr/bin/python
# coding: utf8
import time
from datetime import datetime
import re

DATE_NORMALIZE = re.compile('(\d\d\d\d).(\d\d).(\d\d).(\d\d).(\d\d).(\d\d)')
SHORT_DATE_NORMALIZE = re.compile('(\d\d\d\d).(\d\d).(\d\d)')
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY = "%Y-%m-%d"


def retry(count, func, *arg, **k_arg):
    last_e = None
    for retry_no in range(count):
        try:
            res = func(*arg, **k_arg)
            return res
        except Exception as e:
            last_e = e
            print("\nRETRYING due to {}".format(e))
            print "Call was:", func, arg, k_arg
            time.sleep(.1)
    raise last_e


# does not work (why?), using verbose one below
def retry_i_x(count, iterator):
    for n in retry(count, iterator.next):
        yield n


def retry_i(count, iterator):
    last_item = None
    more_data = True
    while more_data:
        for retry_no in range(count):
            try:
                last_item = iterator.next()
                break
            except StopIteration:
                more_data = False
                break
            except Exception as e:
                print("\nRETRYING iterator due to {}".format(e))
                time.sleep(.1)
        yield last_item


def date_to_string(date_t, date_only=False):
    """
    :param (int) date_only:
    :param (datetime) date_t:
    :return (str):
    """
    if date_only:
        return date_t.strftime(DATE_ONLY)
    else:
        return date_t.strftime(DATE_FORMAT)


def string_to_date(date_string):
    m = DATE_NORMALIZE.match(date_string)
    if m:
        normalized = '{}-{}-{} {}:{}:{}'.format(*m.groups())
    else:
        m = SHORT_DATE_NORMALIZE.match(date_string)
        if m:
            normalized = '{}-{}-{} 00:00:00'.format(*m.groups())
        else:
            return datetime.min
            # raise TypeError('date {} bad format'.format(date_string))

    return datetime.strptime(normalized, DATE_FORMAT)


def timestamp_to_date(time_secs, hour_offset=0):
    date = datetime.fromtimestamp(
        int(time_secs) / 1000 + 3600 * hour_offset)
    return date


# gdata patches the http client to handle token refresh for oauth2
# but the signature is out of date for the current http_client.request.
# Here we patch over their patch to fix
# error 'TypeError: new_request() takes exactly 1 argument (4 given)'
# noinspection SpellCheckingInspection
def patch_http_client(oauth, client, request_orig2):
    """
    :param (gdata.gauth.OAuth2TokenFromCredentials) oauth:
    :param (gdata.photos.service.PhotoService) client:
    :param (instancemethod) request_orig2:
    :return:
    """
    client.auth_token = oauth

    # noinspection PyProtectedMember
    def new_request2(*args, **k_args):
        response = request_orig2(*args, **k_args)
        if response.status == 401 or response.status == 403:
            refresh_response = oauth._refresh(request_orig2)
            if oauth._invalid:
                return refresh_response
            else:
                print('\n token refresh: {}\n'.format(oauth.access_token))
                new_h = '{}{}'.format('Bearer ', oauth.access_token)
                client.additional_headers['Authorization'] = new_h
                k_args['headers']['Authorization'] = new_h
            return request_orig2(*args, **k_args)
        else:
            return response

    client.http_client.request = new_request2
    return client
