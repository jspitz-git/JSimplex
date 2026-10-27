from pathlib import Path
import json,hashlib,subprocess,re,os,datetime,ast
os.environ['GIT_OPTIONAL_LOCKS']='0'
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda n:json.loads((D/n).read_text());git=lambda *a,root=M:subprocess.check_output(['git','-C',str(root),*a]);g=lambda *a,root=M:git(*a,root=root).decode().strip();checks=[];resolutions={}
co=read('production-commit.json');target=co['commit'];parent=co['parent'];hist=read('historical-path-map.json');di=read('diagnostic-index-before.json');old=read('protected-before.json');master=read('MASTER-run/protected-before.json')
assert g('rev-parse','HEAD')==g('rev-parse','master')==g('rev-parse','origin/master')==target
remote=dict((ref,h) for h,ref in (line.split() for line in g('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines()))
assert remote['refs/heads/master']==target and remote['refs/heads/codex/simplex-core-architecture']==g('rev-parse','HEAD',root=R)==read('host-before.json')['diagnostic_head']
assert g('rev-list','--parents','-n','1',target).split()==[target,parent]
assert g('remote','get-url','--push','--all','origin')=='git@github.com:jspitz-git/JSimplex.git'
assert not git('diff','--cached','--raw','-z',root=R)
checks.append('published exact sole-parent master; remote diagnostic ref and real index unchanged')
def resolve(p,h):
 if sha(p)==h:return p
 if p in hist['continuation_before']:q=hist['continuation_before'][p]['before']
 elif p in hist['master_index_before']:q=hist['master_index_before'][p]['before']
 elif p in di:q=di[p]['before']
 else:
  assert Path(p).is_relative_to(M/'src') or Path(p).is_relative_to(M/'test'),p
  q=str(D/'baseline'/Path(p).relative_to(M))
 assert sha(q)==h,(p,q);resolutions[p+'@'+h]=q;return q
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')};assert set(hist['continuation_before'])==allowed
for p,h in old['files'].items():
 q=resolve(p,h)
 if p in allowed:
  v=hist['continuation_before'][p];assert q==v['before'] and v['sha256']==h
  before=Path(q).read_bytes();current=Path(p).read_bytes();assert current.endswith(before) and len(current)>len(before)
  prefix=current[:-len(before)].decode();assert target in prefix and '186622' in prefix
 else:assert q==p
for p,h in master['indexes'].items():assert sha(p)==h
assert hist['master_source_before']==read('integration-historical-path-map.json')['source_before'] and hist['master_index_before']==read('integration-historical-path-map.json')['master_index_before']
assert hist['master_before']==parent
for p,v in hist['master_index_before'].items():assert sha(v['before'])==v['sha256']==old['indexes'][p]
ri=g('rev-parse','--path-format=absolute','--git-path','index',root=R);assert set(di)=={ri} and di[ri]['sha256']==sha(di[ri]['before'])==old['indexes'][ri]==sha(ri)
assert set(g('diff','--name-only','HEAD',root=R).splitlines())=={str(Path(p).relative_to(R)) for p in allowed}
checks.append('exact two changed continuations with verbatim old suffixes; all other protected files/current indexes and old maps preserved')
reviews=['admission.json','result-review.json','production-review.json','publication-preparation-reviewed.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','preparation-review.json']
review_binding_count=0
for n in reviews:
 a=read(n);assert a['accepted'] is True and a['findings']==[],n
 for p,h in a['bindings'].items():resolve(p,h);review_binding_count+=1
checks.append('all twelve completed independent reviews accepted with '+str(review_binding_count)+' verified bindings')
phasecounts={}
for phase in [D,D/'RED-run',D/'GREEN-run',D/'MASTER-run']:
 pins=json.loads((phase/'pins.json').read_text());assert set(pins['inventory'])==set(pins['files']);phasecounts[str(phase.relative_to(D))]=len(pins['inventory'])
 for p,v in pins['inventory'].items():assert str(Path(p).resolve(strict=True))==v['resolved'];resolve(p,v['sha256'])
 for tr in map(Path,pins['trees']):
  expected={str(Path(p).relative_to(tr)) for p in pins['inventory'] if Path(p).is_relative_to(tr)};actual={str(p.relative_to(tr)) for p in tr.rglob('*') if p.is_file()}
  if actual!=expected:
   assert tr in [M/'src',M/'test'];bt=D/'baseline'/tr.relative_to(M);actual={str(p.relative_to(bt)) for p in bt.rglob('*') if p.is_file()}
  assert actual==expected,str(tr)
base=read('baseline-tree.json');assert set(base)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()}
for n,h in base.items():assert sha(D/'baseline'/n)==h
checks.append('all four phase inventories, path resolutions, complete tree memberships and baseline hashes verified')
files=g('ls-tree','-r','--name-only',target,'--','src','test').splitlines();assert len(files)==532
for tree in ['src','test']:assert {str(p.relative_to(M)) for p in (M/tree).rglob('*') if p.is_file()}=={n for n in files if n.startswith(tree+'/')}
for n in files:assert git('show',target+':'+n)==(M/n).read_bytes()==(D/'GREEN'/n).read_bytes()
assert g('diff-tree','--no-commit-id','--name-only','-r',target).splitlines()==read('source-inverse.json')['names']
for n,h in read('source-inverse.json')['candidate_sha256'].items():assert sha(M/n)==h
assert (M/'test/generic_dual_comparisons_tests.jl').read_bytes()==(D/'baseline/test/generic_dual_comparisons_tests.jl').read_bytes()
checks.append('all 532 published/current/tested source-test bytes and exact five changes verified; prior Rational gate unchanged')
for arm in ['GREEN','MASTER']:
 a=read(arm+'-run/audit.json');r=read(arm+'-run/result-review.json');assert a['accepted'] and r['accepted'] and a['passed']==a['total']==r['passed']==r['total']==186622 and a['expected_failures']==r['expected_failures']==r['errors']==r['broken']==r['skipped']==0
 raw=(D/(arm+'-run/output/run.log')).read_text();assert len(re.findall(r'^Quality Devex '+arm+r'\s*\|\s+186622\s+186622\s+',raw,re.M))==1
 assert raw.count('QUALITY_DEVEX_COMPLETED '+arm)==1 and not re.search(r'^ERROR:|Test Failed|Error During Test',raw,re.M)
 inc=re.findall(r'^INCLUDING (.+)$',raw,re.M);expected=json.loads(re.search(r'for file in (\[.*\])',(D/(arm+'-run/tests.jl')).read_text()).group(1));assert inc==expected and len(inc)==len(set(inc))==34
 if arm=='GREEN':green_inc=inc
 else:assert inc==green_inc and raw.startswith('QUALITY_DEVEX_SOURCE /home/jspitz/JSimplex.jl/src/JSimplex.jl\n')
 proc=read(arm+'-run/output/process.json');assert proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True
assert read('MASTER-run/completed.json')['elapsed_shared_seconds']==read('MASTER-run/audit.json')['elapsed_shared_seconds']==1500.4778898909972
assert read('publication.json')['accepted'] and read('publication.json')['normal_nonforce_push'] and read('publication.json')['commit']==target
checks.append('raw GREEN/MASTER ordinary totals and identical 34-file sequence, completion and successful exit; MASTER1500.478s; normal production publication record')
report=(D/'FINAL-REPORT.md').read_text();assert '1.1344,1.1114,1.0122' in report and 'No reuse of that exception' in report and 'Fullsuite/x64/broaderplan/native-memory/end-to-end remain open' in report
for p in allowed:
 before=Path(hist['continuation_before'][p]['before']).read_bytes();prefix=Path(p).read_bytes()[:-len(before)].decode()
 assert target in prefix and '186622' in prefix and 'Fullsuite/broaderS2/S3/S4/S5/S6/x64 remain OPEN' in prefix and 'No automatic new experiment or automation resume' in prefix
checks.append('new report/prefix preserve three slower cells, historical failed exception and open fullsuite/x64/broader scope')
for n in ['closure.py','diagnostic-publish.py','finalize.py','finalization_checks.py']:ast.parse((D/n).read_text());assert sha(D/n)==read('preparation-review.json')['bindings'][str(D/n)]
assert not (D/'closure.json').exists() and not (D/'diagnostic-publication-plan.json').exists() and not (D/'publication-after.json').exists()
checks.append('accepted canonical scripts unchanged; final closure and diagnostic publication remain unexecuted')
seed=read('host-seed.json');host=read('final-host.json');groups=set(seed['groups'])
for p in [D/'output/process.json',*D.glob('*-run/output/process.json')]:
 a=json.loads(p.read_text());groups.update(a[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
assert groups==set(host['groups']) and len(groups)==585 and host['no_Julia'] and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==host['boot_id']==seed['boot_id']
procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();pgid,sid=int(s[2]),int(s[3]);assert pgid not in groups and sid not in groups
  assert not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]);procs.append({'pid':int(p.name),'pgid':pgid,'sid':sid,'start_ticks':int(s[19]),'command':cmd})
 except (FileNotFoundError,ProcessLookupError):pass
checks.append('fresh same-boot observation: all585 historical/current groups AND sessions absent; no Julia')
result={'accepted':True,'checks':checks,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'production_commit':target,'remote_refs':remote,'phase_inventory_counts':phasecounts,'historical_resolutions':resolutions,'no_Julia':True,'no_runner_execution':True,'no_git_mutation':True,'host':{'boot_id':host['boot_id'],'groups':sorted(groups),'processes':procs}}
Path('/tmp/independent-final-closure-check-output.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['host','historical_resolutions']},indent=2));print('unique historical resolutions',len(resolutions))
