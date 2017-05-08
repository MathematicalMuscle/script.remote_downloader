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

import urllib
import urllib2
import urlparse
import json
import base64
import re


def trans(text):
    for c in '\/:*?"<>|':
        text = text.replace(c, '')
    return text.strip('.').strip()


def resp_content_resumable(url, headers, size, title, url0):
    try:
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes={0}-'.format(size)

        req = urllib2.Request(url, headers=headers)
        resp = urllib2.urlopen(req, timeout=30)

    except:
        dest, _ = get_dest(title, url0)
        xbmcgui.Dialog().ok(title, dest, 'Download failed', 'No response from server')
        return None, None, None

    try:
        content = int(resp.headers['Content-Length'])
    except:
        xbmcgui.Dialog().ok(title, trans(title), 'Unknown filesize', 'Unable to download')
        return None, None, None

    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False

    if resumable:
        xbmc.log("Download is resumable")

    return resp, content, resumable


def get_dest(title, url0):
    transname = trans(title)

    name = re.compile('(.+?)\sS(\d*)E\d*$').findall(title)
    levels =['../../../..', '../../..', '../..', '..']

    if len(name) == 0:
        # movie
        dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder')
        if dest == "":
            return None, None

        dest = xbmc.translatePath(dest)
        for level in levels:
            try:
                xbmcvfs.mkdir(os.path.abspath(os.path.join(dest, level)))
            except:
                pass
        xbmcvfs.mkdir(dest)

        # put the movie into its own folder?
        if xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_own_folder') == 'true':
            dest = os.path.join(dest, transname)
            xbmcvfs.mkdir(dest)
    else:
        # TV
        dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_tv_folder')
        if dest == "":
            return None, None

        dest = xbmc.translatePath(dest)
        for level in levels:
            try:
                xbmcvfs.mkdir(os.path.abspath(os.path.join(dest, level)))
            except:
                pass
        xbmcvfs.mkdir(dest)
        transtvshowtitle = trans(name[0][0])
        dest = os.path.join(dest, transtvshowtitle)
        xbmcvfs.mkdir(dest)
        dest = os.path.join(dest, 'Season {0:01d}'.format(int(name[0][1])))
        xbmcvfs.mkdir(dest)

    # add the extension
    ext = os.path.splitext(urlparse.urlparse(url0).path)[1][1:]
    if ext not in ['mp4', 'mkv', 'flv', 'avi', 'mpg']:
        ext = 'mp4'

    # the temporary download location
    temp_dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_temp_folder')
    if temp_dest == "":
        temp_dest = os.path.join(dest, transname + '.' + ext)
    else:
        temp_dest = xbmc.translatePath(temp_dest)
        temp_dest = os.path.join(temp_dest, transname + '.' + ext)

    dest = os.path.join(dest, transname + '.' + ext)

    return dest, temp_dest


def done(title, dest, downloaded):
    playing = xbmc.Player().isPlaying()
    text = xbmcgui.Window(10000).getProperty('GEN-DOWNLOADED')

    if len(text) > 0:
        text += '[CR]'

    if downloaded:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR forestgreen]Download succeeded[/COLOR]')
    else:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR red]Download failed[/COLOR]')

    xbmcgui.Window(10000).setProperty('GEN-DOWNLOADED', text)

    if (not downloaded) or (not playing):
        xbmcgui.Dialog().ok(title, text)
        xbmcgui.Window(10000).clearProperty('GEN-DOWNLOADED')


def modify_addons(msg_fmt='ok'):
    # modify Exodus
    infile = xbmc.translatePath('special://home/addons/plugin.video.exodus/exodus.py')
    if xbmcvfs.exists(infile):
        with open(infile, 'r') as f:
            text = f.read()
        old = 'try: downloader.download(name, image, sources.sources().sourcesResolve(json.loads(source)[0], True))'
        new = 'try:\n'
        new += '        import urllib\n'
        new += '        xbmc.executebuiltin("RunScript(script.remote_downloader, {0})".format(urllib.quote_plus(str({\'title\': name, \'image\': image, \'url\': sources.sources().sourcesResolve(json.loads(source)[0], True)}))))'
        if old in text:
            text = text.replace(old, new)
            with open(infile, 'w') as f:
                f.write(text)
            if msg_fmt == 'ok':
                xbmcgui.Dialog().ok('Remote Downloader', 'Exodus successfully modified!')
            elif msg_fmt == 'notification':
                xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format('Remote Downloader', 'Exodus successfully modified!', 5000,
                                                                                xbmcaddon.Addon('script.remote_downloader').getAddonInfo('icon')))
        elif new in text:
            if msg_fmt == 'ok':
                xbmcgui.Dialog().ok('Remote Downloader', 'Exodus was already modified.')
        else:
            xbmcgui.Dialog().ok('Remote Downloader', 'Exodus could not be modified.')

        # make a file to indicate that Exodus has been modified
        modfile = xbmcvfs.File(xbmc.translatePath('special://home/addons/plugin.video.exodus/.modified'), 'w')
        result = modfile.write('Modified by Remote Downloader')
        modfile.close()

        # set Exodus settings
        xbmcaddon.Addon('plugin.video.exodus').setSetting('downloads', 'true')
        if xbmcaddon.Addon('plugin.video.exodus').getSetting('movie.download.path') == "":
            xbmcaddon.Addon('plugin.video.exodus').setSetting('movie.download.path', xbmc.translatePath('special://userdata'))
        if xbmcaddon.Addon('plugin.video.exodus').getSetting('tv.download.path') == "":
            xbmcaddon.Addon('plugin.video.exodus').setSetting('tv.download.path', xbmc.translatePath('special://userdata'))

    # modify Last Played
    infile = xbmc.translatePath('special://home/addons/plugin.video.last_played/addon.py')
    if xbmcvfs.exists(infile):
        with open(infile, 'r') as f:
            text = f.read()
        old = 'li.addContextMenuItems(command)'
        new = "if line['show'] and line['season'] and line['episode']:\n"
        new += "\t\t\t\t\ttitle = '{0} S{1:02d}E{2:02d}'.format(line['show'], int(line['season']), int(line['episode']))\n"
        new += "\t\t\t\telse:\n"
        new += "\t\t\t\t\ttitle = line['title']\n"
        new += "\t\t\t\tinfo = {'url': line['video'], 'image': line['thumbnail'], 'title': title}\n"
        new += "\t\t\t\tcommand.append(('Download', 'RunScript(script.remote_downloader, {0})'.format(urllib.quote_plus(str(info)))))\n"
        new += "\t\t\t\tli.addContextMenuItems(command)"
        if old in text and new not in text:
            # text = text.replace(new, old)
            text = text.replace(old, new)
            with open(infile, 'w') as f:
                f.write(text)
            if msg_fmt == 'ok':
                xbmcgui.Dialog().ok('Remote Downloader', 'Last Played successfully modified!')
            elif msg_fmt == 'notification':
                xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format('Remote Downloader', 'Last Played successfully modified!', 5000,
                                                                                xbmcaddon.Addon('script.remote_downloader').getAddonInfo('icon')))
        elif old in text and new in text:
            if msg_fmt == 'ok':
                xbmcgui.Dialog().ok('Remote Downloader', 'Last Played was already modified.')
        else:
            xbmcgui.Dialog().ok('Remote Downloader', 'Last Played could not be modified.')

    # set Kodi Callbacks settings
    if xbmcvfs.exists(xbmc.translatePath('special://home/addons/script.service.kodi.callbacks/')) and msg_fmt == 'ok':
        if xbmcgui.Dialog().yesno('Remote Downloader', "Create 'Kodi Callbacks' Task and Event?"):
            # task number
            task = 1
            task_type = 'builtin'
            task_builtin = "RunScript(\"script.remote_downloader\", {\"modify_addons_silent\": True})".decode('utf-8')
            while task < 11:
                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.type'.format(task)) == 'none' \
                        or (xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.type'.format(task)) == task_type \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.builtin'.format(task)) == task_builtin):
                    break
                else:
                    task += 1

            # event number
            event = 1
            exodus_folder = xbmc.translatePath('special://home/addons/plugin.video.exodus')
            while event < 11:
                if xbmcaddon.Addon('script.service.kodi.callbacks').getLocalizedString(int(xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type'.format(event)))) == 'None' \
                        or (xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type'.format(event)) == '32235' \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type-v'.format(event)) == '6' \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.folder'.format(event)) == exodus_folder \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.task'.format(event)) == 'Task {0}'.format(task) \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.patterns'.format(event)) == '*.modified'):
                    break
                else:
                    event += 1

            if task < 11 and event < 11:
                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.builtin'.format(task)) != task_builtin:
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('T{0}.builtin'.format(task), task_builtin)

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.type'.format(task)) != task_type:
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('T{0}.type'.format(task), task_type)

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type'.format(event)) != '32235':
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.type'.format(event), '32235')

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type-v'.format(event)) != '6':
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.type-v'.format(event), '6')

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.folder'.format(event)) != exodus_folder:
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.folder'.format(event), exodus_folder)

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.task'.format(event)) != 'Task {0}'.format(task):
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.task'.format(event), 'Task {0}'.format(task))

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.patterns'.format(event)) != '*.modified':
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.patterns'.format(event), '*.modified')

                xbmcgui.Dialog().ok('Remote Downloader', "Created 'Kodi Callbacks' Task {0} and Event {1}".format(task, event))


def getJsonRemote(host, port, username, password, method, parameters):
    # http://forum.kodi.tv/showthread.php?tid=197645
    # build the URL we're going to talk to
    url = 'http://{0}:{1}/jsonrpc'.format(host, port)

    # build out the Data to be sent
    values = {'jsonrpc': '2.0', 'method': method, 'id': '1'}
    if parameters:
        values["params"] = parameters
    headers = {"Content-Type": "application/json"}

    # format the data
    data = json.dumps(values)

    # prepare to initiate the connection
    req = urllib2.Request(url, data, headers)
    if username and password:
        # format the provided username & password and add them to the request header
        base64string = base64.encodestring('{0}:{1}'.format(username, password)).replace('\n', '')
        req.add_header("Authorization", "Basic {0}".format(base64string))

    # send the command
    try:
        response = urllib2.urlopen(req)
        response = response.read()
        response = json.loads(response)

        # A lot of the XBMC responses include the value "result", which lets you know how your call went
        # This logic fork grabs the value of "result" if one is present, and then returns that.
        # Note, if no "result" is included in the response from XBMC, the JSON response is returned instead.
        # You can then print out the whole thing, or pull info you want for further processing or additional calls.
        if 'result' in response:
            response = response['result']

    # This error handling is specifically to catch HTTP errors and connection errors
    except urllib2.URLError as e:
        # In the event of an error, I am making the output begin with "ERROR " first, to allow for easy scripting.
        # You will get a couple different kinds of error messages in here, so I needed a consistent error condition to check for.
        response = 'ERROR ' + str(e.reason)

    return response


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # modify addons and exit
        modify_addons()
        sys.exit()

    params = eval(urllib.unquote_plus(sys.argv[1]).replace('streaminfo=', ''))
    xbmc.log('script.remote_downloader: ' + str(params))

    if params.get('modify_addons_silent') is not None:
        # modify addons silently and exit
        modify_addons(msg_fmt='notification')
        sys.exit()

    # if we're going to download remotely, make sure the remote Kodi is available
    if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'false':
        # get info from the settings about the remote Kodi
        ip = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_ip_address')
        port = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_port')
        username = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_username')
        password = xbmcaddon.Addon('script.remote_downloader').getSetting('remote_password')

        # JSON RPC parameters for running `Remote Downloader` in silent update mode on the remote Kodi
        method = 'Addons.ExecuteAddon'
        parameters = {"addonid": "script.remote_downloader", "params": {"streaminfo": "{0}".format(
            urllib.quote_plus(str({'modify_addons_silent': True})))}}

        # silently update the remote Kodi
        results = getJsonRemote(ip, port, username, password, method, parameters)

        if results != 'OK':
            xbmcgui.Dialog().ok('Remote Downloader', 'Download cannot be started because the remote Kodi is unavailable.')
            sys.exit()

    # provided parameters
    image = params.get('image')
    title = params.get('title')
    url = params.get('url')
    preapproved = params.get('preapproved')

    # if there is no url, exit
    if url is None:
        sys.exit()

    # process the url to get the headers
    try:
        headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict('')

    # split the url
    url0 = url.split('|')[0]

    # determine whether the file can be downloaded
    resp, content, resumable = resp_content_resumable(url0, headers, 0, title, url0)
    if resp is None and content is None:
        sys.exit()

    # file size info
    size = 1024 * 1024
    mb = content / size
    if content < size:
        size = content

    # get the translated name
    ext = os.path.splitext(urlparse.urlparse(url0).path)[1][1:]
    if ext not in ['mp4', 'mkv', 'flv', 'avi', 'mpg']:
        ext = 'mp4'
    name = re.compile('(.+?)\sS(\d*)E\d*$').findall(title)
    transname = trans(title) + '.' + ext

    # ask for approval
    if not preapproved:
        if xbmcgui.Dialog().yesno(title + ' - Confirm Download', transname, 'Complete file is {0}MB'.format(mb), 'Continue with download?', 'Confirm',  'Cancel') != 0:
            sys.exit()

    # don't download it locally --> send it to another Kodi
    if xbmcaddon.Addon('script.remote_downloader').getSetting('download_local') == 'false':
        # get info via JSON RPC about the current Kodi
        local_username = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverusername"}, "id":1}'))['result']['value']
        local_password = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverpassword"}, "id":1}'))['result']['value']
        local_port = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverport"}, "id":1}'))['result']['value']

        # JSON RPC parameters for downloading the stream
        method = 'Addons.ExecuteAddon'
        parameters = {"addonid":"script.remote_downloader", "params":{"streaminfo": "{0}".format(urllib.quote_plus(str({'title': title, 'image': image, 'url': url, 'preapproved': True, 'local_ip': xbmc.getIPAddress(), 'local_password': local_password, 'local_username': local_username, 'local_port': local_port})))}}

        # make the remote Kodi download the stream
        results = getJsonRemote(ip, port, username, password, method, parameters)
        xbmc.log('script.remote_downloader: ' + str(results))

    # download it locally
    else:
        # provided parameters
        local_ip = params.get('local_ip')
        local_username = params.get('local_username')
        local_password = params.get('local_password')
        local_port = params.get('local_port')

        # get the destination path
        dest, temp_dest = get_dest(title, url0)
        if dest is None:
            sys.exit()

        # download-tracking variables
        total = 0
        notify = 0
        errors = 0
        count = 0
        resume = 0
        sleep = 0

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
                xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format(title + ' - Download Progress - ' + str(percent) + '%', dest, 10000, image))

                # send a notification to the Kodi that sent the download command
                if local_ip is not None:
                    parameters = {'title': title + ' - Download Progress - ' + str(percent) + '%',
                                  'message': dest, 'image': image, 'displaytime': 10000}
                    results = getJsonRemote(local_ip, int(local_port), local_username, local_password, "GUI.ShowNotification", parameters)
                    xbmc.log('script.remote_downloader: ' + str(results))

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

                        done(title, dest, True)

                        # update the library?
                        if xbmcaddon.Addon('script.remote_downloader').getSetting('update_library') == 'true':
                            update_library = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"VideoLibrary.Scan"}'))

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
                    done(title, dest, False)
                    sys.exit()

                resume += 1
                errors  = 0
                if resumable:
                    chunks  = []
                    #create new response
                    xbmc.log('script.remote_downloader: ' + 'Download resumed ({0}) {1}'.format(resume, dest))
                    resp, _, _ = resp_content_resumable(url, headers, total, title, url0)
                else:
                    #use existing response
                    pass
