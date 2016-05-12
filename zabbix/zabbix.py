import threading
import http.client
import json


def call_zabix():
    for i in range(0, 100):
        conn = http.client.HTTPConnection("zabbix.dcb.olx.com.br")

        headers = {
            'content-type': "application/json-rpc",
            }

        payload = '{"jsonrpc": "2.0", "method": "user.login",\
        "params": {"user": "desenvolvimento", "password": "olx123"},\
        "id": 1, "auth": null}'

        conn.request("POST", "/api_jsonrpc.php", payload, headers)

        res = conn.getresponse()
        data = res.read()

        token = json.loads(data.decode("utf-8"))["result"]

        print('##############################################################')

        payload = '{"jsonrpc": "2.0", "method": "apiinfo.version", "id": 1}'

        print(payload)

        conn.request("POST", "/api_jsonrpc.php", payload, headers)

        res = conn.getresponse()
        data = res.read()

        print(data.decode("utf-8"))

        print('##############################################################')

        # payload = '{{"jsonrpc": "2.0", "method": "service.get",\
        # "params": {{ "output": "extend", "selectDependencies": "extend" }},\
        # "id": 1, "auth": "{0}"}}'.format(token)

        payload = '{{"jsonrpc": "2.0", "method": "service.get",\
        "params": {{ "output": "extend", "limit": 10 }},\
        "id": 1, "auth": "{0}"}}'.format(token)

        conn.request("POST", "/api_jsonrpc.php", payload, headers)

        res = conn.getresponse()
        data = res.read()

        print(data.decode("utf-8"))

try:
    for i in range(1, 2):
        threading.Thread(target=call_zabix())
except:
    print('Error')
