import os
from urllib.parse import urlsplit
from common.runtime import run,request,secret
from collector import collect

def snapshot(source):
 url=os.environ['PROXMOX_URL'].rstrip('/')
 target=urlsplit(url)
 if target.scheme!='https' or not target.hostname or target.username or target.password or target.query or target.fragment:raise ValueError('Proxmox requires an HTTPS URL without credentials')
 if target.path not in ('','/api2/json'):raise ValueError('Use the Proxmox server URL or /api2/json URL')
 if not url.endswith('/api2/json'):url+='/api2/json'
 token=secret('PROXMOX_TOKEN_FILE')
 if any(c.isspace() for c in token) or '!' not in token or '=' not in token:raise ValueError('Use user@realm!token-id=secret')
 headers={'Authorization':'PVEAPIToken='+token}
 def get(path):
  result=request(url+path,headers,ca=os.environ.get('CA_FILE'))
  if not isinstance(result,dict) or 'data' not in result:raise ValueError('Invalid Proxmox response')
  return result['data']
 return collect(get,source,os.environ.get('CLUSTER_NAME','Proxmox VE'))
if __name__=='__main__':run('proxmox',snapshot)
