"""Some helper functions

"""

import sys

import xbmcaddon
import xbmcgui

import urllib2
import urlparse

from . import json_functions


def get_url0(url):
    return url.split('|')[0]


def get_headers(url):
    try:
        headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict('')
    return headers


def resp_bytesize_resumable(url, headers, size=0):
    try:
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes={0}-'.format(size)

        url0 = get_url0(url)
        req = urllib2.Request(url0, headers=headers)
        resp = urllib2.urlopen(req, timeout=30)

    except:
        xbmcgui.Dialog().ok('Remote Downloader', 'Error: no response from server')
        return None, None, None

    try:
        bytesize = int(resp.headers['Content-Length'])
    except:
        xbmcgui.Dialog().ok('Remote Downloader', 'Error: unknown filesize')
        return None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    return resp, bytesize, resumable
    

def get_downloading_system(r_ip, r_port, r_user, r_pass):
    if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'Yes':
        return None, None, None, None

    else:
        for i in range(5):
            # get info about the downloading Kodi system
            d_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address{0}'.format(i+1))
            d_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port{0}'.format(i+1))
            d_user = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username{0}'.format(i+1))
            d_pass = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password{0}'.format(i+1))

            if d_ip:
                # check that the remote system is available
                if json_functions.jsonrpc(method='JSONRPC.Ping', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5) == 'pong':
                    # check that the remote system will be able to communicate with this system
                    if json_functions.jsonrpc(method='JSONRPC.Ping', ip=r_ip, port=r_port, username=r_user, password=r_pass, timeout=5) == 'pong':
                        return d_ip, d_port, d_user, d_pass
                    else:
                        xbmcgui.Dialog().ok('Remote Downloader', "Error: please specify the correct IP address for this system")
                        sys.exit()

        # no remote Kodi systems available ==> download it locally?
        if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'If remote unavailable':
            return None, None, None, None
        else:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: no Kodi system available for downloading')
            sys.exit()
