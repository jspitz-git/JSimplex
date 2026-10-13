"""One-use offline preparation closure and exact fail-fast publication."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S4-AC';A=D.parent/'S4-AB'
BASE='fd8f414510d40cfb2f1e93ce21a60b5be5b522b8';MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
CONT=('diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')
EXTERNAL=(*CONT,'diagnostics/simplex-core-architecture/S4-MARKOWITZ-ROW-COUNT-TEST-PREPARATION.md','docs/superpowers/plans/2026-10-13-markowitz-row-count-integration.md')
NAMES=('host.json','STATUS.md.before-S4-AC','roadmap.md.before-S4-AC','continuation-map.json','test-append.jl','prepare.py','original-test.jl','candidate-test.jl','candidate-source.jl','preparation.json','continuation-host.json','review.md','review.json','publication.py')
FILES=tuple(sorted((*EXTERNAL,*(str((D/n).relative_to(R)) for n in NAMES))))
CLOSURE=str((D/'closure.json').relative_to(R));PUBLICATION=str((D/'publication.json').relative_to(R));FINAL=tuple(sorted((*FILES,CLOSURE,PUBLICATION)))
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git','-C',str(R),*a],text=True).strip()
def hashes(record,mapping=None):
 for p,h in record['sha256'].items():
  q=Path(p);q=q if q.is_absolute() else R/q;rel=str(q.relative_to(R)) if q.is_relative_to(R) else str(q)
  if mapping and rel in mapping:q=R/mapping[rel]['saved_path']
  require(sha(q)==h,'hash '+p)
def inventory(expected):
 require({str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}=={p for p in expected if p.startswith(str(D.relative_to(R))+'/')},'evidence completeness')
 require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(expected)-set(CONT)|{'Manifest.toml','LocalPreferences.toml'},'untracked completeness')
def scope():
 require(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs')
 require(subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip()==MASTER,'primary ref')
 require(not git('diff','--cached','--name-only'),'empty index')
 require(set(git('diff','--name-only').splitlines())==set(CONT),'tracked scope')
 require(not git('diff','master','--','src','test','.github','Project.toml'),'actual production/test/CI/environment')
def host():
 groups=set(read(D/'host.json')['groups']);matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split();comm=(p/'comm').read_text().strip()
   if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 require(len(groups)==34 and not matches,'fresh34groups ANDsessions/noJulia')
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches)
def closure():
 scope();inventory(FILES);h=host();mapping=read(D/'continuation-map.json')['mapping']
 for n in ('result-review.json','closure.json','publication.json'):hashes(read(A/n),mapping)
 for rel,v in mapping.items():
  require(sha(R/v['saved_path'])==v['sha256'],'before hash')
  require(subprocess.check_output(['git','-C',str(R),'show',BASE+':'+rel])==(R/v['saved_path']).read_bytes(),'before committed bytes')
 prep=read(D/'preparation.json');require(prep['all_passed'] is True and len(prep['checks'])==12 and all(v is True for v in prep['checks'].values()),'offline preparation');hashes(prep)
 require((D/'candidate-source.jl').read_bytes()==(A/'candidate-source.jl').read_bytes(),'exact qualified candidate')
 require((D/'candidate-test.jl').read_bytes()==(D/'original-test.jl').read_bytes()+(D/'test-append.jl').read_bytes(),'exact append')
 require((D/'original-test.jl').read_bytes()==(R/'test/markowitz_workspace_reuse_allocation_tests.jl').read_bytes(),'actual test prefix')
 rv=read(D/'review.json');require(rv['accepted'] is True and rv['unresolved_findings']==[] and all(v is True for v in rv['checks'].values()),'independent review');hashes(rv)
 require('ACCEPTED S4-AC offline preparation.' in (D/'review.md').read_text(),'review marker')
 checks=dict.fromkeys(('refs_and_scope','exact_complete_files','fresh34groups_ANDsessions_noJulia','all_AB_final_bindings_preserved','exact_before_texts','twelve_offline_preparation_checks','all28_preparation_bindings','exact_qualified_source','exact_test_append','unchanged_actual_test_prefix','independent_review_accepted','all_review_bindings','actual_production_test_env_CI_unchanged'),True)
 dump(D/'closure.json',dict(all_passed=True,checks=checks,sha256={q:sha(R/q) for q in FILES},host=h,previous_AB_mapping=mapping,scope='Offline source/test preparation only; no Julia syntax/runtime/numerical qualification.'))
 print(json.dumps(dict(closure_passed=True,checks=len(checks),bindings=len(FILES))),flush=True)
def publish():
 scope();inventory((*FILES,CLOSURE));c=read(D/'closure.json');require(c['all_passed'] is True and all(c['checks'].values()),'separate PASS closure');hashes(c)
 require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={BASE+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote refs')
 nonself=tuple(sorted((*FILES,CLOSURE)));subprocess.run(['git','-C',str(R),'add','--',*nonself],check=True)
 require(tuple(git('diff','--cached','--name-only').splitlines())==nonself,'staged names')
 for q in nonself:require(subprocess.check_output(['git','-C',str(R),'show',':'+q])==(R/q).read_bytes(),'staged blob '+q)
 subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
 dump(D/'publication.json',dict(all_passed=True,checks=dict.fromkeys(('separate_closure_PASS','fixed_complete_names','exact_nonself_staged_names_blobs','diff_clean','remote_refs'),True),expected_staged_names=list(FINAL),sha256={q:sha(R/q) for q in nonself},self_exclusion='Own recursive hash excluded; all final staged and committed blobs verified before push.'))
 subprocess.run(['git','-C',str(R),'add','--',PUBLICATION],check=True)
 require(tuple(git('diff','--cached','--name-only').splitlines())==FINAL,'final staged names')
 for q in FINAL:require(subprocess.check_output(['git','-C',str(R),'show',':'+q])==(R/q).read_bytes(),'final staged blob '+q)
 require(set(git('ls-files','--others','--exclude-standard').splitlines())=={'Manifest.toml','LocalPreferences.toml'},'untracked after staging')
 subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
 print(json.dumps(dict(exact_staged_blobs=len(FINAL),all_passed=True)),flush=True)
 subprocess.run(['git','-C',str(R),'commit','-m','diagnostics: prepare permanent Markowitz row-count regression'],check=True)
 commit=git('rev-parse','HEAD');require(tuple(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())==FINAL,'committed names')
 for q in FINAL:require(subprocess.check_output(['git','-C',str(R),'show',commit+':'+q])==(R/q).read_bytes(),'committed blob '+q)
 subprocess.run(['git','-C',str(R),'push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
 require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={commit+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote verification')
 print(json.dumps(dict(commit=commit,master=MASTER,exact_committed_blobs=len(FINAL),remote_verified=True)),flush=True)
if __name__=='__main__':
 require(len(sys.argv)==2 and sys.argv[1] in ('closure','publish'),'phase')
 (closure if sys.argv[1]=='closure' else publish)()
