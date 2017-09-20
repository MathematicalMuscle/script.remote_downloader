"""JSON functions

"""


import xbmc
import xbmcaddon

import base64
import json
import urllib
import urllib2


def jsonrpc(method, params=None, addonid=None, ip=None, port=None, username=None, password=None):
    # build out the data to be sent
    payload = {'jsonrpc': '2.0', 'method': method, 'id': '1'}

    if params is not None:
        if addonid is not None:
            payload['params'] = {'addonid': addonid, 'params': urllib.quote_plus(str(params))}
        else:
            payload['params'] = params

    # format the data
    data = json.dumps(payload)

    # local JSON-RPC
    if ip is None:
        response = eval(xbmc.executeJSONRPC(data))

    # remote JSON-RPC
    else:
        # prepare to initiate the connection
        url = 'http://{0}:{1}/jsonrpc'.format(ip, port)
        headers = {"Content-Type": "application/json"}
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

        # This error handling is specifically to catch HTTP errors and connection errors
        except urllib2.URLError as e:
            # In the event of an error, I am making the output begin with "ERROR " first, to allow for easy scripting.
            # You will get a couple different kinds of error messages in here, so I needed a consistent error condition to check for.
            return 'ERROR ' + str(e.reason)

    # A lot of the XBMC responses include the value "result", which lets you know how your call went
    # This logic fork grabs the value of "result" if one is present, and then returns that.
    # Note, if no "result" is included in the response from XBMC, the JSON response is returned instead.
    # You can then print out the whole thing, or pull info you want for further processing or additional calls.
    if 'result' in response:
        response = response['result']

    return response


def from_jsonrpc(parameters):
    """Extract a dictionary of the parameters sent via a JSON-RPC command

    """
    params = eval(urllib.unquote_plus(parameters).replace('streaminfo=', ''))
    if 'url' in params:
        if isinstance(params['url'], str):
            params['url'] = params['url'].replace(' ', '')
    return params
