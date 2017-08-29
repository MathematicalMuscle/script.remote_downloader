"""Get info about the "now playing" item

"""

import xbmc
import xbmcgui

import json
import sys


def get_now_playing():
    """Get info about the currently played file via JSON-RPC.

    https://stackoverflow.com/a/38436735/8023447

    """
    request = json.dumps({'jsonrpc': '2.0',
                          'method': 'Player.GetItem',
                          'params': {'playerid': 1,
                                     'properties': ['file', 'showtitle', 'season', 'episode', 'thumbnail']},
                          'id': '1'})
    return eval(json.dumps(json.loads(xbmc.executeJSONRPC(request))['result']['item']))


def process_now_playing():
    try:
        info = get_now_playing()
    except:
        info = {'file': xbmc.getInfoLabel('Player.Filenameandpath'), 'showtitle': xbmc.getInfoLabel('Player.Title'),
                'label': xbmc.getInfoLabel('Player.Title'), 'type': '', 'thumbnail': xbmc.getInfoLabel('Player.Art(thumb)')}

    url = info['file']
    if url == '':
        sys.exit()

    image = info['thumbnail']

    # Movie
    #if info['type'] == 'movie' and info['label']:
    if info['label'] and info['season'] == '-1' and info['episode'] == '-1':
        title = info['label']
        if title[-1] != ')' or title[-5:-3] not in ['19', '20']:
            year = xbmc.getInfoLabel('VideoPlayer.Year')
            if year is not None and len(year) == 4 and year[:2] in ['19', '20']:
                title += ' ({0})'.format(year)

    # TV
    #elif info['type'] == 'episode' and info['showtitle'] and info['season'] != '-1' and info['episode'] != '-1':
    elif info['showtitle'] and info['season'] != '-1' and info['episode'] != '-1':
        title = '{0} S{1:02d}E{2:02d}'.format(info['showtitle'], int(info['season']), int(info['episode']))

    # ask the user
    else:
        movie_or_tv = xbmcgui.Dialog().select('Movie or TV Show?', ['Movie', 'TV Show'])

        # Movie
        if movie_or_tv == 0:
            if len(info['label']) < 25 or ' ' in info['label']:
                title = xbmcgui.Dialog().input('Enter movie name:', info['label'])
            else:
                title = xbmcgui.Dialog().input('Enter movie name:')
            if title == '':
                sys.exit()

        # TV
        elif movie_or_tv == 1:
            if len(info['showtitle']) < 25 or ' ' in info['showtitle']:
                showtitle = xbmcgui.Dialog().input('Enter show title:', info['showtitle'])
            else:
                showtitle = xbmcgui.Dialog().input('Enter show title:')
            if showtitle == '':
                sys.exit()

            season = xbmcgui.Dialog().input('Enter season:')
            if season == '':
                sys.exit()

            episode = xbmcgui.Dialog().input('Enter episode number:')
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

    return title, url, image
