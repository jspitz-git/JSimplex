from pathlib import Path
import json,hashlib,importlib.util,subprocess,os,re,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');P=D/'MASTER-run';M=Path('/home/jspitz/JSimplex.jl');G=D/'GREEN';BASE='bb765d008c6e8aab6187aa0ea49d49a4f8a03309';TARGET='85f8275b85183f87fa8f33164cb0fbb5115f17ec'
sp=importlib.util.spec_from_file_location('rpc_master_admission_common',P/'common.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(args,env=None):return subprocess.check_output(['/usr/bin/git','-C',str(M),*args],env=env)
def tree(raw):
 out={}
 for line in raw.split(b'\0'):
  if not line:continue
  meta,n=line.split(b'\t',1);mode,kind,oid=meta.decode().split();out[n.decode()]=(mode,kind,oid)
 return out
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
c.unchanged();pins=read(P/'pins.json');assert len(pins['inventory'])==804
co=read(D/'production-commit.json');cr=read(D/'commit-review.json');st=read(D/'staged-tree.json');iv=read(D/'source-inverse.json');gr=read(D/'GREEN-run/result-review.json');gc=read(D/'GREEN-run/contract.json');con=read(P/'contract.json');hist=read(D/'integration-historical-path-map.json');before=read(D/'integration-before.json');after=read(D/'integration-after.json');protected=read(D/'protected-before.json');baseline=read(D/'baseline-tree.json')
assert cr['accepted'] is True and cr['findings']==[] and gr['accepted'] is True and gr['findings']==[]
assert co['commit']==cr['commit']==TARGET==c.TARGET and co['parent']==cr['parent']==st['base']==iv['production_baseline']==BASE
assert git(['rev-list','--parents','-n','1',TARGET]).decode().split()==[TARGET,BASE]
assert git(['rev-parse',TARGET+'^{tree}']).decode().strip()==co['tree']==cr['tree']==st['tree']
assert git(['branch','--show-current']).decode().strip()=='master'
assert git(['rev-parse','HEAD']).decode().strip()==git(['rev-parse','master']).decode().strip()==TARGET
assert git(['rev-parse',co['branch']]).decode().strip()==TARGET
assert git(['rev-parse','origin/master']).decode().strip()==BASE==git(['ls-remote','origin','refs/heads/master']).decode().split()[0]
assert c.git(['rev-parse','HEAD'],c.R)=='94394f8b91a4670c24f7fb9e7c23c468e4cadfd4'==c.git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],c.R).split()[0]
rawold=git(['ls-tree','-r','-z',BASE]);rawnew=git(['ls-tree','-r','-z',TARGET]);old=tree(rawold);new=tree(rawnew)
assert len(old)==3559 and len(new)==3560 and hashlib.sha256(rawnew).hexdigest()==cr['full_tree_sha256']
names=co['names'];assert names==st['names']==iv['names']==cr['changed_paths']
assert sorted(n for n in set(old)|set(new) if old.get(n)!=new.get(n))==names
assert set(new)-set(old)=={'test/generic_residual_pivot_crash_tests.jl'} and not set(old)-set(new)
assert {str(p.relative_to(G)) for p in G.rglob('*') if p.is_file()}==set(iv['whole_stage']) and len(iv['whole_stage'])==543
for n,h in iv['whole_stage'].items():
 assert sha(G/n)==sha(M/n)==h,n
 if n in new:assert new[n]==('100644','blob',blob((G/n).read_bytes())),n
for n in names:assert new[n]==('100644','blob',co['blobs'][n]) and co['blobs'][n]==st['blobs'][n] and sha(M/n)==st['sha256'][n]==iv['candidate_sha256'][n]
for ch in read(D/'changes.json'):
 b=(D/'baseline'/ch['file']).read_text();now=(M/ch['file']).read_text();assert b.count(ch['old'])==1 and now==b.replace(ch['old'],ch['new'],1)
assert (M/'test/generic_residual_pivot_crash_tests.jl').read_bytes()==(D/'new-test.jl').read_bytes()
assert (M/'test/runtests.jl').read_text()==(D/'baseline/test/runtests.jl').read_text()+'\ninclude("generic_residual_pivot_crash_tests.jl")\n'
for root in ['src','test']:
 actual={str(p.relative_to(M)) for p in (M/root).rglob('*') if p.is_file()};tested={str(p.relative_to(G)) for p in (G/root).rglob('*') if p.is_file()};bound={str(Path(n).relative_to(M)) for n in pins['inventory'] if Path(n).is_relative_to(M/root)}
 assert actual==tested==bound
# Prove exact beforeimage maps before using any historical resolution.
main_index=git(['rev-parse','--path-format=absolute','--git-path','index']).decode().strip()
assert hist['master_before']==BASE and hist['older_maps_preserved'] is True
expected_existing={str(M/n):n for n in names if n in baseline}
assert set(hist['source_before'])==set(expected_existing) and set(hist['master_index_before'])=={main_index}
for actual,n in expected_existing.items():
 v=hist['source_before'][actual];assert v==dict(before=str(D/'baseline'/n),sha256=baseline[n]);assert sha(v['before'])==v['sha256']
 assert old[n]==('100644','blob',blob(Path(v['before']).read_bytes()))
idx=hist['master_index_before'][main_index];assert idx==dict(before=str(D/'before-master/master.index'),sha256=protected['indexes'][main_index]);assert sha(idx['before'])==idx['sha256']
assert {str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()}==set(baseline) and len(baseline)==542
for n,h in baseline.items():assert sha(D/'baseline'/n)==h
before_entries=git(['ls-files','--stage','-z'],env=dict(os.environ,GIT_INDEX_FILE=idx['before'],GIT_OPTIONAL_LOCKS='0')).decode().split('\0')
assert before_entries==before['entries'] and before['target']==TARGET
now_entries=git(['ls-files','--stage','-z']).decode().split('\0')
def unrelated(entries):return [x for x in entries if x and x.split('\t',1)[1] not in names]
assert unrelated(now_entries)==unrelated(before_entries)
assert git(['diff','--cached','--raw','-z']).decode()==before['staged']==''
for entry in now_entries:
 if entry:
  meta,n=entry.split('\t',1);mode,oid,stage=meta.split();assert stage=='0' and new[n]==(mode,'blob',oid)
assert after==dict(fast_forward=True,protected_unchanged=True,pushed=False,target=TARGET,unrelated_indexes_unchanged=True)
assert sha(idx['before'])==idx['sha256'],'read-only beforeindex unchanged'
# Historical manifests/bindings: map only the four explicitly changed existing paths and original main index.
mapfiles={**hist['source_before'],**hist['master_index_before']};used={};cache={}
def digest_cached(p):
 p=str(p)
 if p not in cache:cache[p]=sha(p)
 return cache[p]
def historical(path,want):
 path=str(path)
 if digest_cached(path)==want:return path
 assert path in mapfiles,'unmapped historical drift '+path
 v=mapfiles[path];assert v['sha256']==want and digest_cached(v['before'])==want,'wrong exact beforeimage '+path
 used[path]=v;return v['before']
manifest_checks=[]
for rel,count in [('pins.json',1251),('pins-ready.json',1268),('pins-final.json',1285),('output/pins.json',1285),('RED-run/pins.json',1328),('RED-run/output/pins.json',1328),('GREEN-run/pins.json',1329),('GREEN-run/output/pins.json',1329)]:
 man=read(D/rel);assert len(man['inventory'])==count
 for n,v in man['inventory'].items():
  assert str(Path(n).resolve(strict=True))==v['resolved'];historical(n,v['sha256'])
 for root in man['trees']:
  root=Path(root);expected={n for n in man['inventory'] if Path(n).is_relative_to(root)}
  if root in [M/'src',M/'test']:
   actual={str(M/n) for n in baseline if Path(n).is_relative_to(root.relative_to(M))}
  else:actual={str(p) for p in root.rglob('*') if p.is_file()}
  assert actual==expected,'historical membership '+str(root)
 manifest_checks.append(dict(path=str(D/rel),count=count,sha256=sha(D/rel)))
for rel in ['admission.json','admission-final.json','result-review.json','RED-run/admission.json','RED-run/result-review.json','production-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','commit-review.json','publication-preparation-reviewed.json']:
 for n,h in read(D/rel)['bindings'].items():historical(n,h)
for n,h in protected['files'].items():assert sha(n)==h
for n,h in protected['indexes'].items():historical(n,h)
assert set(used)==set(mapfiles)
assert con['source_root']==str(M) and con['arm']=='MASTER' and con['attempts']==1 and con['expected_exit']==0 and con['expected_failures']==0 and con['expected_failure_locations']==[]
assert con['expected_total']==gr['required_MASTER_total']==gr['total']==cr['required_MASTER_total']==362111
assert con['files']==gc['files']==gr['required_MASTER_files'] and len(con['files'])==len(set(con['files']))==67
assert con['shared_limit_seconds']==3600 and con['guard_limit_seconds']==3592
assert (P/'tests.jl').read_text()==(D/'GREEN-run/tests.jl').read_text().replace(str(G),str(M)).replace('GREEN','MASTER')
assert con['command']==[x.replace(str(D/'GREEN-run/tests.jl'),str(P/'tests.jl')).replace('--project='+str(G),'--project='+str(M)) for x in gc['command']]
# Launch and guard are the same admitted implementation; only common pins/ref targets change.
assert (P/'launch.py').read_bytes()==(D/'GREEN-run/launch.py').read_bytes()
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (P/'guard'/n).read_bytes()==(D/'guard'/n).read_bytes()
expected_common=(D/'GREEN-run/common.py').read_text().replace("TARGET='"+BASE+"'","TARGET='"+TARGET+"'").replace("==git(['rev-parse','origin/master'])==TARGET","==TARGET and git(['rev-parse','origin/master'])=='"+BASE+"'")
assert (P/'common.py').read_text()==expected_common
assert sha(D/'phase-audit.py')==sha(D/'GREEN-run/audit.py') and str(D/'phase-audit.py') in pins['inventory']
assert not any((P/n).exists() for n in ['output','reservation.json','completed.json'])
# Independently verify GREEN's ordered all-pass root and binding to its source tree.
log=(D/'GREEN-run/output/run.log').read_text();assert re.findall(r'^INCLUDING (.*)$',log,re.M)==con['files']
assert not re.search(r'Test Failed|Error During Test|^ERROR:|Test Broken',log,re.M)
line=next(x for x in log.splitlines() if x.startswith('Residual pivot crash GREEN') and '|' in x);assert line.split('|')[1].split()[:2]==['362111','362111']
assert log.count('RPC_COMPLETED GREEN')==1
host=c.host();assert len(host['groups'])==665 and host['no_Julia'] is True and host['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb'
e=dict(accepted=True,commit=TARGET,parent=BASE,tree=co['tree'],full_tree_entries=3560,full_tree_sha256=hashlib.sha256(rawnew).hexdigest(),changed_paths=names,stage_files=543,actual_master_matches_complete_tested_stage=True,index_beforeimage_verified=True,current_index_entries_match_commit=True,unrelated_index_entries_and_staging_preserved=True,historical_manifests=manifest_checks,exact_historical_resolutions=used,MASTER_pins=804,ordered_files=con['files'],expected_total=362111,host=host)
with (P/'admission-evidence.json').open('x') as f:json.dump(e,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in e.items() if k not in ['host','ordered_files','exact_historical_resolutions','historical_manifests']}));print(json.dumps(dict(time=host['time_utc'],groups=len(host['groups']),available_kib=host['available_kib'],swap_used_kib=host['swap_used_kib'],no_Julia=host['no_Julia'])))
