from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
path=root/'atlas-addin.json'
manifest=json.loads(path.read_text())
for file in manifest['files']:
 file['sha256']=hashlib.sha256((root/file['path']).read_bytes()).hexdigest()
path.write_text(json.dumps(manifest,indent=2)+'\n')
