import importlib.util, os, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('transport_checks',ROOT/'common/runtime.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class TransportFailures(unittest.TestCase):
 def test_failed_collection_reports_error_without_snapshot(self):
  requests=[]
  def request(url,headers,body=None,**kwargs):requests.append((url,body))
  with patch.dict(os.environ,{'CONNECTOR_ID':'test','ATLAS_URL':'https://atlas.example','RUN_ONCE':'true'}),patch.object(r,'secret',return_value='DUMMY_TOKEN'),patch.object(r,'request',side_effect=request),patch('builtins.print') as printed:
   with self.assertRaises(SystemExit):r.run('test',lambda _:(_ for _ in ()).throw(RuntimeError('PRIVATE_UPSTREAM_BODY')))
  self.assertFalse(any(url.endswith('/snapshot') for url,_ in requests));self.assertEqual(requests[0][1]['phase'],'error');self.assertNotIn('PRIVATE_UPSTREAM_BODY',str(printed.call_args_list))
 def test_redirect_does_not_forward_credentials(self):
  with self.assertRaises(ValueError):r.NoRedirect().redirect_request(None,None,302,'redirect',{},'https://different.example')
