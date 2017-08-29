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
from resources.lib.modify_addons import modify_addons


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
        # modify addons and exit
        modify_addons()
        sys.exit()

    # get the `params`
    params = json_functions.from_jsonrpc(sys.argv[1])
    action = params.get('action')

    # ================================================== #
    #                                                    #
    #             1. Modify addons silently              #
    #                                                    #
    # ================================================== #
    if action == 'modify_addons_silent':
        # modify addons silently and exit
        modify_addons(msg_fmt='notification')
        sys.exit()

    # ================================================== #
    #                                                    #
    #              2. Download now playing               #
    #                                                    #
    # ================================================== #
    if action == 'download_now_playing':
        # get info for the current video and download it
        title, url, image = now_playing.process_now_playing()

        # download the current video
        params = {'title': title, 'url': url, 'image': image, 'action': 'prepare_download'}
        method = 'Addons.ExecuteAddon'
        result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
        sys.exit()

    # ================================================== #
    #                                                    #
    #                3. Prepare download                 #
    #                                                    #
    # ================================================== #
    if action == 'prepare_download':
        # provided parameters
        image = params.get('image')
        title = name_functions.title_substitutions(params.get('title'))
        url = params.get('url')

        # if there is no url, exit
        if url is None:
            xbmcgui.Dialog().ok('Remote Downloader', 'There is no stream.  Exiting now.')
            sys.exit()

        # derived parameters
        url0 = url.split('|')[0]
        try:
            headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
        except:
            headers = dict('')

        # determine whether the file can be downloaded
        resp, content, resumable = helper_functions.resp_content_resumable(url0, headers, 0, title, url0)
        if resp is None and content is None:
            sys.exit()

        # JSON-RPC arguments
        method = 'Addons.ExecuteAddon'

        # send a download request to the downloading system
        if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'Yes':
            params = {'title': title, 'url': url, 'image': image, 'url0': url0, 'headers': headers,
                      'resumable': resumable, 'content': content, 'action': 'request_download'}

            result = json_functions.jsonrpc(method, params, 'script.remote_downloader')
            sys.exit()

        else:
            for i in range(5):
                # get info about the downloading Kodi system
                downloading_ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address{0}'.format(i+1))
                downloading_port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port{0}'.format(i+1))
                downloading_username = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username{0}'.format(i+1))
                downloading_password = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password{0}'.format(i+1))

                if downloading_ip != '':
                    # make sure the remote Kodi is available
                    _params = {'action': 'modify_addons_silent'}
                    result = json_functions.jsonrpc(method, _params, 'script.remote_downloader',
                                                    downloading_ip, downloading_port, downloading_username, downloading_password)

                    if result == 'OK':
                        # get info via JSON RPC about the current Kodi
                        requesting_ip = xbmc.getIPAddress()
                        requesting_port = json_functions.jsonrpc(method="Settings.GetSettingValue", params={"setting": "services.webserverport"})['value']
                        requesting_username = json_functions.jsonrpc(method="Settings.GetSettingValue", params={"setting": "services.webserverusername"})['value']
                        requesting_password = json_functions.jsonrpc(method="Settings.GetSettingValue", params={"setting": "services.webserverpassword"})['value']

                        params = {'title': title, 'url': url, 'image': image, 'url0': url0, 'headers': headers,
                                  'content': content, 'resumable': resumable, 'action': 'request_download',
                                  'downloading_ip': downloading_ip, 'downloading_username': downloading_username, 'downloading_password': downloading_password,
                                  'downloading_port': downloading_port, 'requesting_ip': requesting_ip, 'requesting_port': requesting_port,
                                  'requesting_username': requesting_username, 'requesting_password': requesting_password}

                        result = json_functions.jsonrpc(method, params, 'script.remote_downloader',
                                                        downloading_ip, downloading_port, downloading_username, downloading_password)
                        sys.exit()

            # no remote Kodi systems available ==> download it locally?
            if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'If remote unavailable':
                params = {'title': title, 'url': url, 'image': image, 'url0': url0, 'headers': headers,
                          'content': content, 'action': 'request_download'}

                result = json_functions.jsonrpc(method, params, 'script.remote_downloader')

        sys.exit()

    # ================================================== #
    #                                                    #
    #                 4. Download request                #
    #                                                    #
    # ================================================== #
    if action == 'request_download':
        # provided parameters
        title = name_functions.title_substitutions(params.get('title'))
        url0 = params.get('url0')
        content = params.get('content')

        # change the action from 'request_download' to 'confirm_download'
        params['action'] = 'confirm_download'

        # get the name of the file to be created and add it to `params`
        dest, _ = name_functions.get_dest(title, url0)
        basename = os.path.basename(dest)
        params['basename'] = basename

        # info about the requesting Kodi system
        requesting_ip = params.get('requesting_ip')
        requesting_username = params.get('requesting_username')
        requesting_password = params.get('requesting_password')
        requesting_port = params.get('requesting_port')

        # the size of the file to be created
        size = 1024 * 1024
        mb = content / size
        if content < size:
            size = content
        params['mb'] = mb
        params['size'] = size

        # the name of this system, aka the downloading system
        kodi_name = xbmc.getInfoLabel('System.FriendlyName')
        params['kodi_name'] = kodi_name

        # the JSON-RPC method
        method = 'Addons.ExecuteAddon'

        # requesting system == downloading system
        if not requesting_ip:
            json_functions.jsonrpc(method, params, 'script.remote_downloader')

        # requesting system != downloading system
        else:
            json_functions.jsonrpc(method, params, 'script.remote_downloader',
                                   requesting_ip, requesting_port, requesting_username, requesting_password)

        sys.exit()

    # ================================================== #
    #                                                    #
    #              5. Download confirmation              #
    #                                                    #
    # ================================================== #
    if action == 'confirm_download':
        basename = params.get('basename')
        kodi_name = params.get('kodi_name')
        mb = params.get('mb')

        if xbmcgui.Dialog().yesno('Remote Downloader', basename, 'Complete file is {0}MB'.format(mb), 'Download to {0}?'.format(kodi_name), 'Confirm',  'Cancel') == 0:
            method = 'Addons.ExecuteAddon'
            params['action'] = 'download'

            # info about the downloading Kodi system
            downloading_ip = params.get('downloading_ip')
            downloading_port = params.get('downloading_port')
            downloading_username = params.get('downloading_username')
            downloading_password = params.get('downloading_password')

            # requesting system == downloading system
            if not downloading_ip:
                json_functions.jsonrpc(method, params, 'script.remote_downloader')

            # requesting system != downloading system
            else:
                json_functions.jsonrpc(method, params, 'script.remote_downloader',
                                       downloading_ip, downloading_port, downloading_username, downloading_password)

        sys.exit()

    # ================================================== #
    #                                                    #
    #                      6. Download                   #
    #                                                    #
    # ================================================== #
    if action == 'download':
        # provided parameters
        url = params.get('url')
        url0 = params.get('url0')
        title = params.get('title')
        image = params.get('image')
        headers = params.get('headers')
        size = params.get('size')
        mb = params.get('mb')
        content = params.get('content')
        basename = params.get('basename')
        dest = params.get('dest')
        temp_dest = params.get('temp_dest')
        resumable = params.get('resumable')

        # determine whether the file can be downloaded
        resp, _, _ = helper_functions.resp_content_resumable(url0, headers, 0, title, url0)
        if resp is None:
            sys.exit()

        # info about the requesting Kodi
        requesting_ip = params.get('requesting_ip')
        requesting_username = params.get('requesting_username')
        requesting_password = params.get('requesting_password')
        requesting_port = params.get('requesting_port')

        # download-tracking variables
        total = 0
        notify = 0
        errors = 0
        count = 0
        resume = 0
        sleep = 0

        # provided parameters
        local_ip = params.get('local_ip')
        local_username = params.get('local_username')
        local_password = params.get('local_password')
        local_port = params.get('local_port')

        # get the destination path
        dest, temp_dest = name_functions.get_dest(title, url0)
        if dest is None:
            sys.exit()

        if os.path.exists(dest):
            i = 2
            while True:
                # add "(i)" to the end of the filename and check if it exists
                new_dest = dest.split('.')
                new_dest = '.'.join(new_dest[:-1]) + ' ({0}).'.format(i) + new_dest[-1]
                if not os.path.exists(new_dest):
                    dest = new_dest
                    break
                else:
                    i += 1

        xbmc.log('script.remote_downloader: ' + 'Download File Size : {0}MB {1}'.format(mb, dest))

        f = xbmcvfs.File(temp_dest, 'w')

        chunk = None
        chunks = []

        while True:
            downloaded = total
            for c in chunks:
                downloaded += len(c)
            percent = min(100 * downloaded / content, 100)
            if percent >= notify:
                # show a notification of the download progress
                if image:
                    xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format(title + ' - Download Progress - ' + str(percent) + '%', dest, 10000, image))
                else:
                    xbmc.executebuiltin("XBMC.Notification({0},{1},{2})".format(title + ' - Download Progress - ' + str(percent) + '%', dest, 10000))

                # send a notification to the Kodi that sent the download command
                if requesting_ip is not None:
                    method = "GUI.ShowNotification"
                    if image:
                        _params = {'title': title + ' - Download Progress - ' + str(percent) + '%',
                                   'message': dest, 'image': image, 'displaytime': 10000}
                    else:
                        _params = {'title': title + ' - Download Progress - ' + str(percent) + '%',
                                   'message': dest, 'displaytime': 10000}
                    result = json_functions.jsonrpc(method, params, None,
                                                    requesting_ip, requesting_port, requesting_username, requesting_password)

                notify += 10

            chunk = None
            error = False

            try:
                chunk = resp.read(size)
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
                        if requesting_ip is not None:
                            update_requesting_library = json_functions.jsonrpc(requesting_ip, requesting_port, requesting_username, requesting_password, method)

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
                    resp, _, _ = helper_functions.resp_content_resumable(url, headers, total, title, url0)
                else:
                    #use existing response
                    pass
