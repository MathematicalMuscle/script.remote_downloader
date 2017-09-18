"""Functions for dealing with stream names/titles

"""

import xbmc
import xbmcaddon
import xbmcvfs

import os
import re
import urlparse

from . import simple


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


def get_title(title):
    return title_substitutions(trans(title))


def remove_extension(f):
    return '.'.join(os.path.basename(f).split('.')[:-1])


def get_dest(title, url, look_for_duplicates=True, make_directories=True):
    transname = title_substitutions(trans(title))
    url0 = simple.get_url0(url)

    name = re.compile('(.+?)\sS(\d*)E\d*$').findall(title)

    if len(name) == 0:
        # movie
        dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder')
        if dest == "":
            return 1, None

        dest = xbmc.translatePath(dest)

        # put the movie into its own folder?
        if xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_own_folder') == 'true':
            dest = os.path.join(dest, transname)

    else:
        # TV
        dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_tv_folder')
        if dest == "":
            return 2, None

        dest = xbmc.translatePath(dest)

        # add the show title
        transtvshowtitle = trans(name[0][0])
        dest = os.path.join(dest, transtvshowtitle)

        # add the season
        dest = os.path.join(dest, 'Season {0:01d}'.format(int(name[0][1])))

    # make the directory?
    if make_directories:
        xbmcvfs.mkdirs(dest)

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
        if os.path.exists(os.path.dirname(dest)):
            # get lists of the files without extensions in the `dest` and `temp_dest` directories
            dest_dir = [remove_extension(f) for f in os.listdir(os.path.dirname(dest)) if os.path.isfile(os.path.join(os.path.dirname(dest), f))]
            temp_dest_dir = [remove_extension(f) for f in os.listdir(os.path.dirname(temp_dest)) if os.path.isfile(os.path.join(os.path.dirname(temp_dest), f))]

            if remove_extension(dest) in dest_dir or remove_extension(temp_dest) in temp_dest_dir:
                i = 2
                while True:
                    # add "(i)" to the end of the filename and check if it exists
                    new_dest = dest.split('.')
                    new_dest = '.'.join(new_dest[:-1]) + ' ({0}).'.format(i) + new_dest[-1]
                    new_temp_dest = temp_dest.split('.')
                    new_temp_dest = '.'.join(new_temp_dest[:-1]) + ' ({0}).'.format(i) + new_temp_dest[-1]

                    if remove_extension(new_dest) not in dest_dir and remove_extension(new_temp_dest) not in temp_dest_dir:
                        dest = new_dest
                        temp_dest = new_temp_dest
                        break
                    else:
                        i += 1

    return dest, temp_dest
