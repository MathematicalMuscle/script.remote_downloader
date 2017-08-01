import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from . import create_callbacks
from . import modify_covenant
from . import modify_elysium
from . import modify_exodus
from . import modify_lastplayed


def modify_addons(msg_fmt='ok'):
    modify_exodus.modify(msg_fmt)
    modify_elysium.modify(msg_fmt)
    modify_covenant.modify(msg_fmt)
    modify_lastplayed.modify(msg_fmt)
    create_callbacks.create_callbacks(msg_fmt)
