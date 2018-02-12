"""Get info about the "now playing" item

"""

import xbmc
import xbmcaddon
import xbmcgui

import sys

from . import jsonrpc_functions
from . import network_functions


def get_now_playing():
    """Get info about the currently playing file via JSON-RPC.

    https://stackoverflow.com/a/38436735/8023447

    """
    params = {'playerid': 1, 'properties': ['file', 'showtitle', 'season', 'episode', 'thumbnail']}
    return jsonrpc_functions.jsonrpc('Player.GetItem', params)['item']


def process_now_playing():
    """Get info about the currently playing file, prompting the user if necessary
    
    """
    # pre-check: make sure a download path has been configured
    download_local = xbmcaddon.Addon('script.remote_downloader').getSetting('download_local')
    local_movies_folder = xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder')
    local_tv_folder = xbmcaddon.Addon('script.remote_downloader').getSetting('local_tv_folder')

    if download_local == 'Yes':
        if not local_movies_folder and not local_tv_folder:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: download paths not configured in Remote Downloader settings')
            sys.exit()

    try:
        info = get_now_playing()
    except:
        info = {'file': xbmc.getInfoLabel('Player.Filenameandpath'), 'showtitle': xbmc.getInfoLabel('Player.Title'),
                'label': xbmc.getInfoLabel('Player.Title'), 'type': '', 'thumbnail': xbmc.getInfoLabel('Player.Art(thumb)')}

    url = info['file']
    if url == '':
        xbmcgui.Dialog().ok('Remote Downloader', 'Error: cannot get stream URL')
        sys.exit()

    # determine whether the file can be downloaded
    resp, bytesize, headers, cookie, _ = network_functions.open(url)
    if bytesize is None:
        sys.exit()
    url_redirect = resp.geturl()
    if url_redirect == url:
        url_redirect = None

    image = info['thumbnail']

    # Movie
    if info['type'] == 'movie' and info['label']:
        # if downloading locally, make sure the movies download path has been configured
        if download_local == 'Yes' and not local_movies_folder:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: movies download folder not setup in Remote Downloader settings')
            sys.exit()

        title = info['label']
        if title[-1] != ')' or title[-5:-3] not in ['19', '20']:
            year = xbmc.getInfoLabel('VideoPlayer.Year')
            if year is not None and len(year) == 4 and year[:2] in ['19', '20']:
                title += ' ({0})'.format(year)

    # TV
    elif info['type'] == 'episode' and info['showtitle'] and info['season'] != '-1' and info['episode'] != '-1':
        # if downloading locally, make sure the TV download path has been configured
        if download_local == 'Yes' and not local_tv_folder:
            xbmcgui.Dialog().ok('Remote Downloader', 'Error: TV download folder not setup in Remote Downloader settings')
            sys.exit()

        title = '{0} S{1:02d}E{2:02d}'.format(info['showtitle'], int(info['season']), int(info['episode']))

    # ask the user
    else:
        movie_or_tv = xbmcgui.Dialog().select('Movie or TV Show?', ['Movie', 'TV Show'])

        # Movie
        if movie_or_tv == 0:
            # if downloading locally, make sure the movies download path has been configured
            if download_local == 'Yes' and not local_movies_folder:
                xbmcgui.Dialog().ok('Remote Downloader', 'Error: movies download folder not setup in Remote Downloader settings')
                sys.exit()

            if len(info['label']) < 25 or ' ' in info['label']:
                title = xbmcgui.Dialog().input('Enter movie name:', info['label'])
            else:
                title = xbmcgui.Dialog().input('Enter movie name:')
            if title == '':
                sys.exit()

        # TV
        elif movie_or_tv == 1:
            # if downloading locally, make sure the TV download path has been configured
            if download_local == 'Yes' and not local_tv_folder:
                xbmcgui.Dialog().ok('Remote Downloader', 'Error: TV download folder not setup in Remote Downloader settings')
                sys.exit()
                
            if len(info['showtitle']) < 25 or ' ' in info['showtitle']:
                showtitle = xbmcgui.Dialog().input('Enter show title:', info['showtitle'])
            else:
                showtitle = xbmcgui.Dialog().input('Enter show title:')
            if showtitle == '':
                sys.exit()

            season = xbmcgui.Dialog().input('Enter season:', type=xbmcgui.INPUT_NUMERIC)
            if season == '':
                sys.exit()

            episode = xbmcgui.Dialog().input('Enter episode number:', type=xbmcgui.INPUT_NUMERIC)
            if episode == '':
                sys.exit()

            # try to zero pad the season and episode
            try:
                season = "{0:02d}".format(int(season))
            except:
                pass
            try:
                episode = "{0:02d}".format(int(episode))
            except:
                pass

            title = "{0} S{1}E{2}".format(showtitle, season, episode)

        else:
            sys.exit()

    return title, url, url_redirect, image, bytesize, headers, cookie

