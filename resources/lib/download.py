"""Define a class for downloading streams

"""

import xbmc
import xbmcgui
import xbmcvfs

import os
import sys
import time

from . import helper_functions
from . import jsonrpc_functions
from . import name_functions
from . import tracking


class Download(object):
    def __init__(self, title, url, url_redirect, image, bytesize, r_ip, r_port, r_user, r_pass, track):
        self.title = title
        self.url = url
        self.url_redirect = url_redirect
        self.bytesize = bytesize
        self.image = image
        self.r_ip = r_ip
        self.r_port = r_port
        self.r_user = r_user
        self.r_pass = r_pass
        self.track = track
        
        self.basename = None
        self.dest = None
        self.temp_dest = None
        
        self.start_time = None
        self.progress_file = None
        
    def download(self):
        """Download the stream
        
        """
        # the name of the file to be created
        self.dest, self.temp_dest = name_functions.get_dest(self.title, self.url)
        if self.dest is None:
            self.dialog_ok('ERROR: no download destination')
            sys.exit()
            
        self.basename = os.path.basename(self.dest)
        
        # determine whether the file can be downloaded
        resp, _, resumable = helper_functions.resp_bytesize_resumable(self.url, self.url_redirect, r_ip=self.r_ip, r_port=self.r_port, r_user=self.r_user, r_pass=self.r_pass)

        if resp is None:
            sys.exit()
        
        # create the destination directory, if it doesn't already exist
        xbmcvfs.mkdirs(os.path.dirname(self.dest))
            
        # the size of the file in MB
        mbsize = self.bytesize / (1024 * 1024)
        
        # the file where progress will be tracked
        if self.track:
            self.progress_file = os.path.join(tracking.get_tracking_folder(), 'TRACKER {0}.txt'.format(os.path.splitext(self.basename)[0]))

        # download-tracking variables
        total = 0
        notify = 0
        errors = 0
        count = 0
        resume = 0
        sleep = 0

        f = xbmcvfs.File(self.temp_dest, 'w')

        chunk = None
        chunks = []
        
        self.start_time = time.time()

        while True:
            downloaded = total
            for c in chunks:
                downloaded += len(c)
            percent = int(min(100. * downloaded / self.bytesize, 100))
            
            # record the download progress
            if self.track:
                self.track_progress(percent)
                
            # show a notification of the download progress
            if percent >= notify:
                self.notification(percent)
                notify += 10

            chunk = None
            error = False

            try:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    if percent < 99:
                        error = True
                    else:
                        while len(chunks) > 0:
                            c = chunks.pop(0)
                            f.write(c)
                            del c

                        f.close()
                        xbmc.log('script.remote_downloader: ' + '{0} download complete'.format(self.dest))

                        # if it was downloaded to a temporary location, move it
                        if self.temp_dest != self.dest:
                            xbmcvfs.rename(self.temp_dest, self.dest)

                        # update the library
                        method = "VideoLibrary.Scan"
                        update_downloading_library = jsonrpc_functions.jsonrpc(method)
                        if self.r_ip:
                            update_requesting_library = jsonrpc_functions.jsonrpc(method, None, None, self.r_ip, self.r_port, self.r_user, self.r_pass)

                        self.done(True)
                        sys.exit()

            except Exception, e:
                xbmc.log('script.remote_downloader: ' + str(e))
                error = True
                sleep = 10
                errno = 0

                if hasattr(e, 'errno'):
                    errno = e.errno

                if errno == 10035: # 'A non-blocking socket operation could not be completed immediately'
                    pass

                if errno == 10054: #'An existing connection was forcibly closed by the remote host'
                    errors = 10 #force resume
                    sleep  = 30

                if errno == 11001: # 'getaddrinfo failed'
                    errors = 10 #force resume
                    sleep  = 30

            if chunk:
                errors = 0
                chunks.append(chunk)
                if len(chunks) > 5:
                    c = chunks.pop(0)
                    f.write(c)
                    total += len(c)
                    del c

            if error:
                errors += 1
                count  += 1
                xbmc.log('script.remote_downloader: {0} Error(s) whilst downloading {1}'.format(count, self.dest))
                xbmc.sleep(sleep*1000)

            if (resumable and errors > 0) or errors >= 10:
                if (not resumable and resume >= 50) or resume >= 500:
                    #Give up!
                    xbmc.log('script.remote_downloader: {0} download canceled - too many errors whilst downloading'.format(self.dest))
                    self.done(False)
                    sys.exit()

                resume += 1
                errors  = 0
                if resumable:
                    chunks  = []
                    #create new response
                    xbmc.log('script.remote_downloader: Download resumed ({0}) {1}'.format(resume, self.dest))
                    resp, _, _ = helper_functions.resp_bytesize_resumable(self.url, self.url_redirect, size=total, r_ip=self.r_ip, r_port=self.r_port, r_user=self.r_user, r_pass=self.r_pass)
                else:
                    #use existing response
                    pass
                
    def track_progress(self, status, finish_time=-1.):
        """Track the download progress
        
        """
        # `status` is an integer (percent)
        if isinstance(status, int):
            with open(self.progress_file, 'w') as f:
                f.write('{0}\n{1}\n{2}\n[COLOR forestgreen]{3:3d}%[/COLOR]  {4}'.format('script.remote_downloader', self.start_time, finish_time, status, self.basename))
                
        # `status` is a failure message
        else:
            with open(self.progress_file, 'w') as f:
                f.write('{0}\n{1}\n{2}\n[COLOR red]{3}[/COLOR]  {4}'.format('script.remote_downloader', self.start_time, finish_time, str(status), self.basename))
        
    def notification(self, status):
        """Show a notification of the download progress
        
        """
        # `status` is an integer (percent)
        if isinstance(status, int):
            msg_params = {'title': '{0}% - {1}'.format(status, self.basename), 'message': self.dest, 'displaytime': 10000}
            
        # `status` is a failure message
        else:
            msg_params = {'title': str(status), 'message': self.dest, 'displaytime': 10000}
            
        # include the image in the notification, if there is one
        if self.image is not None:
            msg_params['image'] = self.image
            
        # show a notification on this system
        result = jsonrpc_functions.jsonrpc("GUI.ShowNotification", msg_params)

        # send a notification to the Kodi that sent the download command
        if self.r_ip:
            result = jsonrpc_functions.jsonrpc("GUI.ShowNotification", msg_params, None, self.r_ip, self.r_port, self.r_user, self.r_pass)
    
    def dialog_ok(self, line, heading='Remote Downloader'):
        params = {'action': 'dialog_ok', 'line': line, 'heading': heading}
        result = jsonrpc_functions.jsonrpc('Addons.ExecuteAddon', params, 'script.remote_downloader', self.r_ip, self.r_port, self.r_user, self.r_pass)
            
    def done(self, success):
        """Show a success/failure message
        
        """
        playing = xbmc.Player().isPlaying()
        text = xbmcgui.Window(10000).getProperty('GEN-DOWNLOADED')

        if len(text) > 0:
            text += '[CR]'

        if success:
            self.track_progress(100, time.time())
            text += '{0} : {1}'.format(self.basename, '[COLOR forestgreen]Download succeeded[/COLOR]')
        else:
            self.track_progress('FAILED', time.time())
            text += '{0} : {1}'.format(self.basename, '[COLOR red]Download failed[/COLOR]')

        xbmcgui.Window(10000).setProperty('GEN-DOWNLOADED', text)

        if not success:
            self.dialog_ok('{0} : {1}'.format(self.basename, '[COLOR red]Download failed[/COLOR]'))
        
        elif not playing:
            xbmcgui.Dialog().ok(self.title, text)
            xbmcgui.Window(10000).clearProperty('GEN-DOWNLOADED')
            
    def delete_tracker(self):
        """Delete the tracker file
        
        """
        if self.progress_file is not None and xbmcvfs.exists(self.progress_file):
            xbmcvfs.delete(self.progress_file)

