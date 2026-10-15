"""UNEXECUTED ordinary source-overlay builder. No Julia or launcher.
Usage (only after separate admission): python3 -B overlay.py reference|candidate TARGET
Target must be a new child of this checkout's .superpowers/native-pivot-qualification.
"""
from common import *
import sys

def build(arm,target):
 require(arm in ('reference','candidate'),'Invalid arm')
 root=R/'.superpowers/native-pivot-qualification'
 target=Path(target).resolve()
 require(target!=root.resolve() and target.is_relative_to(root.resolve()),'Target outside dedicated staging root')
 require(not target.exists(),'Target already exists')
 manifest=rd(Q/'overlay-manifest.json')
 entries=manifest[arm]
 require(len({e['destination'] for e in entries})==len(entries),'Duplicate destination')
 for e in entries:
  d=Path(e['destination'])
  require(not d.is_absolute() and '..' not in d.parts,'Unsafe destination')
  require(sha(e['source'])==e['sha256'],'Source changed '+e['source'])
 target.mkdir(parents=True,exist_ok=False)
 # A failed partial stage is preserved, never reused or overwritten.
 for e in entries:
  out=target/e['destination'];out.parent.mkdir(parents=True,exist_ok=True)
  with out.open('xb') as f:f.write(Path(e['source']).read_bytes())
  require(sha(out)==e['sha256'],'Staged bytes mismatch')
 print(dict(arm=arm,files=len(entries),target=str(target)))

if __name__=='__main__':
 require(len(sys.argv)==3,'Expected arm and target');build(sys.argv[1],sys.argv[2])
