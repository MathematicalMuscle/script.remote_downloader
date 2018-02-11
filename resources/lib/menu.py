"""Display a menu

"""

import xbmc
import xbmcaddon
import xbmcgui

import sys

from . import autoexec_functions
from . import jsonrpc_functions
from . import modify_addons
from . import name_functions


def menu():
    """Display a menu
    
    """
    autoexec_opt = autoexec_functions.get_autoexec_opt()
    
    if xbmc.Player().isPlayingVideo():
        opts = ['Download current video']
    else:
        opts = []
        
    if xbmcaddon.Addon('script.remote_downloader').getSetting('track_downloads') == 'true':
        opts += ['View download progress']
        
    opts += ['Modify addons',
             'Clean remote video library',
             'Update remote video library',
             'Update remote addons',
             # 'Add a title regex substitution',
             autoexec_opt,
             'Restart remote UPnP server']

    len_opts = len(opts)
             
    select = xbmcgui.Dialog().select('Remote Downloader', opts, 0)
    if select >= 0:
        selection = opts[select]
        if selection == 'Download current video':
            # download the current video
            params = {'action': 'download_now_playing'}
            method = 'Addons.ExecuteAddon'
            result = jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()
            
        elif selection == 'View download progress':
            params = {'action': 'get_downloads'}            
            method = 'Addons.ExecuteAddon'
            result = jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()
        
        elif selection == 'Modify addons':
            modify_addons.modify_addons()
            sys.exit()
            
        elif selection == 'Restart remote UPnP server':
            # restart the remote UPnP server                
            params = {'action': 'restart_upnp'}
            method = 'Addons.ExecuteAddon'
            result = jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()
            
        elif selection == 'Add a title regex substitution':
            name_functions.add_substitution()
            sys.exit()
        
        elif selection == autoexec_opt:
            autoexec_functions.autoexec_add_remove(autoexec_opt)
            sys.exit()
            
        else:
            # get info about the remote Kodi
            d_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address1')
            d_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port1')
            d_user = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username1')
            d_pass = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password1')
            
            if not d_ip:
                sys.exit()
                
            if selection == 'Clean remote video library':
                # clean the remote video library
                result = jsonrpc_functions.jsonrpc(method='VideoLibrary.Clean', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
            
            elif selection == 'Update remote video library':
                # scan the remote video library
                result = jsonrpc_functions.jsonrpc(method='VideoLibrary.Scan', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
            
            elif selection == 'Update remote addons':
                # update addons on the remote system
                method = 'Addons.ExecuteAddon'
                params = {'action': 'update_addons'}
                result = jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader', ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
                sys.exit()
    
    else:
        sys.exit()

