"""Functions pertaining to 'autoexec.py'

"""

import xbmc
import xbmcvfs


# variables relating to `autoexec.py`
autoexec = xbmc.translatePath('special://userdata/autoexec.py')
autoexec_import = 'import xbmc'
autoexec_command = 'xbmc.executebuiltin("RunAddon(script.remote_downloader, \\"{\'action\':\'restart_upnp\'}\\")")'
autoexec_str = autoexec_import + '\n\n' + autoexec_command


def get_autoexec_opt():
    """Return the 'autoexec_opt' action that appears in the menu
    
    """
    if autoexec_status().startswith('delete'):
        return 'Remove \'Restart remote UPnP server\' from `autoexec.py`'
    else:
        return 'Add \'Restart remote UPnP server\' to `autoexec.py`'


def autoexec_status():
    """Determine whether or not 'Restart remote UPnP server' is already in 'autoexec.py'
    
    """
    if not xbmcvfs.exists(autoexec):
        return 'create'
    else:
        with open(autoexec, 'r') as f:
            text = f.read()
        if autoexec_import not in text:
            return 'add_both'
        elif autoexec_command not in text:
            return 'add_command'
        else:
            if text.strip() == autoexec_import + '\n\n' + autoexec_command:
                return 'delete_file'
            else:
                return 'delete_command'


def autoexec_add_remove(autoexec_opt=None):
    """Add or remove 'Restart remote UPnP server' from 'autoexec.py'
    
    """
    if isinstance(autoexec_opt, str):
        status = autoexec_status()
        
        if autoexec_opt.lower().startswith('add'):
            if status == 'create':
                with open(autoexec, 'w') as f:
                    f.write(autoexec_import + '\n\n' + autoexec_command)
            elif status == 'add_both':
                with open(autoexec, 'a') as f:
                    f.write(autoexec_import + '\n\n' + autoexec_command)
            elif status == 'add_command':
                with open(autoexec, 'a') as f:
                    f.write(autoexec_command)
                    
        elif autoexec_opt.lower().startswith('remove'):
            if status == 'delete_file':
                xbmcvfs.delete(autoexec)
            elif status == 'delete_command':
                with open(autoexec, 'r') as f:
                    text = f.read()
                    
                with open(autoexec, 'w') as f:
                    f.write(text.replace(autoexec_command + '\n', '').replace(autoexec_command, ''))

