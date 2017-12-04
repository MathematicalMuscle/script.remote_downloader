"""Display a menu

"""

import sys
import xbmc
import xbmcaddon
import xbmcgui

from . import json_functions
from . import modify_addons


def menu():
    if xbmc.Player().isPlayingVideo():
        opts = ['Download current video']
    else:
        opts = []
        
    opts += ['Modify addons',
             'Clean remote video library',
             'Update remote video library',
             'Update remote addons',
             'Restart remote UPnP server']

    len_opts = len(opts)
             
    select = xbmcgui.Dialog().select('Remote Downloader', opts, 0)
    if select >= 0:
        if len_opts == 6 and select == 0:
            # download the current video
            params = {'action': 'download_now_playing'}
            method = 'Addons.ExecuteAddon'
            result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()
        
        elif select == len_opts - 5:
            modify_addons.modify_addons()
            sys.exit()
            
        elif select == len_opts - 1:
            # restart the remote UPnP server                
            params = {'action': 'restart_upnp'}
            method = 'Addons.ExecuteAddon'
            result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()
            
        else:
            # get info about the remote Kodi
            d_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address1')
            d_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port1')
            d_user = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username1')
            d_pass = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password1')
            
            if not d_ip:
                sys.exit()
                
            if select == len_opts - 4:
                # clean the remote video library
                result = json_functions.jsonrpc(method='VideoLibrary.Clean', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
            
            elif select == len_opts - 3:
                # scan the remote video library
                result = json_functions.jsonrpc(method='VideoLibrary.Scan', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
            
            elif select == len_opts - 2:
                # update addons on the remote system
                method = 'Addons.ExecuteAddon'
                params = {'action': 'update_addons'}
                result = json_functions.jsonrpc(method, params, 'script.remote_downloader', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
            
            elif select == len_opts - 1:
                # restart the remote UPnP server
                method = 'Settings.SetSettingValue'
                params = {'setting': 'services.upnpserver', 'value':False}
                result = json_functions.jsonrpc(method, params, ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                params = {'setting': 'services.upnpserver', 'value':True}
                result = json_functions.jsonrpc(method, params, ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
    
    else:
        sys.exit()
