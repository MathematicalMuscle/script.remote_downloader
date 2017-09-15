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

import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import urlparse

from resources.lib import helper_functions
from resources.lib import json_functions
from resources.lib import name_functions
from resources.lib import now_playing
from resources.lib import simple
from resources.lib.modify_addons import modify_addons


# info about this system
ip = xbmcaddon.Addon('script.remote_downloader').getSetting('local_ip_address')
if not ip:
    ip = xbmc.getIPAddress()
port = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverport"}, "id":1}'))['result']['value']
username = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverusername"}, "id":1}'))['result']['value']
password = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverpassword"}, "id":1}'))['result']['value']


if __name__ == "__main__":
    """Download a stream to this Kodi or a remote Kodi

    There are 2 systems involved (and it could be the same Kodi system for both):

    1. The **requesting system** is the Kodi system that first calls Remote Downloader
    2. The **downloading system** is the Kodi system that will download the file

    Values for `action`:

    * `None` -- `modify_addons()`
    * `'modify_addons_silent'` -- `modify_addons(msg_fmt='notification')`
    * `'download_now_playing'` -- the requesting system will get info about the current stream
    * `'prepare_download'` -- the requesting system sends the inputs (`title`, `image`, `url`) to the downloading
      system, which processes them and sends a confirmation message to the requesting system
    * `'confirm_download'` -- the downloading system sends a message to the requesting system, which replies with a
      message indicating whether or not to download the file
    * `'download'` -- download the stream on the downloading system

    """
    # if a "title_regex_substitutions.txt" file doesn't exist, create it
    title_regex_substitutions = 'special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'
    if not xbmcvfs.exists(title_regex_substitutions):
        with open(xbmc.translatePath(title_regex_substitutions), 'w') as f:
            f.write('# enter regular expressions here\n# EXAMPLE: re.sub(r"^Old Title (S[0-9]+\s?E[0-9]+)\\Z", r"New Title \\1", s)')

    # ================================================== #
    #                                                    #
    #                  0. Modify addons                  #
    #                                                    #
    # ================================================== #
    if len(sys.argv) == 1:
        """Modify addons and exit

        """
        modify_addons()
        sys.exit()

    # get the `params`
    params = json_functions.from_jsonrpc(sys.argv[1])
    action = params.get('action')

    # ================================================== #
    #                                                    #
    #                  0.1 Update addons                 #
    #                                                    #
    # ================================================== #
    if action == 'update_addons':
        """Update addons and exit

        """
        xbmc.executebuiltin('UpdateAddonRepos')
        sys.exit()

    # ================================================== #
    #                                                    #
    #             1. Modify addons silently              #
    #                                                    #
    # ================================================== #
    if action == 'modify_addons_silent':
        """Modify addons silently and exit

        """
        modify_addons(msg_fmt='notification')
        sys.exit()

    # ================================================== #
    #                                                    #
    #              2. Download now playing               #
    #                                                    #
    # ================================================== #
    if action == 'download_now_playing':
        """Get info for the current video and download it

        Requesting system

        Returns
        -------
        action : str
            'prepare_download'
        title : str
            title of the stream
        url : str
            URL for the stream
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes

        """
        title, url, image, bytesize = now_playing.process_now_playing()

        # download the current video
        params = {'action': 'prepare_download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize}
        method = 'Addons.ExecuteAddon'
        result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
        sys.exit()

    # ================================================== #
    #                                                    #
    #                3. Prepare download                 #
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
        image : str
            image for the stream
        bytesize : int
            file size of the download in bytes
        r_ip : str
            requesting system IP address (if downloading remotely)
        r_port : str
            requesting system port (if downloading remotely)
        r_user : str
            requesting system username (if downloading remotely)
        r_pass : str
            requesting system password (if downloading remotely)
        d_ip : str
            downloading system IP address (if downloading remotely)
        d_port : str
            downloading system port (if downloading remotely)
        d_user : str
            downloading system username (if downloading remotely)
        d_pass : str
            downloading system password (if downloading remotely)

        """
        title = name_functions.get_title(params.get('title'))
        url = params.get('url')
        image = params.get('image')
        bytesize = params.get('bytesize')

        # if there is no url, exit
        if url is None:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: there is no stream')
            sys.exit()

        # derived parameters
        url0 = simple.get_url0(url)
        headers = simple.get_headers(url)

        # determine whether the file can be downloaded
        if bytesize is None:
            _, bytesize, _ = helper_functions.resp_bytesize_resumable(url, headers)
            if bytesize is None:
                sys.exit()

        # if the file is < 1 MB, show an error message and stop
        if bytesize < 1024 * 1024:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: video is 0 MB')
            sys.exit()

        # JSON-RPC arguments
        method = 'Addons.ExecuteAddon'

        # send a download request to the downloading system
        if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'Yes':
            params = {'action': 'request_download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize}
            result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()

        else:
            for i in range(5):
                # get info about the downloading Kodi system
                d_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address{0}'.format(i+1))
                d_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port{0}'.format(i+1))
                d_user = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username{0}'.format(i+1))
                d_pass = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password{0}'.format(i+1))

                if d_ip:
                    params = {'action': 'request_download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize,
                              'd_ip': d_ip, 'd_port': d_port, 'd_user': d_user, 'd_pass': d_pass,
                              'r_ip': ip, 'r_port': port, 'r_user': username, 'r_pass': password}

                    result = json_functions.jsonrpc(method, params, 'script.remote_downloader', d_ip, d_port, d_user, d_pass)
                    if result == 'OK':
                        sys.exit()

            # no remote Kodi systems available ==> download it locally?
            if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'If remote unavailable':
                params = {'action': 'request_download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize}

                result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
                sys.exit()

        xbmcgui.Dialog().ok('Remote Downloader', 'Error: no Kodi system available for downloading')
        sys.exit()

    # ================================================== #
    #                                                    #
    #                 4. Download request                #
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

        """
        title = name_functions.get_title(params.get('title'))
        url = params.get('url')
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
        dest, _ = name_functions.get_dest(title, url, make_directories=False)
        if isinstance(dest, str):
            # `dest` is a string --> get the basename
            basename = os.path.basename(dest)
        else:
            # `dest` is an integer --> it is an error code
            basename = dest

        if d_ip:
            params = {'action': 'confirm_download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize, 'basename': basename,
                      'd_ip': d_ip, 'd_port': d_port, 'd_user': d_user, 'd_pass': d_pass}
            json_functions.jsonrpc(method, params, 'script.remote_downloader', r_ip, r_port, r_user, r_pass)

        else:
            params = {'action': 'confirm_download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize, 'basename': basename}
            json_functions.jsonrpc(method, params, 'script.remote_downloader')

        sys.exit()

    # ================================================== #
    #                                                    #
    #              5. Download confirmation              #
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

        Returns
        -------
        action : str
            'download'
        title : str
            title of the stream
        url : str
            URL for the stream
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
        title = params.get('title')
        url = params.get('url')
        image = params.get('image')
        bytesize = params.get('bytesize')
        basename = params.get('basename')

        # info about the downloading Kodi system
        d_ip = params.get('d_ip')
        d_port = params.get('d_port')
        d_user = params.get('d_user')
        d_pass = params.get('d_pass')

        # info about the requesting Kodi system
        r_ip = ip
        r_port = port
        r_user = username
        r_pass = password

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
            kodi_name = json_functions.jsonrpc(_method, _params, None, d_ip, d_port, d_user, d_pass)['System.FriendlyName']
        else:
            kodi_name = json_functions.jsonrpc(_method, _params)['System.FriendlyName']

        # the size of the file to be created
        mbsize = bytesize / (1024 * 1024)

        if xbmcgui.Dialog().yesno('Remote Downloader', basename, 'Complete file is {0} MB'.format(mbsize),
                                  'Download to {0}?'.format(kodi_name), 'Confirm',  'Cancel') == 0:
            method = 'Addons.ExecuteAddon'

            if d_ip:
                params = {'action': 'download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize,
                          'd_ip': d_ip, 'd_port': d_port, 'd_user': d_user, 'd_pass': d_pass,
                          'r_ip': r_ip, 'r_port': r_port, 'r_user': r_user, 'r_pass': r_pass}
                json_functions.jsonrpc(method, params, 'script.remote_downloader', d_ip, d_port, d_user, d_pass)
            else:
                params = {'action': 'download', 'title': title, 'url': url, 'image': image, 'bytesize': bytesize}
                json_functions.jsonrpc(method, params, 'script.remote_downloader')

        sys.exit()

    # ================================================== #
    #                                                    #
    #                      6. Download                   #
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

        # determine whether the file can be downloaded
        headers = simple.get_headers(url)
        mbsize = bytesize / (1024 * 1024)
        resp, _, resumable = helper_functions.resp_bytesize_resumable(url, headers)
        dest, temp_dest = name_functions.get_dest(title, url)

        if resp is None or dest is None:
            sys.exit()

        # the name of the file to be created
        basename = os.path.basename(dest)
        basename = basename.split('.')
        basename = '.'.join(basename[:-1])

        # download-tracking variables
        total = 0
        notify = 0
        errors = 0
        count = 0
        resume = 0
        sleep = 0

        f = xbmcvfs.File(temp_dest, 'w')

        chunk = None
        chunks = []

        while True:
            downloaded = total
            for c in chunks:
                downloaded += len(c)
            percent = min(100 * downloaded / bytesize, 100)
            if percent >= notify:
                # show a notification of the download progress
                if image:
                    xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format(str(percent) + '% - ' + basename, dest, 10000, image))
                else:
                    xbmc.executebuiltin("XBMC.Notification({0},{1},{2})".format(str(percent) + '% - ' + basename, dest, 10000))

                # send a notification to the Kodi that sent the download command
                if r_ip:
                    method = "GUI.ShowNotification"
                    if image:
                        _params = {'title': str(percent) + '% - ' + basename, 'message': dest, 'image': image, 'displaytime': 10000}
                    else:
                        _params = {'title': str(percent) + '% - ' + basename, 'message': dest, 'displaytime': 10000}
                    result = json_functions.jsonrpc(method, _params, None, r_ip, r_port, r_user, r_pass)

                notify += 10

            chunk = None
            error = False

            try:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    if percent < 99:
                        error = True
                    else:
                        while len(chunks) > 0:
                            c = chunks.pop(0)
                            f.write(c)
                            del c

                        f.close()
                        xbmc.log('script.remote_downloader: ' + '{0} download complete'.format(dest))

                        # if it was downloaded to a temporary location, move it
                        if temp_dest != dest:
                            xbmcvfs.rename(temp_dest, dest)

                        helper_functions.done(title, dest, True)

                        # update the library
                        method = "VideoLibrary.Scan"
                        update_downloading_library = json_functions.jsonrpc(method)
                        if r_ip:
                            update_requesting_library = json_functions.jsonrpc(method, None, None, r_ip, r_port, r_user, r_pass)

                        sys.exit()

            except Exception, e:
                xbmc.log('script.remote_downloader: ' + str(e))
                error = True
                sleep = 10
                errno = 0

                if hasattr(e, 'errno'):
                    errno = e.errno

                if errno == 10035: # 'A non-blocking socket operation could not be completed immediately'
                    pass

                if errno == 10054: #'An existing connection was forcibly closed by the remote host'
                    errors = 10 #force resume
                    sleep  = 30

                if errno == 11001: # 'getaddrinfo failed'
                    errors = 10 #force resume
                    sleep  = 30

            if chunk:
                errors = 0
                chunks.append(chunk)
                if len(chunks) > 5:
                    c = chunks.pop(0)
                    f.write(c)
                    total += len(c)
                    del c

            if error:
                errors += 1
                count  += 1
                xbmc.log('script.remote_downloader: ' + '{0} Error(s) whilst downloading {1}'.format(count, dest))
                xbmc.sleep(sleep*1000)

            if (resumable and errors > 0) or errors >= 10:
                if (not resumable and resume >= 50) or resume >= 500:
                    #Give up!
                    xbmc.log('script.remote_downloader: ' + '{0} download canceled - too many error whilst downloading'.format(dest))
                    helper_functions.done(title, dest, False)
                    sys.exit()

                resume += 1
                errors  = 0
                if resumable:
                    chunks  = []
                    #create new response
                    xbmc.log('script.remote_downloader: ' + 'Download resumed ({0}) {1}'.format(resume, dest))
                    resp, _, _ = helper_functions.resp_bytesize_resumable(url, headers, total)
                else:
                    #use existing response
                    pass
