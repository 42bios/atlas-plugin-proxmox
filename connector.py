import json,os,runpy,sys
from pathlib import Path
config=json.loads(Path(os.environ['ADDIN_CONFIG_FILE']).read_text())
folder=Path(os.environ['ADDIN_CONFIG_FILE']).parent
credentials=json.loads(Path(os.environ['ADDIN_CREDENTIAL_FILE']).read_text())
token=credentials['tokenId']+'='+credentials['secret']
path=folder/'proxmox_token';path.write_text(token);path.chmod(0o600)
os.environ.update(PROXMOX_URL=config['upstreamUrl'],CLUSTER_NAME=config.get('clusterName','Proxmox VE'),PROXMOX_TOKEN_FILE=str(path),RUN_ONCE='true')
if credentials.get('ca'):
 path=folder/'proxmox_ca';path.write_text(credentials['ca']);path.chmod(0o600);os.environ['CA_FILE']=str(path)
sys.path.insert(0,str(Path(__file__).parent/'worker'))
runpy.run_path(str(Path(__file__).parent/'worker/runtime.py'),run_name='__main__')
