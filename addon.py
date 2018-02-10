"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.



    **Acknowledgments**

    This code is based largely upon:

        Simple XBMC Download Script
        Copyright (C) 2013 Sean Poyser (seanpoyser@gmail.com)

    I also used the "Simple Python Script To Control XBMC via Web/JSON API"
    from SleepyP (http://forum.kodi.tv/showthread.php?tid=197645)

"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import os
import sys
import urllib

from resources.lib import autoexec_functions
from resources.lib import download
from resources.lib import helper_functions
from resources.lib import jsonrpc_functions
from resources.lib import menu
from resources.lib import modify_addons
from resources.lib import name_functions
from resources.lib import now_playing
from resources.lib import tracking


# reset '0.0.0.0' IP addresses
for ip_address in ['local_ip_address'] + ['remote_ip_address{0}'.format(i+1) for i in range(5)]:
    if xbmcaddon.Addon('script.remote_downloader').getSetting(ip_address) == '0.0.0.0':
        xbmcaddon.Addon('script.remote_downloader').setSetting(ip_address, '')


if __name__ == "__main__":
    """Download a stream to this Kodi or a remote Kodi

    There are 2 systems involved (and it could be the same Kodi system for both):

    1. The **requesting system** is the Kodi system that first calls Remote Downloader
    2. The **downloading system** is the Kodi system that will download the file

    Values for `action`:

    * (no parameters provided)) -- Modify addons and exit
    * `'modify_addons_silent'` -- Modify addons silently and exit
    * `'update_addons'` -- Update addons and exit
    * `'download_now_playing'` -- Get info for the current video and proceed to download it
    * `'prepare_download'` -- Prepare to download a stream
    * `'request_download'` -- Send a message to the requesting system to confirm or cancel the download
    * `'confirm_download'` -- Send a message telling the downloading system to download the stream
    * `'download'` -- Download the stream

    """
    # if a "title_regex_substitutions.txt" file doesn't exist, create it
    title_regex_substitutions = 'special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'
    if not xbmcvfs.exists(title_regex_substitutions):
        with open(xbmc.translatePath(title_regex_substitutions), 'w') as f:
            f.write(r'# enter regular expressions here\n# EXAMPLE: re.sub(r"^Old Title (S[0-9]+\s?E[0-9]+)\Z", r"New Title \1", title)')

    # ================================================== #
    #                                                    #
    #                        Menu                        #
    #                                                    #
    # ================================================== #
    if len(sys.argv) == 1:
        """Display a menu
        
        """
        menu.menu()
        
    # get the `params`
    params = jsonrpc_functions.from_jsonrpc(', '.join(sys.argv[1:]))
    action = params.get('action')

    # ================================================== #
    #                                                    #
    #                 0. Simple actions                  #
    #                                                    #
    # ================================================== #
    if action == 'modify_addons':
        """Modify addons and exit
        
        """
        modify_addons.modify_addons()
        sys.exit()
        
    if action == 'modify_addons_silent':
        """Modify addons silently and exit

        """
        modify_addons.modify_addons(msg_fmt='notification')
        sys.exit()

    if action == 'update_addons':
        """Update addons and exit

        """
        xbmc.executebuiltin('UpdateAddonRepos')
        sys.exit()

    if action == 'library_clean':
        """Clean the video library and exit

        """
        jsonrpc_functions.jsonrpc('VideoLibrary.Clean')
        sys.exit()

    if action == 'library_scan':
        """Scan the video library and exit

        """
        jsonrpc_functions.jsonrpc('VideoLibrary.Scan')
        sys.exit()

    if action == 'restart_upnp':
        """Restart the remote UPnP server

        """
        d_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address1')
        d_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port1')
        
        if d_ip and d_port:
            d_user = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username1')
            d_pass = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password1')
            
            method = 'Settings.SetSettingValue'
            params = {'setting': 'services.upnpserver', 'value':False}
            result = jsonrpc_functions.jsonrpc(method, params, ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
            params = {'setting': 'services.upnpserver', 'value':True}
            result = jsonrpc_functions.jsonrpc(method, params, ip=d_ip, port=d_port, username=d_user, password=d_pass, timeout=5)
            
        sys.exit()
    
    if action == 'get_downloads':
        """Get a string of the current download(s) and their progress from the downloading system
        
        """        
        d_ip, d_port, d_user, d_pass, r_ip, r_port, r_user, r_pass = helper_functions.get_system_addresses()
        tracking.get_downloads(d_ip, d_port, d_user, d_pass, r_ip, r_port, r_user, r_pass)
        sys.exit()
    
    if action == 'get_local_downloads':
        """Get a string of the current download(s) and their progress from this system
        
        """
        r_ip = params.get('r_ip')
        r_port = params.get('r_port')
        r_user = params.get('r_user')
        r_pass = params.get('r_pass')
        tracking.get_local_downloads(r_ip, r_port, r_user, r_pass)
        sys.exit()
    
    if action == 'show_downloads':
        """Show the current download(s) and their progress
        
        """
        download_string = params.get('download_string')
        tracking.show_downloads(download_string)
        sys.exit()
        
    if action == 'add_regex_substitution':
        """Add a regex substitution to `title_regex_substitutions.txt`
        
        """
        old = params.get('old')
        new = params.get('new')
        if old and new:
            name_functions.add_substitution(old, new)
        sys.exit()
        
    if action == 'autoexec_add_remove':
        """Add or remove 'Restart remote UPnP server' from `autoexec.py`
        
        """
        autoexec_functions.autoexec_add_remove(params.get('autoexec_opt'))
        sys.exit()
        
    if action == 'dialog_ok':
        """Show an `xbmcgui.Dialog().ok` message
        
        """
        heading = params.get('heading')
        line = params.get('line')
        xbmcgui.Dialog().ok(heading, line)
        
    if action == 'save_jsonrpc_url':
        """Save a 'prepare_download' URL that can be used to initiate a download
        
        """
        title = name_functions.get_title(params.get('title'))
        url = params.get('url')
        url_redirect = params.get('url_redirect')
        image = params.get('image')
        bytesize = params.get('bytesize')
        basename = params.get('basename')
        
        _params = {'action': 'prepare_download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize}
        
        links_dir = xbmc.translatePath('special://userdata/addon_data/script.remote_downloader/Links')
        if not xbmcvfs.exists(links_dir):
            xbmcvfs.mkdirs(links_dir)
            
        outfile = os.path.join(links_dir, os.path.splitext(basename)[0] + '.txt')
        if xbmcvfs.exists(outfile):
            i = 2
            while True:
                if not xbmcvfs.exists(outfile[:-4] + ' ({0}).txt'.format(i)):
                    outfile = outfile[:-4] + ' ({0}).txt'.format(i)
                    break
                else:
                    i += 1
        
        port = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverport"}}'))['result']['value']
        with open(outfile, 'w') as f:
            f.write('http://localhost:' + str(port) + '/jsonrpc?request={"jsonrpc":"2.0","id":1,"method":"Addons.ExecuteAddon","params":{"addonid":"script.remote_downloader","params":"' + urllib.quote_plus(str(_params)) + '"}}')

        sys.exit()
        

    # ================================================== #
    #                                                    #
    #              1. Download now playing               #
    #                                                    #
    # ================================================== #
    if action == 'download_now_playing':
        """Get info for the current video and proceed to download it

        Requesting system

        Returns
        -------
        action : str
            'prepare_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes

        """
        title, url, url_redirect, image, bytesize = now_playing.process_now_playing()

        # download the current video
        params = {'action': 'prepare_download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize}
        method = 'Addons.ExecuteAddon'
        result = jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader')
        sys.exit()

    # ================================================== #
    #                                                    #
    #                2. Prepare download                 #
    #                                                    #
    # ================================================== #
    if action == 'prepare_download':
        """Prepare to download a stream

        Requesting system --> Downloading system

        Parameters
        ----------
        action : str
            'prepare_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes (if downloading the "now playing" stream)

        Returns
        -------
        action : str
            'request_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)

        """
        title = name_functions.get_title(params.get('title'))
        url = params.get('url')
        url_redirect = params.get('url_redirect')
        image = params.get('image')
        bytesize = params.get('bytesize')

        # if there is no url, exit
        if url is None:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: there is no stream')
            sys.exit()

        # determine whether the file can be downloaded
        if bytesize is None:
            resp, bytesize, _ = helper_functions.resp_bytesize_resumable(url)
            if bytesize is None:
                sys.exit()
            url_redirect = resp.geturl()
            if url_redirect == url:
                url_redirect = None

        # if the file is < 1 MB, show an error message and stop
        if bytesize < 1024 * 1024:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: video is 0 MB')
            sys.exit()

        # identify the requesting and downloading systems
        d_ip, d_port, d_user, d_pass, r_ip, r_port, r_user, r_pass = helper_functions.get_system_addresses()
        
        # send a download request to the downloading system
        method = 'Addons.ExecuteAddon'
        params = {'action': 'request_download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize,
                  'd_ip': d_ip, 'd_port': d_port, 'd_user': d_user, 'd_pass': d_pass,
                  'r_ip': r_ip, 'r_port': r_port, 'r_user': r_user, 'r_pass': r_pass}
        
        result = jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader', d_ip, d_port, d_user, d_pass)
        sys.exit()

    # ================================================== #
    #                                                    #
    #                 3. Download request                #
    #                                                    #
    # ================================================== #
    if action == 'request_download':
        """Send a message to the requesting system to confirm or cancel the download

        Downloading system --> requesting system

        Parameters
        ----------
        action : str
            'request_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)

        Returns
        -------
        action : str
            'confirm_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        basename : str
            the name of the file to be created
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)

        """
        title = name_functions.get_title(params.get('title'))
        url = params.get('url')
        url_redirect = params.get('url_redirect')
        image = params.get('image')
        bytesize = params.get('bytesize')

        # info about the downloading Kodi system
        d_ip = params.get('d_ip')
        d_port = params.get('d_port')
        d_user = params.get('d_user')
        d_pass = params.get('d_pass')

        # info about the requesting Kodi system
        r_ip = params.get('r_ip')
        r_port = params.get('r_port')
        r_user = params.get('r_user')
        r_pass = params.get('r_pass')

        # the JSON-RPC method
        method = 'Addons.ExecuteAddon'

        # get the name of the file to be created
        dest, _ = name_functions.get_dest(title, url)
        if isinstance(dest, str):
            # `dest` is a string --> get the basename
            basename = os.path.basename(dest)
        else:
            # `dest` is an integer --> it is an error code
            basename = dest

        if d_ip:
            params = {'action': 'confirm_download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize, 'basename': basename,
                      'd_ip': d_ip, 'd_port': d_port, 'd_user': d_user, 'd_pass': d_pass,
                      'r_ip': r_ip, 'r_port': r_port, 'r_user': r_user, 'r_pass': r_pass}
            jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)

        else:
            params = {'action': 'confirm_download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize, 'basename': basename}
            jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader')

        sys.exit()

    # ================================================== #
    #                                                    #
    #              4. Download confirmation              #
    #                                                    #
    # ================================================== #
    if action == 'confirm_download':
        """Send a message telling the downloading system to download the stream

        Requesting system --> downloading system

        Parameters
        ----------
        action : str
            'confirm_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        basename : str
            the name of the file to be created
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)

        Returns
        -------
        action : str
            'download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)
        track : bool
            whether or not to track the download progress

        """
        title = params.get('title')
        url = params.get('url')
        url_redirect = params.get('url_redirect')
        image = params.get('image')
        bytesize = params.get('bytesize')
        basename = params.get('basename')

        # info about the downloading Kodi system
        d_ip = params.get('d_ip')
        d_port = params.get('d_port')
        d_user = params.get('d_user')
        d_pass = params.get('d_pass')

        # info about the requesting Kodi system
        r_ip = params.get('r_ip')
        r_port = params.get('r_port')
        r_user = params.get('r_user')
        r_pass = params.get('r_pass')
        
        # track the download progress?
        track = xbmcaddon.Addon('script.remote_downloader').getSetting('track_downloads') == 'true'

        # make sure the download paths are configured correctly
        if basename == 1:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: movies download folder not setup in Remote Downloader settings')
            sys.exit()
        if basename == 2:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: TV download folder not setup in Remote Downloader settings')
            sys.exit()

        # get the name of the downloading Kodi system
        _params = {"labels": ["System.FriendlyName"]}
        _method = "XBMC.GetInfoLabels"
        if d_ip:
            kodi_name = jsonrpc_functions.jsonrpc(_method, _params, None, d_ip, d_port, d_user, d_pass)['System.FriendlyName']
        else:
            kodi_name = jsonrpc_functions.jsonrpc(_method, _params)['System.FriendlyName']

        # the size of the file to be created
        mbsize = bytesize / (1024 * 1024)

        if xbmcgui.Dialog().yesno('Remote Downloader', basename, 'Complete file is {0} MB'.format(mbsize),
                                  'Download to {0}?'.format(kodi_name), 'Confirm',  'Cancel') == 0:
            method = 'Addons.ExecuteAddon'

            if d_ip:
                params = {'action': 'download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize, 'track': track,
                          'd_ip': d_ip, 'd_port': d_port, 'd_user': d_user, 'd_pass': d_pass,
                          'r_ip': r_ip, 'r_port': r_port, 'r_user': r_user, 'r_pass': r_pass}
                jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader', d_ip, d_port, d_user, d_pass)
            else:
                params = {'action': 'download', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize, 'track': track}
                jsonrpc_functions.jsonrpc(method, params, 'script.remote_downloader')

            # for saving the JSON-RPC URL
            _params = {'action': 'save_jsonrpc_url', 'title': title, 'url': url, 'url_redirect': url_redirect, 'image': image, 'bytesize': bytesize, 'basename': basename}
            
            # save the JSON-RPC URL to this system?
            if xbmcaddon.Addon('script.remote_downloader').getSetting('save_jsonrpc_url') == 'true':
                result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', _params, 'script.remote_downloader')
                    
            # save the JSON-RPC URL to remote systems?
            for i in range(5):
                if xbmcaddon.Addon('script.remote_downloader').getSetting('save_jsonrpc_url{0}'.format(i)) == 'true':
                    ip_address = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address{0}'.format(i))            
                    port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port{0}'.format(i+1))
                    username = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username{0}'.format(i+1))
                    password = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password{0}'.format(i+1))
                    result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', _params, 'script.remote_downloader', ip_address, port, username, password)

        sys.exit()

    # ================================================== #
    #                                                    #
    #                      5. Download                   #
    #                                                    #
    # ================================================== #
    if action == 'download':
        """Download the stream

        Downloading system

        Parameters
        ----------
        action : str
            'download'
        title : str
            title of the stream
        url : str
            URL for the stream
        url_redirect : str
            (possibly) redirected URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)
        track : bool
            whether or not to track the download progress

        """
        title = name_functions.get_title(params.get('title'))
        url = params.get('url')
        url_redirect = params.get('url_redirect')
        image = params.get('image')
        bytesize = params.get('bytesize')

        # info about the downloading Kodi system
        d_ip = params.get('d_ip')
        d_port = params.get('d_port')
        d_user = params.get('d_user')
        d_pass = params.get('d_pass')

        # info about the requesting Kodi system
        r_ip = params.get('r_ip')
        r_port = params.get('r_port')
        r_user = params.get('r_user')
        r_pass = params.get('r_pass')
        
        # track the download progress?
        track = params.get('track')
            
        d = download.Download(title, url, url_redirect, image, bytesize, r_ip, r_port, r_user, r_pass, track)
        d.download()

