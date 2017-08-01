import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


def modify(msg_fmt='ok'):
    # modify Covenant
    infile = xbmc.translatePath('special://home/addons/plugin.video.covenant/covenant.py')
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
                xbmcgui.Dialog().ok('Remote Downloader', 'Covenant successfully modified!')
            elif msg_fmt == 'notification':
                xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format('Remote Downloader', 'Covenant successfully modified!', 5000, xbmcaddon.Addon('script.remote_downloader').getAddonInfo('icon')))
        elif new in text:
            if msg_fmt == 'ok':
                xbmcgui.Dialog().ok('Remote Downloader', 'Covenant was already modified.')
        else:
            xbmcgui.Dialog().ok('Remote Downloader', 'Covenant could not be modified.')

        # make a file to indicate that Covenant has been modified
        modfile = xbmcvfs.File(xbmc.translatePath('special://home/addons/plugin.video.covenant/.modified'), 'w')
        result = modfile.write('Modified by Remote Downloader')
        modfile.close()

        # set Covenant settings
        xbmcaddon.Addon('plugin.video.covenant').setSetting('downloads', 'true')
        if xbmcaddon.Addon('plugin.video.covenant').getSetting('movie.download.path') == "":
            xbmcaddon.Addon('plugin.video.covenant').setSetting('movie.download.path', xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder'))
        if xbmcaddon.Addon('plugin.video.covenant').getSetting('tv.download.path') == "":
            xbmcaddon.Addon('plugin.video.covenant').setSetting('tv.download.path', xbmcaddon.Addon('script.remote_downloader').getSetting('local_tv_folder'))
