import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


def modify(msg_fmt='ok'):
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
