#!/usr/bin/python3
# Autor: Emerson Cesario
# E-mail: emerson.cesario50@gmail.com

from zabbix_api import ZabbixAPI,Already_Exists
import csv
import sys
import getpass

URL = sys.argv[1]
USERNAME = sys.argv[2]
PASSWORD = getpass.getpass("Digite a senha: ")

try:
    zapi = ZabbixAPI(URL, timeout=15, validate_certs=False)
    zapi.login(USERNAME, PASSWORD)
    print(f'Conectado na API do Zabbix, Versao Atual {zapi.api_version()}')
    print ()
except Exception as err:
    print(f'Falha ao conectar na API do zabbix, erro: {err}')

hostname = 'Monitoramento URL'
group = 'Monitoramento URL'

h = zapi.host.get({
    "filter": {"host": [hostname]},
})
hg = zapi.hostgroup.get({
    "filter": {'name': [group]}
})

if not h:
 if not hg:
  zapi.hostgroup.create({"name": group})   
  hg = zapi.hostgroup.get({
    "filter": {"host": [group]},
  })[0]['groupid']
  zapi.host.create({
     "groups": [{ "groupid": hg}],
     "host": hostname,
     "proxy_hostid": "0",
     "interfaces": {
         "type": 1,
         "main": 1,
         "useip": 1,
         "ip": "127.0.0.1",
         "dns": "",
         "port": "10050",
         "details": {
             "version": 2,
             "bulk": 1,
             "community": "{$SNMP_COMMUNITY}"
         }
     }
  })   

hostids = zapi.host.get({
    "output": "extend",
    "filter": {"host": [hostname]},
    "selectHosts": ["hostid", "host"]
    })[0]['hostid']

def create_web(step):         
        try:
           nome = "Web Check " + step
           version = zapi.api_version()
           version.split(".")
           a = version.split(".")
           versao = a[0]
           if versao <= '5':
            try:
             a = zapi.application.get({"output": 'extend',
                                 "hostid": hostids, 
                                 "filter":{'name': "Web Check " +step}
                                 })[0]['applicationid']
            except Exception as IndexError: 
             app = zapi.application.create({"name": "Web Check " +step,
                                 "hostid": hostids})

             a = zapi.application.get({"output": 'extend',
                                 "hostid": hostids, 
                                 "filter":{'name': "Web Check " +step}
                                 })[0]['applicationid']

            create_web = zapi.httptest.create({
              "name": "Web Check "+ step,
              "hostid": hostids,
              "applicationid": a,
              "steps": [
               {
                   "name": nome,
                   "url": step,
                   "status_codes": "200",
                   "no": 1
               }
              ]
            })
            
            trigger = zapi.trigger.create({"description": "Failed step of scenario URL: " + step,
                                "expression": "{"+hostname+":web.test.fail["+nome+"].sum(#3)}>=3",
                                "priority": 5})

           elif versao >= "6":
            create_web = zapi.httptest.create({
              "name": "Web Check "+ step,
              "hostid": hostids,
              "tags": [
                {
                  "tag": "Web Check",
                  "value": step
                }
              ],
              "steps": [
               {
                   "name": nome,
                   "url": step,
                   "status_codes": "200",
                   "no": 1
               }
              ]
            })

            trigger = zapi.trigger.create({"description": "Failed step of scenario URL: " + step,
                                "expression": "sum(/"+hostname+"/web.test.fail["+nome+"],#3)>=3",
                                "priority": 5})
           
           print(f'URL(s) cadastrada {r}')
        except Already_Exists:
           print(f'URL(s) já cadastrada {r}')
        except Exception as err:
           print(f'Falha ao cadastrar a URL(s) {err}')

with open('urls.csv') as file:
    file_csv = csv.reader(file, delimiter=';')
    for [r] in file_csv:
        create_web(step=r)

zapi.logout()
   