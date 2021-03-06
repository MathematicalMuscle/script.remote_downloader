"""Some helper functions

"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import functools
import socket
import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    import http.client
    import urllib.request, urllib.error, urllib.parse
else:
    import httplib
    import urllib2
    import urlparse

from . import jsonrpc_functions


if not PY2:
    HTTPHandlerClass = urllib.request.HTTPHandler
    HTTPSHandlerClass = urllib.request.HTTPHandler
else:
    HTTPHandlerClass = urllib2.HTTPHandler
    HTTPSHandlerClass = urllib2.HTTPSHandler



class BoundHTTPHandler(HTTPHandlerClass):
    """https://stackoverflow.com/a/14669175
    
    """
    def __init__(self, source_address=None, debuglevel=0):
        if not PY2:
            urllib.request.HTTPHandler.__init__(self, debuglevel)
            self.http_class = functools.partial(http.client.HTTPConnection, source_address=source_address)
        else:
            urllib2.HTTPHandler.__init__(self, debuglevel)
            self.http_class = functools.partial(httplib.HTTPConnection, source_address=source_address)

    def http_open(self, req):
        return self.do_open(self.http_class, req)


class BoundHTTPSHandler(HTTPSHandlerClass):
    """https://stackoverflow.com/a/14669175
    
    """
    def __init__(self, source_address=None, debuglevel=0):
        if not PY2:
            urllib.request.HTTPSHandler.__init__(self, debuglevel)
            self.https_class = functools.partial(http.client.HTTPSConnection, source_address=source_address)
        else:
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

    if not PY2:
        return urllib.request.build_opener(handler)
    else:
        return urllib2.build_opener(handler)


def get_url0(url):
    """Get the portion of the URL before the first "|"
    
    """
    return url.split('|')[0]


def get_headers(url):
    """Get the headers from the URL
    
    """
    try:
        if not PY2:
            headers = dict(urllib.parse.parse_qsl(url.rsplit('|', 1)[1]))
        else:
            headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict()
    return headers


def open(url, url_redirect=None, headers=None, cookie=None, size=0, r_ip=None, r_port=None, r_user=None, r_pass=None):
    """Open the URL and get info about the file size and whether the download is resumable
    
    """
    original_headers = headers

    for i, u in enumerate([url, url, url, url, url, url_redirect, url_redirect, url_redirect, url_redirect, url_redirect, None]):
        # i % 5 == 0:  get the headers from the url
        # i % 5 == 1:  use the provided headers
        # i % 5 == 2:  use the provided headers + cookie
        # i % 5 == 3:  use the provided headers and the opener with the `source_address` argument
        # i % 5 == 4:  use the provided headers + cookie and the opener with the `source_address` argument
        # Error: no response from server
        if u is None:
            params = {'action': 'dialog_ok', 'line': 'Error: no response from server', 'heading': 'Remote Downloader'}
            result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
            return None, None, None, None, None
            
        if i % 5 > 2 and r_ip is None:
            continue

        # get the portion of the URL before the first "|"
        url0 = get_url0(u)
        xbmc.log('{0}) '.format(i+1) + u, xbmc.LOGNOTICE)
        
        # get the headers if they were not provided as an input
        if i % 5 == 0 or original_headers is None:
            headers = get_headers(u)
        else:
            headers = original_headers
        
        # use the provided cookie
        if cookie is not None and (i % 5 == 2 or i % 5 == 4):
            headers['Cookie'] = cookie

        # the first byte to start at
        if size > 0:
            headers['Range'] = 'bytes={0}-'.format(int(size))
            
        try:
            if not PY2:
                req = urllib.request.Request(url0, headers=headers)
            else:
                req = urllib2.Request(url0, headers=headers)

            if i % 5 < 3:
                if not PY2:
                    resp = urllib.request.urlopen(req, timeout=30)
                else:
                    resp = urllib2.urlopen(req, timeout=30)
            else:
                resp = get_opener(url0, r_ip).open(req, timeout=30)
                
            headers = dict(req.header_items())
            cookie = resp.headers.get('Set-Cookie')

            # log stuff on the requesting system
            log_str = '\n\nRemote Downloader ({0})  [{1}]\n---------------------\n'.format(i+1, 'this system' if r_ip is None else 'remote system')
            log_str += '* url:          {0}\n\n'.format(u)
            log_str += '* headers (1):  {0}\n\n'.format(str(dict(req.header_items())))
            log_str += '* headers (2):  {0}\n\n'.format(str(dict(resp.headers)))
            log_str += '* headers (3):  {0}\n\n'.format(str(headers))
            log_str += '* cookie:       {0}\n\n.'.format(str(cookie))
            params = {'action': 'log', 'log_str': log_str}
            result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
            
            #xbmc.log('{0}) '.format(i+1) + u, xbmc.LOGNOTICE)
            #xbmc.log('{0}) BEFORE headers:     '.format(i+1) + str(headers), xbmc.LOGNOTICE)
            #xbmc.log('{0}) `Request` headers:  '.format(i+1) + str(dict(req.header_items())), xbmc.LOGNOTICE)
            #xbmc.log('{0}) `urlopen` headers:  '.format(i+1) + str(dict(resp.headers)), xbmc.LOGNOTICE)
            #xbmc.log('{0}) RETURNED headers:   '.format(i+1) + str(headers), xbmc.LOGNOTICE)
            #xbmc.log('{0}) RETURNED cookie:    '.format(i+1) + str(cookie), xbmc.LOGNOTICE)
            break
        except:
            pass

    try:
        bytesize = int(resp.headers['Content-Length'])
    except:
        params = {'action': 'dialog_ok', 'line': 'Error: unknown filesize', 'heading': 'Remote Downloader'}
        result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
        return None, None, None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    return resp, bytesize, headers, cookie, resumable


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

