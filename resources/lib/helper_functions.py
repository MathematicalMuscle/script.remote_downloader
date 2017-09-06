"""Some helper functions

"""

import xbmc
import xbmcgui

import os
import urllib2
import urlparse

from . import simple


def resp_content_resumable(url, headers, size=0, title=None):
    url0 = simple.get_url0(url)
    try:
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes={0}-'.format(size)

        req = urllib2.Request(url0, headers=headers)
        resp = urllib2.urlopen(req, timeout=30)

    except:
        if title is not None:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: no response from server')
        return None, None, None

    try:
        content = int(resp.headers['Content-Length'])
    except:
        if title is not None:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: unknown filesize')
        return None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    return resp, content, resumable


def done(title, dest, downloaded):
    playing = xbmc.Player().isPlaying()
    text = xbmcgui.Window(10000).getProperty('GEN-DOWNLOADED')

    if len(text) > 0:
        text += '[CR]'

    if downloaded:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR forestgreen]Download succeeded[/COLOR]')
    else:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR red]Download failed[/COLOR]')

    xbmcgui.Window(10000).setProperty('GEN-DOWNLOADED', text)

    if not downloaded or not playing:
        xbmcgui.Dialog().ok(title, text)
        xbmcgui.Window(10000).clearProperty('GEN-DOWNLOADED')

    return


def get_url0(url):
    return url.split('|')[0]


def get_headers(url):
    try:
        headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict('')
    return headers
