"""JSON functions

"""


import xbmc
import xbmcaddon

import base64
import json
import urllib
import urllib2


# info about this system
ip = xbmcaddon.Addon('script.remote_downloader').getSetting('local_ip_address')
if not ip:
    ip = xbmc.getIPAddress()
username = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverusername"}, "id":1}'))['result']['value']
password = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverpassword"}, "id":1}'))['result']['value']
port = eval(xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.GetSettingValue","params":{"setting":"services.webserverport"}, "id":1}'))['result']['value']


def jsonrpc(method, params=None, addonid=None, ip=ip, port=port, username=username, password=password):
    url = 'http://{0}:{1}/jsonrpc'.format(ip, port)

    # build out the Data to be sent
    payload = {'jsonrpc': '2.0', 'method': method, 'id': '1'}

    if params is not None and addonid == 'script.remote_downloader':
        payload["params"] = {"addonid": "script.remote_downloader", "params": {"streaminfo": "{0}".format(urllib.quote_plus(str(params)))}}
    else:
        payload["params"] = params

    headers = {"Content-Type": "application/json"}

    # format the data
    data = json.dumps(payload)

    # prepare to initiate the connection
    req = urllib2.Request(url, data, headers)
    if username and password:
        # format the provided username & password and add them to the request header
        base64string = base64.encodestring('{0}:{1}'.format(username, password)).replace('\n', '')
        req.add_header("Authorization", "Basic {0}".format(base64string))

    # send the command
    try:
        response = urllib2.urlopen(req)
        response = response.read()
        response = json.loads(response)

        # A lot of the XBMC responses include the value "result", which lets you know how your call went
        # This logic fork grabs the value of "result" if one is present, and then returns that.
        # Note, if no "result" is included in the response from XBMC, the JSON response is returned instead.
        # You can then print out the whole thing, or pull info you want for further processing or additional calls.
        if 'result' in response:
            response = response['result']

    # This error handling is specifically to catch HTTP errors and connection errors
    except urllib2.URLError as e:
        # In the event of an error, I am making the output begin with "ERROR " first, to allow for easy scripting.
        # You will get a couple different kinds of error messages in here, so I needed a consistent error condition to check for.
        response = 'ERROR ' + str(e.reason)

    return response


def from_jsonrpc(parameters):
    """Extract a dictionary of the parameters sent via a JSON-RPC command

    """
    return eval(urllib.unquote_plus(parameters).replace('streaminfo=', ''))
