import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


def modify(msg_fmt='ok'):
    # modify Exodus
    infile = xbmc.translatePath('special://home/addons/plugin.video.exodus/exodus.py')
    if xbmcvfs.exists(infile):
        with open(infile, 'r') as f:
            text = f.read()
        old = 'try: downloader.download(name, image, sources.sources().sourcesResolve(json.loads(source)[0], True))'
        new = 'try:\n'
        new += '        import urllib\n'
        new += '        xbmc.executebuiltin("RunScript(script.remote_downloader, {0})".format(urllib.quote_plus(str({\'action\': \'prepare_download\', \'title\': name, \'image\': image, \'url\': sources.sources().sourcesResolve(json.loads(source)[0], True)}))))'
        if old in text:
            text = text.replace(old, new)
            with open(infile, 'w') as f:
                f.write(text)
            if msg_fmt == 'ok':
                xbmcgui.Dialog().ok('Remote Downloader', 'Exodus successfully modified!')
            elif msg_fmt == 'notification':
                xbmc.executebuiltin("XBMC.Notification({0},{1},{2},{3})".format('Remote Downloader', 'Exodus successfully modified!', 5000, xbmcaddon.Addon('script.remote_downloader').getAddonInfo('icon')))
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
            xbmcaddon.Addon('plugin.video.exodus').setSetting('movie.download.path', xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder'))
        if xbmcaddon.Addon('plugin.video.exodus').getSetting('tv.download.path') == "":
            xbmcaddon.Addon('plugin.video.exodus').setSetting('tv.download.path', xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder'))
