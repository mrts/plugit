from __future__ import with_statement

import urllib, urlparse, tempfile
from contextlib import closing
try:
    import json
except ImportError:
    import simplejson as json

from plugit import app
from plugit.exceptions import FetchError

def fetch_descriptor(base_url, appname, appversion=None):
    """
    Fetches the application descriptor from `url` and converts it to an
    `app.App` object.

    :return: `app.App` object.
    """
    url = urlparse.urljoin(base_url, appname)
    if appversion:
        url = _add_query_params(url, version=appversion)
    try:
        with closing(urllib.urlopen(url)) as response:
            app_dict = json.load(response)
    except Exception, e:
        raise FetchError("Error in fetching application descriptor: %s" %
                str(e))
    return app.App(**app_dict)

def fetch_package(url):
    """
    Fetches the application package from `url`.

    :return: full path to the downloaded package (in a temporary directory).
    """
    tmpdir = tempfile.mkdtemp()
    try:
        filename, _ = urllib.urlretrieve(url, tmpdir)
    except Exception, e:
        raise FetchError("Error in fetching application package: %s" %
                str(e))
    return filename

def _add_query_params(url, **params):
    """
    Adds additional query parameters to the given url, preserving original
    parameters.

    Usage:
    >>> add_query_params('http://foo.com', a='b')
    'http://foo.com?a=b'
    >>> add_query_params('http://foo.com?a=b', b='c', d='q')
    'http://foo.com?a=b&b=c&d=q'

    A robust implementation should be more strict, e.g. do something
    intelligent with the following:
    >>> add_query_params('http://foo.com?a=b', a='b')
    'http://foo.com?a=b&a=b'
    """
    if not params:
        return url
    encoded = urllib.urlencode(params)
    url = urlparse.urlparse(url)
    return urlparse.urlunparse((url.scheme, url.netloc, url.path, url.params,
        (encoded if not url.query else url.query + '&' + encoded),
        url.fragment))

