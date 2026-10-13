"""Exclusive post-review S5-U closure. No saved prior script is run or imported."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';H=D/'results/S5-U';T=H.parent/'S5-T'
REL='test/simplex_precision_tests.jl';OLD='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5';NEW='357a976f5fc984025452ee4b259f2fc1f140885212f5b40ff71e072ebfab3684'
STATUS=D/'STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';NEXT=R/'docs/superpowers/plans/2026-10-13-crash-fallback-ownership-contract.md'
cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def read(p):return json.loads(Path(p).read_text())
def mapped(p,d):
 p=Path(p)
 if p in (R/REL,M/REL) and d==OLD:return H/'original-test.jl'
 if p==STATUS:return H/'STATUS.md.before-U'
 if p==ROAD:return H/'2026-10-11-simplex-core-architecture.md.before-U'
 return p
def bindings(data,historical=False):return all(sha(mapped(k,v) if historical else k)==v for k,v in data.items())
def passed(data,n):return data['all_passed'] is True and len(data['checks'])==n and all(v is True for v in data['checks'].values())
def pins(path,n):
 a=read(path);inv=a['inventory']
 return len(inv)==n and all(sha(mapped(k,v['sha256']))==v['sha256'] and str(Path(k).resolve(strict=True))==v['resolved'] for k,v in inv.items())
def git(*args,cwd=R):return subprocess.check_output(['git','-C',str(cwd),*args],text=True)
c={}
c['candidate_both_exact_prefix']=all(sha(r/REL)==NEW and (r/REL).read_bytes()==(H/'original-test.jl').read_bytes()+(T/'append.jl').read_bytes() for r in (R,M))
c['all_admission_inventories_preserved']=all(pins(H/n,num) for n,num in [('admission-pins.json',1446),('admission-reviewed-pins.json',1466),('admission-final-pins.json',1485)])
c['green1489_master1512_preserved']=pins(H/'green/pins.json',1489) and pins(H/'master/pins.json',1512)
c['T891_with_only_old_target_mapping']=len(read(T/'pins.json')['sha256'])==891 and bindings(read(T/'pins.json')['sha256'],True)
c['T_closure25_preserved']=passed(read(T/'closure.json'),14) and len(read(T/'closure.json')['sha256'])==25 and bindings(read(T/'closure.json')['sha256'],True)
c['T_continuation4_preserved']=bindings(read(T/'continuation.json')['sha256'],True)
c['all_three_reviews_accepted']=all('ACCEPTED' in p.read_text() and 'Unresolved findings: []' in p.read_text() for p in (H/'admission-final-review.md',H/'green/review.md',H/'master/review.md'))
c['two_rejections_preserved']=all('REJECTED' in (H/n).read_text() for n in ('admission-review.md','admission-accepted-review.md'))
c['review_copy']=sha(H/'master/review.md')==sha(D/'S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION-REVIEW.md')
c['admission_acceptance28']=len(read(H/'admission-acceptance-final.json')['sha256'])==28 and bindings(read(H/'admission-acceptance-final.json')['sha256'])
RAW={'process.json','pins.json','current.json','run.log','resources.jsonl','raw/case.toml','raw/report.toml','raw/executed-suffix.jl'}
for stage,num in [('green',1489),('master',1512)]:
 h=H/stage;o=R/'.superpowers/simplex-core-architecture/S5-U'/f'{stage}-1';a=read(h/'audit.json');p=read(h/'postcheck.json');proc=read(o/'process.json')
 c[stage+'_audit25_post9']=passed(a,25) and passed(p,9) and a['pin_count']==num and len(p['sha256'])==14 and bindings(p['sha256'])
 c[stage+'_raw8_invocation3']=set(a['raw_sha256'])==RAW and all(sha(o/k)==sha(h/'portable'/k)==v for k,v in a['raw_sha256'].items()) and len(a['invocation_sha256'])==3 and bindings(a['invocation_sha256'])
 c[stage+'_stage_launch_bindings']=all(bindings(read(h/n)['sha256']) for n in ('stage-acceptance.json','launch-binding.json'))
 c[stage+'_single_entry_and_process']=a['entry_counts']==[1,1,1] and a['at_throw']==a['after_unwind'] and proc['reason']=='exit0' and type(proc['returncode']) is int and proc['returncode']==0
source=read(H/'master/postcheck.json')['source_sha256'];c['all511_source_identity']=len(source)==511 and all(sha(R/k)==sha(M/k)==v['root']==v['master'] for k,v in source.items())
c['production_environment_CI_unchanged']=not git('diff','35a6a9f','--','src','.github','Project.toml') and not git('diff','35a6a9f','--','src','.github','Project.toml',cwd=M)
x=read(H/'integration.json');c['exact_test_commit_scope']=git('rev-parse','HEAD').strip()==x['test_commit'] and git('rev-parse','HEAD',cwd=M).strip()==x['master_commit'] and all(git('diff-tree','--no-commit-id','--name-only','-r',rev).splitlines()==[REL] for rev in (x['test_commit'],x['master_commit']))
u=read(H/'host-before.json')['user_hashes'];c['user6']=len(u)==6 and bindings(u)
groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746};matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c['full20groups_noJulia']=not matches
c['continuation_bound']=bindings(read(H/'continuation.json')['sha256']) and 'SOURCE/EVIDENCE-ONLY' in NEXT.read_text() and 'crash-fallback-ownership-contract.md' in STATUS.read_text()
files={p for p in H.rglob('*') if p.is_file()}|{STATUS,ROAD,NEXT,D/'S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION.md',D/'S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-test-integration.md'}
result=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in sorted(files)},historical_mapping='Only old target identities use original-test; prior STATUS/roadmap use before-U. Current launch pins never rewritten.',groups=sorted(groups),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),refs=x,time_ns=time.time_ns())
with (H/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));raise SystemExit(0 if result['all_passed'] else 1)
