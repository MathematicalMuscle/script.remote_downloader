import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


def create_callbacks(msg_fmt='ok'):
    # set Kodi Callbacks settings
    if xbmcvfs.exists(xbmc.translatePath('special://home/addons/script.service.kodi.callbacks/')) and msg_fmt == 'ok':
        if xbmcgui.Dialog().yesno('Remote Downloader', "Create 'Kodi Callbacks' Task and Event?"):
            # task number
            task = 1
            task_type = 'builtin'
            task_builtin = "RunScript(\"script.remote_downloader\", {\"modify_addons_silent\": True})".decode('utf-8')
            while task < 11:
                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.type'.format(task)) == 'none' \
                        or (xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.type'.format(task)) == task_type \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.builtin'.format(task)) == task_builtin):
                    break
                else:
                    task += 1

            # event number
            event = 1
            exodus_folder = xbmc.translatePath('special://home/addons/plugin.video.exodus')
            while event < 11:
                if xbmcaddon.Addon('script.service.kodi.callbacks').getLocalizedString(int(xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type'.format(event)))) == 'None' \
                        or (xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type'.format(event)) == '32235' \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type-v'.format(event)) == '6' \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.folder'.format(event)) == exodus_folder \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.task'.format(event)) == 'Task {0}'.format(task) \
                            and xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.patterns'.format(event)) == '*.modified'):
                    break
                else:
                    event += 1

            if task < 11 and event < 11:
                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.builtin'.format(task)) != task_builtin:
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('T{0}.builtin'.format(task), task_builtin)

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('T{0}.type'.format(task)) != task_type:
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('T{0}.type'.format(task), task_type)

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type'.format(event)) != '32235':
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.type'.format(event), '32235')

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.type-v'.format(event)) != '6':
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.type-v'.format(event), '6')

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.folder'.format(event)) != exodus_folder:
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.folder'.format(event), exodus_folder)

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.task'.format(event)) != 'Task {0}'.format(task):
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.task'.format(event), 'Task {0}'.format(task))

                if xbmcaddon.Addon('script.service.kodi.callbacks').getSetting('E{0}.patterns'.format(event)) != '*.modified':
                    xbmcaddon.Addon('script.service.kodi.callbacks').setSetting('E{0}.patterns'.format(event), '*.modified')

                xbmcgui.Dialog().ok('Remote Downloader', "Created 'Kodi Callbacks' Task {0} and Event {1}".format(task, event))
