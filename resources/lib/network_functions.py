"""Some helper functions

"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import functools
import httplib
import socket
import sys
import urllib2
import urlparse

from . import jsonrpc_functions


class BoundHTTPHandler(urllib2.HTTPHandler):
    """https://stackoverflow.com/a/14669175
    
    """
    def __init__(self, source_address=None, debuglevel=0):
        urllib2.HTTPHandler.__init__(self, debuglevel)
        self.http_class = functools.partial(httplib.HTTPConnection, source_address=source_address)

    def http_open(self, req):
        return self.do_open(self.http_class, req)


class BoundHTTPSHandler(urllib2.HTTPSHandler):
    """https://stackoverflow.com/a/14669175
    
    """
    def __init__(self, source_address=None, debuglevel=0):
        urllib2.HTTPSHandler.__init__(self, debuglevel)
        self.https_class = functools.partial(httplib.HTTPSConnection, source_address=source_address)

    def https_open(self, req):
        return self.do_open(self.https_class, req)


def get_opener(url0, r_ip):
    """Return an HTTP/HTTPS opener
    
    """
    if url0.startswith('https'):
        handler = BoundHTTPSHandler(source_address=(r_ip, 0))
    else:
        handler = BoundHTTPSHandler(source_address=(r_ip, 0))
    
    return urllib2.build_opener(handler)


def get_url0(url):
    """Get the portion of the URL before the first "|"
    
    """
    return url.split('|')[0]


def get_headers(url):
    """Get the headers from the URL
    
    """
    try:
        headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict()
    return headers


def open(url, url_redirect=None, headers=None, size=0, r_ip=None, r_port=None, r_user=None, r_pass=None):
    """Open the URL and get info about the file size and whether the download is resumable
    
    """
    original_headers = headers

    for i, u in enumerate([url, url, url_redirect, url_redirect, None]):
        # Error: no response from server
        if u is None:
            params = {'action': 'dialog_ok', 'line': 'Error: no response from server', 'heading': 'Remote Downloader'}
            result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
            return None, None, None, None
            
        if i % 2 == 1 and r_ip is None:
            continue

        # get the portion of the URL before the first "|"
        url0 = get_url0(u)
        
        # get the headers if they were not provided as an input
        if original_headers is None:
            headers = get_headers(u)

        # the first byte to start at
        if size > 0:
            headers['Range'] = 'bytes={0}-'.format(int(size))
            
        try:
            xbmc.log('{0}) BEFORE:  '.format(i+1) + str(headers), xbmc.LOGNOTICE)
            req = urllib2.Request(url0, headers=headers)
            headers = dict(req.header_items())
            xbmc.log('{0}) AFTER Request:  '.format(i+1) + str(headers), xbmc.LOGNOTICE)
            if i % 2 == 0:
                resp = urllib2.urlopen(req, timeout=30)
            else:
                resp = get_opener(url0, r_ip).open(req, timeout=30)
            #headers = dict(resp.headers)
            #xbmc.log('{0}) AFTER urlopen:  '.format(i+1) + str(headers), xbmc.LOGNOTICE)
            break
        except:
            pass

    try:
        bytesize = int(resp.headers['Content-Length'])
    except:
        params = {'action': 'dialog_ok', 'line': 'Error: unknown filesize', 'heading': 'Remote Downloader'}
        result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
        return None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    return resp, bytesize, headers, resumable


def test_ip_address(ip, port, username, password, timeout=5):
    """Verify that there is a Kodi system at the provided IP address
    
    """
    return jsonrpc_functions.jsonrpc(method='JSONRPC.Ping', ip=ip, port=port, username=username, password=password, timeout=timeout) == 'pong'
    

def get_this_system():
    """Get this system's local IP address, along with port, username, and password
    
    """
    port = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverport"}}'))['result']['value']
    username = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverusername"}}'))['result']['value']
    password = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverpassword"}}'))['result']['value']
    
    # get the IP address from the Remote Downloader "local_ip_address" setting
    ip = xbmcaddon.Addon('script.remote_downloader').getSetting('local_ip_address')
    if ip not in ['', '0.0.0.0']:
        if test_ip_address(ip, port, username, password):
            return ip, port, username, password
        
    # https://stackoverflow.com/a/25850698
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    ip = s.getsockname()[0]
    if test_ip_address(ip, port, username, password):
        return ip, port, username, password
        
    # get the IP address from the Kodi function
    ip = xbmc.getIPAddress()
    timeout = int(xbmcaddon.Addon('script.remote_downloader').getSetting('max_wait_time'))
    if test_ip_address(ip, port, username, password, timeout=timeout):
        return ip, port, username, password
        
    # failed to get IP address
    xbmcgui.Dialog().ok('Remote Downloader', "Error: please specify the correct IP address for this system")
    sys.exit()


def get_system_addresses():
    """For the requesting and downloading systems, get: IP address, port, username, & password
    
    """
    if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'Yes':
        return None, None, None, None, None, None, None, None
    
    else:
        timeout = int(xbmcaddon.Addon('script.remote_downloader').getSetting('max_wait_time'))
        r_ip, r_port, r_user, r_pass = None, None, None, None
        
        for i in range(5):
            # get info about the downloading Kodi system
            d_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address{0}'.format(i+1))
            d_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port{0}'.format(i+1))
            d_user = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username{0}'.format(i+1))
            d_pass = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password{0}'.format(i+1))

            if d_ip:
                # get the requesting system's info (but only do so once!)
                if r_ip is None:
                    r_ip, r_port, r_user, r_pass = get_this_system()
                    
                # check that the remote system is available
                if test_ip_address(ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=timeout):
                    return d_ip, d_port, d_user, d_pass, r_ip, r_port, r_user, r_pass

        # no remote Kodi systems available ==> download it locally?
        if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'If remote unavailable':
            return None, None, None, None, None, None, None, None
        else:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: no Kodi system available for downloading')
            sys.exit()

