import copy,importlib.util,json,os,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('collector',ROOT/'worker/collector.py');collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
def fixture():
 return {'/cluster/resources':[{'type':'node','node':'pve-a','status':'online'},{'type':'node','node':'pve-b','status':'offline'},{'type':'storage','node':'pve-a','storage':'local-lvm','maxdisk':123},{'type':'qemu','node':'pve-a','vmid':100,'name':'Web VM'},{'type':'lxc','node':'pve-a','vmid':101,'name':'DNS'}],'/nodes/pve-a/network':[{'iface':'eth0','type':'eth'},{'iface':'eth1','type':'eth'},{'iface':'bond0','type':'bond','slaves':'eth0 eth1'},{'iface':'vmbr0','type':'bridge','bridge_ports':'bond0','cidr':'192.0.2.2/24'},{'iface':'lo','type':'loopback'}],'/nodes/pve-a/qemu/100/config':{'cores':4,'memory':8192,'net0':'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,tag=10','scsi0':'local-lvm:vm-100-disk-0,size=32G','smbios1':'secret-data','cicustom':'SECRET'},'/nodes/pve-a/lxc/101/config':{'net0':'name=eth0,bridge=vmbr0,ip=192.0.2.10/24,ip6=2001:db8::10/64,trunks=20;30','rootfs':'local-lvm:subvol-101-disk-0,size=8G','password':'SECRET'}}
class CollectorTests(unittest.TestCase):
 def test_import_model_and_no_secrets(self):
  data=collector.collect(fixture().__getitem__,'test-proxmox')
  devices={x['id']:x for x in data['devices']};services={x['id']:x for x in data['services']}
  self.assertEqual(services['qemu-100']['kind'],'Virtual machine');self.assertEqual(services['lxc-101']['kind'],'LXC')
  self.assertEqual(services['qemu-100']['host'],'node-pve-a')
  self.assertEqual(services['lxc-101']['interfaces'][0]['ips'],['192.0.2.10','2001:db8::10'])
  self.assertEqual(services['lxc-101']['interfaces'][0]['taggedVlans'],[20,30])
  self.assertEqual(services['qemu-100']['interfaces'][0]['nativeVlan'],10)
  self.assertEqual(devices['node-pve-a']['interfaces'][0]['lag'],'bond0')
  self.assertEqual(len(data['links']),2)
  self.assertNotIn('SECRET',json.dumps(data));self.assertNotIn('secret-data',json.dumps(data))
  self.assertNotIn('interfaces',devices['node-pve-b'])
 def test_migration_keeps_guest_identity(self):
  data=fixture();first=collector.collect(data.__getitem__,'test-proxmox')
  data['/cluster/resources'][1]['status']='online'
  data['/cluster/resources'][3]['node']='pve-b'
  data['/nodes/pve-b/network']=[];data['/nodes/pve-b/qemu/100/config']=data['/nodes/pve-a/qemu/100/config']
  second=collector.collect(data.__getitem__,'test-proxmox')
  a=next(x for x in first['services'] if x['id']=='qemu-100');b=next(x for x in second['services'] if x['id']=='qemu-100')
  self.assertEqual(a['id'],b['id']);self.assertEqual(b['host'],'node-pve-b')
 def test_failed_endpoint_aborts_snapshot(self):
  data=fixture();del data['/nodes/pve-a/lxc/101/config']
  with self.assertRaises(KeyError):collector.collect(data.__getitem__,'test-proxmox')
 def test_unknown_guest_host_rejected(self):
  data=fixture();data['/cluster/resources'][3]['node']='missing'
  with self.assertRaisesRegex(ValueError,'unknown node'):collector.collect(data.__getitem__,'test-proxmox')
 def test_transport_is_read_only_and_checks_envelope(self):
  sys.path.insert(0,str(ROOT))
  spec=importlib.util.spec_from_file_location('runtime_test',ROOT/'worker/runtime.py');runtime=importlib.util.module_from_spec(spec)
  with patch.dict(sys.modules,{'collector':collector}):spec.loader.exec_module(runtime)
  data=fixture();seen=[]
  def request(url,headers,body=None,ca=None):
   self.assertIsNone(body);self.assertEqual(headers['Authorization'],'PVEAPIToken=atlas@pve!inventory=secret')
   seen.append(url);return {'data':data[url.split('/api2/json',1)[1]]}
  with patch.dict(os.environ,{'PROXMOX_URL':'https://pve.example:8006'}),patch.object(runtime,'secret',return_value='atlas@pve!inventory=secret'),patch.object(runtime,'request',side_effect=request):
   result=runtime.snapshot('test-proxmox');self.assertTrue(result['services']);self.assertTrue(seen)
  with patch.dict(os.environ,{'PROXMOX_URL':'http://pve.example'}),patch.object(runtime,'request') as req:
   with self.assertRaises(ValueError):runtime.snapshot('test-proxmox')
   req.assert_not_called()
