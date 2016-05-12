import ConfigParser
from pyzabbix import ZabbixAPI


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

    def get_hostgroup(self, params=None):
        for hostgroup in self.zabbix.hostgroup.get(params):
            print(hostgroup)


zabbix = Zabbix()
zabbix.get_hostgroup('output="extend"')
