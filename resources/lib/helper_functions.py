"""Some helper functions

"""

import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import socket
import urllib2
import urlparse

from . import json_functions


# variables relating to `autoexec.py`
autoexec = xbmc.translatePath('special://userdata/autoexec.py')
autoexec_import = 'import xbmc'
autoexec_command = 'xbmc.executebuiltin("RunAddon(script.remote_downloader, \\"{\'action\':\'restart_upnp\'}\\")")'
autoexec_str = autoexec_import + '\n\n' + autoexec_command


def get_url0(url):
    return url.split('|')[0]


def get_headers(url):
    try:
        headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict('')
    return headers


def resp_bytesize_resumable(url, url_redirect=None, size=0, r_ip=None, r_port=None, r_user=None, r_pass=None):
    try:
        headers = get_headers(url)
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes={0}-'.format(size)

        url0 = get_url0(url)
        req = urllib2.Request(url0, headers=headers)
        resp = urllib2.urlopen(req, timeout=30)

    except:
        try:
            headers = get_headers(url_redirect)
            if size > 0:
                size = int(size)
                headers['Range'] = 'bytes={0}-'.format(size)

            url0 = get_url0(url_redirect)
            req = urllib2.Request(url0, headers=headers)
            resp = urllib2.urlopen(req, timeout=30)
            
        except:
            params = {'action': 'dialog_ok', 'line': 'Error: no response from server', 'heading': 'Remote Downloader'}
            result = json_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
            return None, None, None

    try:
        bytesize = int(resp.headers['Content-Length'])
    except:
        params = {'action': 'dialog_ok', 'line': 'Error: unknown filesize', 'heading': 'Remote Downloader'}
        result = json_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)
        return None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    return resp, bytesize, resumable


def test_ip_address(ip, port, username, password, timeout=5):
    return json_functions.jsonrpc(method='JSONRPC.Ping', ip=ip, port=port, username=username, password=password, timeout=timeout) == 'pong'
    

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
    if test_ip_address(ip, port, username, password):
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
                if test_ip_address(ip=d_ip, port=d_port, username=d_user, password=d_pass):
                    return d_ip, d_port, d_user, d_pass, r_ip, r_port, r_user, r_pass

        # no remote Kodi systems available ==> download it locally?
        if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'If remote unavailable':
            return None, None, None, None, None, None, None, None
        else:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: no Kodi system available for downloading')
            sys.exit()
            

def autoexec_status():
    # determine whether or not 'Restart remote UPnP server' is already in `autoexec.py`
    if not xbmcvfs.exists(autoexec):
        return 'create' #autoexec_opt = 'Add \'Restart remote UPnP server\' to `autoexec.py`'
    else:
        with open(autoexec, 'r') as f:
            text = f.read()
        if autoexec_import not in text:
            return 'add_both'
        elif autoexec_command not in text:
            return 'add_command' #autoexec_opt = 'Add \'Restart remote UPnP server\' to `autoexec.py`'
        else:
            if text.strip() == autoexec_import + '\n\n' + autoexec_command:
                return 'delete_file'
            else:
                return 'delete_command'
            autoexec_opt = 'Remove \'Restart remote UPnP server\' from `autoexec.py`'
            if text == autoexec_str:
                autoexec_delete = True
            else:
                autoexec_delete = False


def autoexec_add_remove(add_remove=None):
    # add or remove 'Restart remote UPnP server' from `autoexec.py`
    status = autoexec_status()
    
    if add_remove == 'add':
        if status == 'create':
            with open(autoexec, 'w') as f:
                f.write(autoexec_import + '\n\n' + autoexec_command)
        elif status == 'add_both':
            with open(autoexec, 'a') as f:
                f.write(autoexec_import + '\n\n' + autoexec_command)
        elif status == 'add_command':
            with open(autoexec, 'a') as f:
                f.write(autoexec_command)
                
    elif add_remove == 'remove':
        if status == 'delete_file':
            xbmcvfs.delete(autoexec)
        else:
            with open(autoexec, 'r') as f:
                text = f.read()
                
            with open(autoexec, 'w') as f:
                f.write(text.replace(autoexec_command + '\n', '').replace(autoexec_command, ''))
        
