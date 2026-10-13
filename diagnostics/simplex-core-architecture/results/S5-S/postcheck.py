"""Exclusive independent post-exit comparison; never rerun audit or numerics."""
from common_final import *
import shutil,subprocess,tomllib
p=read(O/'process.json');a=read(H/'audit.json');pins=read(O/'pins.json');raw=tomllib.loads((O/'report.toml').read_text())
groups=absent([p['runner']['pgid'],p['child']['pgid']]);assert not groups['matches']
dest=H/'qualification-1';dest.mkdir()
for f in O.iterdir():
 if f.is_file():shutil.copyfile(f,dest/f.name)
samples=[json.loads(x) for x in (O/'resources.jsonl').read_text().splitlines()]
checks={'full856':len(pins['inventory'])==856 and inventory_ok(pins),'auditor19':len(a['checks'])==19 and all(v is True for v in a['checks'].values()) and a['all_passed'] is True,'literal40':len(raw['checks'])==40 and all(v is True for v in raw['checks'].values()),'portable6':len(a['raw_sha256'])==6 and all(sha(O/n)==sha(dest/n)==v for n,v in a['raw_sha256'].items()),'guard3':all(sha(n)==v for n,v in a['invocation_sha256'].items()),'candidate_source':sha(C)==EXPECTED,'source_test_CI_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),'user6':all(sha(f)==v for f,v in read(H/'host-before.json')['user_hashes'].items()),'groups_absent':not groups['matches']}
out=dict(checks=checks,all_passed=all(checks.values()),groups=groups,resources=dict(samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_used_kib=max(x['swap_used_kib'] for x in samples),elapsed_including_launch=p['elapsed_including_launch']),sha256={str(f):sha(f) for f in [H/'postcheck.py',H/'audit.json',H/'launch-binding.json',H/'prelaunch-acceptance.json',*dest.iterdir()]})
dump(H/'postcheck.json',out);print(json.dumps(out));assert out['all_passed']
