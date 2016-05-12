from pyzabbix import ZabbixAPI

zapi = ZabbixAPI("http://zabbix.dcb.olx.com.br")
zapi.login("desenvolvimento", "olx123")

print "Connected to Zabbix API Version %s" % zapi.api_version()

for h in zapi.hostgroup.get(output="extend"):
    print h
