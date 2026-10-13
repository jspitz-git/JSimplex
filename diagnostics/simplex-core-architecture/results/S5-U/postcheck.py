"""New post-exit independent stage check; immutable output per distinct stage."""
from common_final import *
import shutil,subprocess
stage=sys.argv[1];h=stage_files(stage);o=out(stage);p=read(o/'process.json');a=read(h/'audit.json');pins=read(h/'pins.json');host=absent([p['runner']['pgid'],p['child']['pgid']])
assert a['all_passed'] is True
shutil.copytree(o,h/'portable')
source={}
for rel in sorted({str(x.relative_to(R)) for d in ('src','test') for x in (R/d).rglob('*') if x.is_file()}):source[rel]=dict(root=sha(R/rel),master=sha(M/rel))
source_same=all(v['root']==v['master'] or (stage=='green' and k==REL and v==dict(root=EXPECTED,master=OLD)) for k,v in source.items())
c={'audit_complete_PASS':len(a['checks'])==25 and a['all_passed'] is True and all(x is True for x in a['checks'].values()),'full_actual_pins':inventory_ok(pins,stage),'raw8_exact_portable':set(a['raw_sha256'])==GREEN_RAW and all(sha(o/n)==sha(h/'portable'/n)==v for n,v in a['raw_sha256'].items()),'invocation3':len(a['invocation_sha256'])==3 and all(sha(k)==v for k,v in a['invocation_sha256'].items()),'actual_candidate_and_prefix':sha(root(stage)/REL)==EXPECTED and (root(stage)/REL).read_bytes()==(H/'original-test.jl').read_bytes()+(T/'append.jl').read_bytes(),'actual_source_test_comparison':len(source)==511 and source_same,'user6':all(sha(k)==v for k,v in read(H/'host-before.json')['user_hashes'].items()),'groups_absent':not host['matches'],'process_exit0':p['reason']=='exit0' and type(p['returncode']) is int and p['returncode']==0}
files={h/'audit.json',h/'pins.json',H/'postcheck.py'}|{p for p in (h/'portable').rglob('*') if p.is_file()}|{Path(k) for k in a['invocation_sha256']}
result=dict(checks=c,all_passed=all(c.values()),source_sha256=source,host=host,sha256={str(k):sha(k) for k in sorted(files)});dump(h/'postcheck.json',result);print(json.dumps(dict(checks=c,bindings=len(files),source_count=len(source))));assert result['all_passed']
