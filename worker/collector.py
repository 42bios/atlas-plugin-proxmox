"""Read-only Proxmox inventory. API responses are reduced to documented fields."""
import ipaddress,re
from urllib.parse import quote

def pairs(value):
 result={}
 for piece in str(value).split(','):
  if '=' in piece:
   k,v=piece.split('=',1);result[k]=v
 return result

def addresses(values):
 result=[]
 for value in values:
  if value and value not in ('dhcp','auto','manual'):
   try: address=str(ipaddress.ip_interface(str(value)).ip)
   except ValueError:continue
   if address not in result:result.append(address)
 return result

def host_interfaces(items):
 result=[]
 for item in items:
  name=item.get('iface')
  if not name or name=='lo':continue
  kind='LAG' if item.get('type')=='bond' else 'Ethernet' if item.get('type')=='eth' else 'Virtual'
  record={'name':name,'type':kind,'ips':addresses([item.get(k) for k in ('cidr','cidr6','address','address6')])}
  if kind=='Virtual':record['connector']='Virtual'
  result.append(record)
 for bond in items:
  if bond.get('type')=='bond':
   for name in str(bond.get('slaves') or bond.get('bond_slaves') or '').split():
    member=next((r for r in result if r['name']==name and r['type']=='Ethernet'),None)
    if member:member['lag']=bond['iface']
 return result

def guest_interfaces(config,kind):
 result=[]
 for key,value in sorted(config.items()):
  if not re.fullmatch(r'net[0-9]+',key):continue
  fields=pairs(value)
  record={'name':fields.get('name',key) if kind=='lxc' else key,'type':'Virtual','connector':'Virtual','ips':addresses([fields.get('ip'),fields.get('ip6')])}
  if fields.get('bridge'):record['bridge']=fields['bridge']
  if fields.get('tag','').isdigit() and 1<=int(fields['tag'])<=4094:record.update(mode='Access',nativeVlan=int(fields['tag']))
  tags=[int(t) for t in re.split(r'[;:]',fields.get('trunks','')) if t.isdigit() and 1<=int(t)<=4094]
  if tags:record.update(mode='Trunk',taggedVlans=sorted(set(tags)))
  result.append(record)
 return result

def collect(get,source,cluster_name='Proxmox VE'):
 resources=get('/cluster/resources')
 if not isinstance(resources,list) or len(resources)>20000:raise ValueError('Invalid or excessive Proxmox inventory')
 nodes={r['node']:r for r in resources if r.get('type')=='node'}
 devices=[];services=[];links=[];guests=[]
 for name,node in sorted(nodes.items()):
  rec={'id':'node-'+name,'name':name,'kind':'Server','model':'Proxmox VE node','ports':0,'proxmox':{'cluster':cluster_name,'node':name}}
  if node.get('status')=='online':
   items=get('/nodes/'+quote(name,safe='')+'/network')
   if not isinstance(items,list) or len(items)>256:raise ValueError('Invalid or excessive node interfaces')
   rec['interfaces']=host_interfaces(items);rec['ports']=sum(i['type']=='Ethernet' for i in rec['interfaces'])
  devices.append(rec)
 storage={}
 for item in resources:
  if item.get('type')=='storage' and item.get('node') in nodes:
   node=item['node'];name=item['storage'];id='storage-'+node+'-'+name
   storage[(node,name)]=id
   services.append({'id':id,'name':name,'kind':'Service','host':'node-'+node,'role':'Storage','group':cluster_name,'proxmox':{'cluster':cluster_name,'node':node,'storage':name,'capacityBytes':item.get('maxdisk',0)}})
  if item.get('type') in ('qemu','lxc'):guests.append(item)
 for item in guests:
  node=item['node'];kind=item['type'];vmid=int(item['vmid'])
  if node not in nodes:raise ValueError('Guest references an unknown node')
  # VMID is cluster-wide; migration changes hosting, not identity.
  rec={'id':kind+'-'+str(vmid),'name':item.get('name') or kind+' '+str(vmid),'kind':'Virtual machine' if kind=='qemu' else 'LXC','host':'node-'+node,'role':'Application','group':cluster_name,'proxmox':{'cluster':cluster_name,'node':node,'vmid':vmid}}
  if kind=='lxc':rec['containerRuntime']='LXC'
  if nodes[node].get('status')=='online':
   config=get('/nodes/'+quote(node,safe='')+'/'+kind+'/'+str(vmid)+'/config')
   if not isinstance(config,dict):raise ValueError('Invalid guest configuration')
   rec['interfaces']=guest_interfaces(config,kind)
   for key in ('cores','sockets','memory','ostype'):
    if key in config:rec['proxmox'][key]=config[key]
   for key,value in config.items():
    if not re.fullmatch(r'(?:scsi|sata|ide|virtio|mp)[0-9]+|rootfs',key):continue
    disk=str(value).split(',')[0];target=storage.get((node,disk.split(':')[0]))
    if target:
     lid=rec['id']+'-uses-'+target
     if not any(l['id']==lid for l in links):links.append({'id':lid,'source':rec['id'],'target':target,'type':'Uses storage'})
  services.append(rec)
 return {'schemaVersion':1,'connector':source,'devices':devices,'services':services,'networks':[],'links':links}
