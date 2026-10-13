import importlib.util, unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('proxmox_variants',Path(__file__).resolve().parents[1]/'worker/collector.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
class Variations(unittest.TestCase):
 def test_dynamic_addresses_not_invented_and_dual_stack_normalized(self):
  self.assertEqual(c.addresses(['dhcp','auto','manual','bad','192.0.2.2/24','192.0.2.2','2001:db8::2/64']),['192.0.2.2','2001:db8::2'])
 def test_invalid_tags_ignored_and_trunk_tags_deduplicated(self):
  r=c.guest_interfaces({'net0':'name=eth0,tag=4095,trunks=20;20;0;4095;30','password':'NEVER_EXPORT'},'lxc')[0]
  self.assertNotIn('nativeVlan',r);self.assertEqual(r['taggedVlans'],[20,30]);self.assertNotIn('NEVER_EXPORT',str(r))
 def test_interface_names_with_digits_sorted_and_no_fake_ips_for_qemu(self):
  r=c.guest_interfaces({'net10':'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0','net2':'e1000=AA:BB:CC:DD:EE:01'},'qemu')
  self.assertEqual({i['name'] for i in r},{'net2','net10'});self.assertTrue(all(not i['ips'] for i in r))
 def test_empty_cluster_and_excessive_resources(self):
  self.assertEqual(c.collect(lambda _:[],'test')['devices'],[])
  for value in ({},None,[{}]*20001):
   with self.assertRaises(ValueError):c.collect(lambda _:value,'test')
 def test_offline_nodes_do_not_query_unreachable_guests(self):
  seen=[]
  def get(path):
   seen.append(path);return [{'type':'node','node':'offline','status':'offline'},{'type':'qemu','node':'offline','vmid':7}]
  r=c.collect(get,'test');self.assertEqual(seen,['/cluster/resources']);self.assertEqual(r['services'][0]['host'],'node-offline');self.assertNotIn('interfaces',r['services'][0])
