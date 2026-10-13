"""Exclusive independent author postexit hashes, portable copy and source checks."""
from common import *
import shutil,tomllib
stage=sys.argv[1];h=stage_files(stage);a=read(h/'audit.json');pins=read(h/'pins.json');output=out(stage)
assert a['all_passed'] is True and all(v is True for v in a['checks'].values())
checks=dict(audit_pass=True,pins=inventory_ok(pins,stage),candidate=sha(root(stage)/REL)==EXPECTED,full_raw=set(a['raw_sha256'])==GREEN_RAW,raw_hashes=all(sha(output/k)==v for k,v in a['raw_sha256'].items()),invocations=len(a['invocation_sha256'])==3 and all(sha(k)==v for k,v in a['invocation_sha256'].items()),source_production_equal=not subprocess.check_output(['git','-C',str(R),'diff','master','--','src','.github','Project.toml']),user6=all(sha(k)==v for k,v in read(H/'host-before.json')['user_hashes'].items()),no_groups=not absent([read(output/'process.json')[kind]['pgid'] for kind in ('runner','child')])['matches'])
assert all(checks.values());(h/'portable').mkdir()
for k,v in a['raw_sha256'].items():
 p=h/'portable'/k;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(output/k,p);assert sha(p)==v
checks['portable_identity']=all(sha(h/'portable'/k)==v for k,v in a['raw_sha256'].items())
dump(h/'postcheck.json',dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in [h/'audit.json',h/'pins.json',h/'stage-acceptance.json',h/'launch-binding.json',H/'postcheck.py',root(stage)/REL,*[Path(k) for k in a['invocation_sha256']]]}))
print(stage,'postcheck',len(checks),'PASS')
