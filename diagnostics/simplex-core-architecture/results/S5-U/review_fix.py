"""Exclusive offline stage-binding correction; preserve initial source/manifests."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent
s=(H/'common.py').read_text().replace("H/'common.py'","H/'common_reviewed.py'").replace("H/'launcher.py'","H/'launcher-reviewed.py'").replace("H/'audit.py'","H/'audit-reviewed.py'").replace("H/'required-paths.json'","H/'required-reviewed-paths.json'").replace("H/'admission-acceptance.json'","H/'admission-acceptance-reviewed.json'").replace("H/'admission-pins.json'","H/'admission-reviewed-pins.json'").replace("H/'admission-review.md'","H/'admission-accepted-review.md'")
s=s.replace("H/'failure_tests.py']","H/'failure_tests.py',H/'review_fix.py',H/'reviewed_failure_tests.py',H/'reviewed-failure-tests.json']")
s=s.replace("def invocation_valid(stage,process,pin_hash):",'''def current_refs():
 import subprocess
 return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,M)}
def stage_required(stage):
 paths={str(p) for p in (root(stage)/REL,H/'admission-acceptance-reviewed.json',H/'admission-accepted-review.md',H/'admission-reviewed-pins.json',H/'required-reviewed-paths.json',H/'common_reviewed.py',H/'launcher-reviewed.py',H/'audit-reviewed.py',H/'driver.jl',H/'expected.toml',H/'insertions.toml')}
 if stage=='master':paths|={str(H/'green'/n) for n in ('audit.json','postcheck.json','review.md','pins.json')}
 return paths
def stage_record_valid(a,stage,hashfn=sha,refs=None):
 refs=current_refs() if refs is None else refs
 return (a.get('accepted') is True and a.get('unresolved_findings')==[] and a.get('stage')==stage and a.get('root')==str(root(stage)) and a.get('refs')==refs and a.get('candidate_sha256')==EXPECTED and type(a.get('sha256')) is dict and stage_required(stage).issubset(a['sha256']) and a['sha256'].get(str(root(stage)/REL))==EXPECTED and all(hashfn(k)==v for k,v in a['sha256'].items()))
def stage_accepted(stage):
 a=read(stage_files(stage)/'stage-acceptance.json');assert stage_record_valid(a,stage)
 if stage=='master':
  audit=read(H/'green/audit.json');post=read(H/'green/postcheck.json');review=(H/'green/review.md').read_text()
  assert audit['all_passed'] is True and audit['checks'] and all(v is True for v in audit['checks'].values())
  assert post['all_passed'] is True and post['checks'] and all(v is True for v in post['checks'].values())
  assert {str(H/'green'/n) for n in ('audit.json','pins.json')}.issubset(post['sha256']) and all(sha(k)==v for k,v in post['sha256'].items())
  assert 'ACCEPTED' in review and 'Unresolved findings: []' in review
 return a
def launch_accepted(stage):
 stage_accepted(stage);h=stage_files(stage);p=h/'pins.json';inv=read(p)['inventory']
 required_extra={str(H/n) for n in ('admission-reviewed-pins.json','admission-accepted-review.md','admission-acceptance-reviewed.json')}|{str(h/'stage-acceptance.json')}
 assert required_extra.issubset(inv) and all(sha(k)==inv[k]['sha256'] for k in required_extra)
 b=read(h/'launch-binding.json');keys={str(p),str(H/'admission-acceptance-reviewed.json'),str(h/'stage-acceptance.json'),str(H/'launcher-reviewed.py'),str(H/'audit-reviewed.py')}
 assert b.get('accepted') is True and b.get('unresolved_findings')==[] and b.get('stage')==stage and b.get('command')==command(stage) and keys.issubset(b['sha256']) and all(sha(k)==v for k,v in b['sha256'].items())
 return b

def invocation_valid(stage,process,pin_hash):''')
with (H/'common_reviewed.py').open('x') as f:f.write(s)
s=(H/'launcher.py').read_text().replace('from common import *','from common_reviewed import *').replace("required-paths.json","required-reviewed-paths.json").replace("admission-pins.json","admission-reviewed-pins.json").replace("admission-review.md","admission-accepted-review.md").replace("admission-acceptance.json","admission-acceptance-reviewed.json").replace("H/'launcher.py'","H/'launcher-reviewed.py'")
s=s.replace("files|={str(h/'stage-acceptance.json')};binding=read(h/'stage-acceptance.json');assert binding['accepted'] is True and all(sha(k)==v for k,v in binding['sha256'].items())","files|={str(h/'stage-acceptance.json')};stage_accepted(stage)")
start=s.index(" binding=read(h/'launch-binding.json')");end=s.index(" assert not out(stage).exists()",start);s=s[:start]+" launch_accepted(stage)\n"+s[end:]
with (H/'launcher-reviewed.py').open('x') as f:f.write(s)
s=(H/'audit.py').read_text().replace('from common import *','from common_reviewed import *').replace("admission_bindings=accepted()['accepted'] is True,","admission_bindings=accepted()['accepted'] is True,stage_launch_bindings=launch_accepted(stage)['accepted'] is True,")
with (H/'audit-reviewed.py').open('x') as f:f.write(s)
print('Created separate reviewed variants; original sources untouched')
