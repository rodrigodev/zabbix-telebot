import ConfigParser
from pyzabbix import ZabbixAPI

from pyzabbix import ZabbixAPI

zapi = ZabbixAPI("http://10.49.10.161")
zapi.login("dmunhoz", "wsym3k@Dighomem5nh@x")

#print "Connected to Zabbix API Version %s" % zapi.api_version()

#for h in zapi.service.getsla(output="extended",serviceids="2"):
#    print h

#print zapi.service.getsla(output="extended",serviceids="1")

print zapi.service.getsla(
   output="extended",
   serviceids="1",
   intervals=[
      {
         "from": 1451959200,
         "to": 1463089198
      }
   ]
)
#print sla
