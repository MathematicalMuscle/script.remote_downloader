"""Some very simple functions

"""

import urlparse


def get_url0(url):
    return url.split('|')[0]


def get_headers(url):
    try:
        headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict('')
    return headers
