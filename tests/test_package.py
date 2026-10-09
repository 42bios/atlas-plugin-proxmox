import ast,hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PackageTests(unittest.TestCase):
 def test_declared_files(self):
  manifest=json.loads((ROOT/'atlas-addin.json').read_text())
  self.assertEqual(manifest['connectorApi'],1)
  self.assertIn(manifest['entrypoint'],[f['path'] for f in manifest['files']])
  for file in manifest['files']:
   path=ROOT/file['path']
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),file['sha256'],file['path'])
   if path.suffix=='.py': ast.parse(path.read_text(),filename=file['path'])
