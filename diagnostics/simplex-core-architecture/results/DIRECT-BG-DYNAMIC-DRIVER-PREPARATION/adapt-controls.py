"""One-shot new source adaptation; never runs a previous launcher/auditor."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];OLD=D.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records={}
# Synthetic test text first. Implementation files are new independent copies.
for n in ['offline-tests.py','control.py','oracle.py','audit.py','seal.py','launch.py']:
 src=OLD/n;s=src.read_text()
 s=s.replace('direct adapter','dynamic BG').replace('adapter driver','dynamic BG driver').replace('adapter phase','dynamic BG phase').replace('Adapter correctness','Dynamic BG correctness')
 s=s.replace("C=R/'diagnostics/direct-lu-policy-adapters/reproduce'","C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'")
 s=s.replace("ENTRY='924e72e9a05634112dc107d6813f9b3a21e4ff54'","ENTRY='d215266d5b4fc8568850208dd210a7f20c23dee8'")
 s=s.replace("(7 if cfg['mode']=='red' else 0)","(8 if cfg['mode']=='red' else 0)")
 with (D/n).open('x') as f:f.write(s)
 records[n]=dict(source=str(src),original_sha256=sha(src),new_sha256=sha(D/n),changes='Scope/log labels; candidate directory; entry commit; RED failure log count8. Remaining safeguards unchanged.')
with (D/'control-adaptation.json').open('x') as f:json.dump(records,f,indent=2);f.write('\n')
print('New Task3 controls and synthetic tests prepared, no seal/launch/audit invoked')
