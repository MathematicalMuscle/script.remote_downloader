"""Functions for dealing with stream names/titles

"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import os
import re
import urlparse

from . import helper_functions


def add_substitution(old=None, new=None):
    """Add a regex substitution to 'special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'
    
    """
    if old is None:
        old = xbmcgui.Dialog().input('Old regex')
        
    if old:
        if new is None:
            new = xbmcgui.Dialog().input('New regex')
        
        if new:
            new_substitution = 're.sub(r"{0}", r"{1}", title)'.format(old, new)
            with open(xbmc.translatePath('special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'), 'r') as f:
                text = f.read()
                
            if new_substitution not in text:
                with open(xbmc.translatePath('special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'), 'a') as f:
                    f.write('re.sub(r"{0}", r"{1}", title)'.format(old, new))


def _remove_forbidden_chars(text):
    """Remove characters not allowed in filenames
    
    """
    for c in '\/:*?"<>|':
        text = text.replace(c, '')
    return text.strip('.').strip()


def _title_substitutions(title):
    """Do regex substitutions in the title
    
    """
    title = str(title)
    with open(xbmc.translatePath('special://userdata/addon_data/script.remote_downloader/title_regex_substitutions.txt'), 'r') as f:
        for line in f.readlines():
            if line.strip() and not line.startswith('#'):
                title = eval(line.strip())

    return title
    
    
def get_title(title):
    """Remove characters not allowed in filenames and perform regex substitutions
    
    """
    return _title_substitutions(_remove_forbidden_chars(title))


def remove_extension(filepath):
    """Get the extension-less basename of the file
    
    """
    return os.path.splitext(os.path.basename(filepath))[0]


def get_dest(title, url, look_for_duplicates=True):
    """Get the destination and temporary destination for the download
    
    """
    new_title = get_title(title)

    season_number = re.compile('(.+?)\sS(\d*)E\d*$').findall(title)

    # movie
    if len(season_number) == 0:
        dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_folder')
        if dest == "":
            return 1, None

        dest = xbmc.translatePath(dest)

        # put the movie into its own folder?
        if xbmcaddon.Addon('script.remote_downloader').getSetting('local_movies_own_folder') == 'true':
            dest = os.path.join(dest, new_title)

    # TV
    else:
        dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_tv_folder')
        if dest == "":
            return 2, None

        dest = xbmc.translatePath(dest)

        # add the show title
        transtvshowtitle = _remove_forbidden_chars(season_number[0][0])
        dest = os.path.join(dest, transtvshowtitle)

        # add the season
        dest = os.path.join(dest, 'Season {0:01d}'.format(int(season_number[0][1])))

    # add the extension
    url0 = helper_functions.get_url0(url)
    ext = os.path.splitext(urlparse.urlparse(url0).path)[1][1:]
    if ext not in ['mp4', 'mkv', 'flv', 'avi', 'mpg']:
        ext = 'mp4'

    # the temporary download location
    temp_dest = xbmcaddon.Addon('script.remote_downloader').getSetting('local_temp_folder')
    if temp_dest == "":
        temp_dest = os.path.join(dest, new_title + '.' + ext)
    else:
        temp_dest = xbmc.translatePath(temp_dest)
        temp_dest = os.path.join(temp_dest, new_title + '.' + ext)

    dest = os.path.join(dest, new_title + '.' + ext)

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

