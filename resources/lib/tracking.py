import glob
import os
import time

import xbmc
import xbmcgui
import xbmcvfs

from . import helper_functions
from . import json_functions


def get_downloads(d_ip, d_port, d_user, d_pass, r_ip, r_port, r_user, r_pass):
    params = {'action': 'get_local_downloads',
              'r_ip': r_ip, 'r_port': r_port, 'r_user': r_user, 'r_pass': r_pass}
    method = 'Addons.ExecuteAddon'
    result = json_functions.jsonrpc(method, params, 'script.remote_downloader', d_ip, d_port, d_user, d_pass)


def get_local_downloads(r_ip, r_port, r_user, r_pass):
    download_folder = xbmc.translatePath('special://userdata/addon_data/script.remote_downloader/downloads/')
    download_txts = sorted(glob.glob(os.path.join(download_folder, '*.txt')))
    
    active_downloads = []
    
    uptime = get_uptime()
        
    for txt in download_txts:
        with open(txt, 'r') as f:
            start_time, progress = f.readlines()
            
        if time.time() - float(start_time) > uptime:
            xbmcvfs.delete(txt)
        else:
            active_downloads.append(progress)
        
    params = {'action': 'show_downloads', 'download_string': '\n'.join(active_downloads)}
    method = 'Addons.ExecuteAddon'
    result = json_functions.jsonrpc(method, params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)


def show_downloads(download_string):
    if download_string == '':
        xbmcgui.Dialog().ok('Remote Downloader', 'No active downloads')
    else:
        xbmcgui.Dialog().textviewer('Remote Downloader', download_string)


def get_uptime():
    # get the time that the system has been running
    uptime = 'Busy'
    while uptime == 'Busy':
        uptime = xbmc.getInfoLabel('System.UpTime')
    uptime = uptime.replace(',', '')
    
    # convert it to seconds
    uptime = uptime.lower().replace(',', '').replace('days', 'day').replace('hours', 'hour').replace('minutes', 'minute')
    uptime = uptime.replace('day', str(24.*3600)).replace('hour', '3600.').replace('minute', '60.')
    uptime_list = uptime.split()
    uptime = sum([float(uptime_list[i]) * float(uptime_list[i+1]) for i in range(0, len(uptime_list), 2)])
    
    return uptime + 60.
    
