"""Functions for dealing with stream names/titles

"""

import xbmc
import xbmcaddon
import xbmcvfs

import json
import os
import re
import sys
import urlparse


def trans(text):
    for c in '\/:*?"<>|':
        text = text.replace(c, '')
    return text.strip('.').strip()


def title_substitutions(title):
    title = str(title)
    with open(xbmc.translatePath('special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'), 'r') as f:
        for line in f.readlines():
            if line.strip() and not line.startswith('#'):
                title = eval(line.strip())

    return title


def get_dest(title, url0, look_for_duplicates=True):
    transname = title_substitutions(trans(title))

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

    if look_for_duplicates:
        if os.path.exists(dest) or os.path.exists(temp_dest):
            i = 2
            while True:
                # add "(i)" to the end of the filename and check if it exists
                new_dest = dest.split('.')
                new_dest = '.'.join(new_dest[:-1]) + ' ({0}).'.format(i) + new_dest[-1]
                new_temp_dest = temp_dest.split('.')
                new_temp_dest = '.'.join(new_temp_dest[:-1]) + ' ({0}).'.format(i) + new_temp_dest[-1]
                if not os.path.exists(new_dest) and not os.path.exists(new_temp_dest):
                    dest = new_dest
                    temp_dest = new_temp_dest
                    break
                else:
                    i += 1

    return dest, temp_dest
