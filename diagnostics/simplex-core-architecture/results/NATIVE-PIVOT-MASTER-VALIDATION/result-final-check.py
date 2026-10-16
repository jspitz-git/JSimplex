"""Additional independent Git blob and admission chronology checks; no historical script imports."""
from pathlib import Path
import hashlib,json,subprocess
E=Path(__file__).resolve().parent;D=E.parent/'NATIVE-PIVOT-MASTER-READINESS';A=D/'runs/master300';R=D.parents[3]
def rd(p):return json.loads(p.read_text())
W=Path(rd(D/'production-commit.json')['worktree']);tree=rd(D/'production-tree.json');count=0
for n,blob in tree['git_blobs'].items():
 p=W/n;h=hashlib.sha1();h.update(('blob '+str(p.stat().st_size)+'\0').encode())
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 assert h.hexdigest()==blob,n
 count+=1
ad=rd(E/'master300-admission-final-host.json');pre=rd(A/'prehost.json');proc=rd(A/'output/process.json');post=rd(A/'posthost.json')
assert rd(E/'integration-before.json')['host']['time']<rd(A/'host.json')['time']<ad['time']<pre['time']<proc['started']<proc['ended']<post['time']<rd(E/'result-host.json')['time']
assert rd(E/'master300-admission-checks.json')['check_count']==14687
assert ad['head']==pre['head'] and ad['master']==pre['master'] and ad['boot_id']==pre['boot_id'] and not ad['matches']
for n in ['REPORT.md','continuation-text.md','close.py','publication.py']:
 assert (E/n).is_file()
record=dict(all_passed=True,exact_working_git_blob_checks=count,chronology='integration before seal before final independent admission before launcher prehost before process start/end before posthost before independent result host',admission_checks=14687,scope='Additional read-only Python verification')
with (E/'result-final-checks.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('Supplement PASS',count,'exact Git working blob checks; admission chronology PASS')
