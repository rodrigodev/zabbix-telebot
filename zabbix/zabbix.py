#!/usr/bin/env python
# coding=utf-8

import ConfigParser
from pyzabbix import ZabbixAPI
import time
import json


class Zabbix(object):

    def __init__(self):
        self.__get_server_config()
        self.__login()

    def __get_server_config(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('prod.cfg')

        self.server_address = self.config.get('ZABBIX', 'SERVER')
        self.api_user = self.config.get('ZABBIX', 'API_USER')
        self.api_pass = self.config.get('ZABBIX', 'API_PASSWORD')

    def __login(self):
        self.zabbix = ZabbixAPI(self.server_address)
        self.zabbix.login(self.api_user, self.api_pass)

    def get_hostgroups(self, params=None):
        return [hostgroup for hostgroup
                in self.zabbix.hostgroup.get(output=['name', 'groupid'])]

    def get_hosts_by_hostgroup(self, hostgroup):
        return [host for host
                in self.zabbix
                .host.get(output=['name', 'hostid'],
                          groupids=['{}'
                                    .format(hostgroup[0])])]

    def get_active_triggers_by_hostgroup(self, hostgroup):
        return [trigger for trigger
                in self.zabbix
                .trigger.get(output=['hosts', 'description'],
                             only_true=1,
                             skipDependent=1,
                             monitored=1,
                             active=1,
                             selectHosts='extend',
                             expandDescription=1,
                             expandData='host',
                             group=hostgroup)]

    def get_slachat(self, params=None):
        timestampnow = time.time()
        j = json.loads(json.dumps(self.zabbix.service.getsla(output="extended",serviceids="1",intervals=[{"from":timestampnow - 2628000,"to":timestampnow}])))
        sla = '{} %'.format(j['1']['sla'][0]['sla'])
        return sla

    def get_events(self):
        return [trigger for trigger
            in self.zabbix
            .trigger.get(output="extend",
                         sortfield=['lastchange'],
                         sortorder= "DESC",
                         withUnacknowledgedEvents=1,
                         only_true=1,
                         monitored=1,
                         active=1,
                         selectHosts='extend',
                         selectLastEvent=1,
                         expandDescription=1,
                         expandData='host',
                         triggerid=16083,
                         limit=1)]




#         events = self.zabbix.event.get(output=["eventid", "relatedObject", "hosts"], sortorder='DESC', selectHosts=1, selectRelatedObject=1, limit=10)
#
#         result = []
#
#         for event in events:
#             event_info = {}
#
#             event_info['eventid'] = event['eventid']
#             event_info['host'] = [host for host in self.zabbix.host.get(output=['name', 'hostid'], hostid=event['hosts'][0]['hostid'])][0]
#
#
#             if 'triggerid' in event['relatedObject'].keys():
#                 event_info['related_object'] = [trigger for trigger
#                         in self.zabbix
#                         .trigger.get(output=['triggerid', 'description', 'priority'],
#                                      triggerids=['{}'
#                                                .format(event['relatedObject']['triggerid'])],
#                                      expandDescription=1,
#                                      active=1)][0]
#
#             result.append(event_info)
#
# #         print result.keys()
# #         print result[result.keys()[0]]['host']
# #         print result[result.keys()[0]]['related_object']
# #
#         return result
#
z = Zabbix()
print(z.get_events())
