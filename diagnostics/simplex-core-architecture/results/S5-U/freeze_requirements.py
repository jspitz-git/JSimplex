"""Exclusive offline required-path manifest and host preparation, no Julia."""
from common import *
import subprocess
host=absent();assert not host['matches'];host.update(refs=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines(),remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True),user_hashes=read(T/'host-before.json')['user_hashes'])
assert host['refs']==['a650c0e16f2423fcfc26abcad13f1ecb3f8e408f','35a6a9f4bb61e204b0c61ec9effe96cd9d2de3ab'] and all(x in host['remote'] for x in host['refs']);assert all(sha(k)==v for k,v in host['user_hashes'].items());dump(H/'host-before.json',host)
files=set(read(T/'pins.json')['sha256'])|{str(p) for p in T.rglob('*') if p.is_file()}|{str(p) for p in H.rglob('*') if p.is_file()}|set(map(str,essentials()))|{str(R/'diagnostics/simplex-core-architecture'/n) for n in ('S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION.md','S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION-REVIEW.md')}
for rootpath in (R,M):
 for tree in ('src','test'):
  files|={str(p) for p in (rootpath/tree).rglob('*') if p.is_file()}
 for n in ('Project.toml','Manifest.toml','LocalPreferences.toml'):files.add(str(rootpath/n))
assert sha(R/REL)==sha(M/REL)==OLD and sha(C)==EXPECTED
assert read(H/'failure-tests.json')['all_passed'] is True
req={p:sha(p) for p in sorted(files)};dump(H/'required-paths.json',dict(sha256=req,planned_only_substitutions={str(R/REL):EXPECTED,str(M/REL):EXPECTED},scope='ROOT test only for GREEN, both test paths for master; no other required hash substitution.'))
print('Required paths',len(req))
