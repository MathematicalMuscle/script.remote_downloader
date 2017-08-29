"""Some helper functions

"""

import xbmc
import xbmcgui

import os
import urllib2

from . import name_functions


def resp_content_resumable(url, headers, size, title, url0):
    try:
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes={0}-'.format(size)

        req = urllib2.Request(url, headers=headers)
        resp = urllib2.urlopen(req, timeout=30)

    except:
        dest, _ = name_functions.get_dest(title, url0, look_for_duplicates=False)
        xbmcgui.Dialog().ok(title, dest, 'Download failed', 'No response from server')
        return None, None, None

    try:
        content = int(resp.headers['Content-Length'])
    except:
        xbmcgui.Dialog().ok(title, name_functions.trans(title), 'Unknown filesize', 'Unable to download')
        return None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    if resumable:
        xbmc.log("Download is resumable")

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

    if (not downloaded) or (not playing):
        xbmcgui.Dialog().ok(title, text)
        xbmcgui.Window(10000).clearProperty('GEN-DOWNLOADED')

    return
