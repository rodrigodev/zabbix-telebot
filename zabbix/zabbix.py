import ConfigParser
from pyzabbix import ZabbixAPI

config = ConfigParser.ConfigParser()
config.read('prod.cfg')

zabbix_server = config.get('ZABBIX', 'SERVER')
zabbix_api_user = config.get('ZABBIX', 'API_USER')
zabbix_api_pass = config.get('ZABBIX', 'API_PASSWORD')

zabbix = ZabbixAPI(zabbix_server)
zabbix.login(zabbix_api_user, zabbix_api_pass)

print "Connected to Zabbix API Version %s" % zabbix.api_version()

for hostgroup in zabbix.hostgroup.get(output="extend"):
    print hostgroup["name"].encode("utf-8")
