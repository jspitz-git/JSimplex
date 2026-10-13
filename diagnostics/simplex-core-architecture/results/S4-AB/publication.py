"""New one-use closure, then exact fail-fast publication. No numerics."""
from common import *
import tomllib
BASE='e80249a1687be8bde2a9fa4123230e7b8662d99b'
MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
CONT=('diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')
EXTERNAL=(*CONT,'diagnostics/simplex-core-architecture/S4-MARKOWITZ-ROW-COUNT-QUALIFICATION.md','docs/superpowers/plans/2026-10-13-markowitz-row-count-fusion.md')
NAMES=(
 'STATUS.md.before-S4-AB','roadmap.md.before-S4-AB','host.json','continuation-map.json',
 'prepare.py','original-construct.jl','candidate-source.jl','candidate-methods.jl','source-checks.json',
 'driver.jl','plan.md','authorization.json','guard.py','common.py','launcher.py','audit.py','oracle.py',
 'postcheck.py','admission_prepare.py','preparation.json','required-paths.json','launch-pins.json',
 'numerical-review.md','review.json','prelaunch-host.json','allowance.json','attempt-reserved.json',
 'launcher.log','invocation.json','audit.json','postcheck.json','prepublication-host.json',
 'qualification-1/current.json','qualification-1/pins.json','qualification-1/process.json',
 'qualification-1/qualification.toml','qualification-1/resources.jsonl','qualification-1/run.log',
 'result-review.md','result-review.json','publication.py')
FILES=tuple(sorted((*EXTERNAL,*(str((D/n).relative_to(R)) for n in NAMES))))
CLOSURE=str((D/'closure.json').relative_to(R));PUBLICATION=str((D/'publication.json').relative_to(R))
FINAL=tuple(sorted((*FILES,CLOSURE,PUBLICATION)))
def git(*args):return subprocess.check_output(['git','-C',str(R),*args],text=True).strip()
def hashes_ok(record,mapping=None):
 for p,h in record['sha256'].items():
  q=Path(p);q=q if q.is_absolute() else R/q
  rel=str(q.relative_to(R)) if q.is_relative_to(R) else str(q)
  if mapping and rel in mapping:q=R/mapping[rel]['saved_path']
  require(sha(q)==h,'binding changed: '+p)
def inventory(expected):
 actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}
 require(actual=={p for p in expected if p.startswith(str(D.relative_to(R))+'/')},'exact evidence completeness')
 require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(expected)-set(CONT)|{'Manifest.toml','LocalPreferences.toml'},'exact untracked completeness')
def refscope():
 require(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs changed')
 require(refs()==read(D/'allowance.json')['refs'],'primary refs changed')
 require(not git('diff','--cached','--name-only'),'index nonempty')
 require(set(git('diff','--name-only').splitlines())==set(CONT),'tracked scope')
 require(not git('diff','master','--','src','test','.github','Project.toml'),'production/test/environment/CI')
def closure():
 refscope();inventory(FILES)
 mapping=read(D/'continuation-map.json')['mapping'];previous=D.parent/'MA-B'
 for n in ('review.json','closure.json','publication.json'):hashes_ok(read(previous/n),mapping)
 for rel,v in mapping.items():
  require(sha(R/v['saved_path'])==v['sha256'],'mapped hash')
  require(subprocess.check_output(['git','-C',str(R),'show',BASE+':'+rel])==(R/v['saved_path']).read_bytes(),'exact before text')
 require(manifest_ok(read(D/'launch-pins.json'),read(D/'required-paths.json')),'624 launch pins')
 for n in ('source-checks.json','review.json','audit.json','postcheck.json'):hashes_ok(read(D/n))
 rv=read(D/'result-review.json')
 require(rv.get('accepted') is True and rv['unresolved_findings']==[] and all(v is True for v in rv['checks'].values()),'result review acceptance')
 require('ACCEPTED S4-AB bounded qualification.' in (D/'result-review.md').read_text(),'review marker')
 hashes_ok(rv)
 a=read(D/'audit.json');post=read(D/'postcheck.json')
 require(a['all_passed'] is True and len(a['checks'])==6 and all(a['checks'].values()),'audit')
 require(post['all_passed'] is True and len(post['checks'])==7 and all(post['checks'].values()),'postcheck')
 raw=tomllib.loads((D/'qualification-1/qualification.toml').read_text())
 require(raw_ok(raw),'raw schema')
 require(sum(len(x['checks']) for k in ('work','lifecycles','cost') for x in raw[k])==648,'predicate count')
 require(all(sha(D/'qualification-1'/n)==sha(OUT/n) for n in ('current.json','pins.json','process.json','qualification.toml','resources.jsonl','run.log')),'portable raw')
 p=read(OUT/'process.json');h=absent([p['runner']['pgid'],p['child']['pgid']])
 require(terminal_ok(p) and not h['matches'] and len(h['groups'])==34,'terminal/fresh34groups')
 require((D/'plan.md').read_bytes()==(R/EXTERNAL[3]).read_bytes(),'frozen plan')
 checks=dict.fromkeys(('refs_index_scope','exact_files_and_untracked','MA_B_current_bindings_preserved','exact_before_texts','all624_launch_pins','source_admission_audit_post_bindings','independent_result_acceptance','all_result_review_bindings','six_audit_gates','seven_postcheck_gates','648_predicates_raw_schema','six_portable_raw_files','terminal_and_fresh34groups_ANDsessions','frozen_plan','production_test_env_CI_unchanged'),True)
 dump(D/'closure.json',dict(all_passed=True,checks=checks,sha256={q:sha(R/q) for q in FILES},host=h,previous_MA_B_mapping=mapping))
 print(json.dumps({'closure_passed':True,'checks':len(checks),'bindings':len(FILES)}),flush=True)
def publish():
 refscope();inventory((*FILES,CLOSURE))
 c=read(D/'closure.json');require(c['all_passed'] is True and all(c['checks'].values()),'separate closure');hashes_ok(c)
 nonself=tuple(sorted((*FILES,CLOSURE)))
 require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={BASE+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote baseline')
 subprocess.run(['git','-C',str(R),'add','--',*nonself],check=True)
 require(tuple(git('diff','--cached','--name-only').splitlines())==nonself,'exact initial staged names')
 for q in nonself:require(subprocess.check_output(['git','-C',str(R),'show',':'+q])==(R/q).read_bytes(),'staged blob '+q)
 subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
 dump(D/'publication.json',dict(all_passed=True,checks=dict.fromkeys(('separate_PASS_closure','fixed_complete_names','exact_nonself_staged_names_and_blobs','staged_diff_clean','remote_baseline'),True),expected_staged_names=list(FINAL),sha256={q:sha(R/q) for q in nonself},self_exclusion='Own recursive hash excluded; all staged and committed names/blobs including this record checked before push.'))
 subprocess.run(['git','-C',str(R),'add','--',PUBLICATION],check=True)
 require(tuple(git('diff','--cached','--name-only').splitlines())==FINAL,'exact final staged names')
 for q in FINAL:require(subprocess.check_output(['git','-C',str(R),'show',':'+q])==(R/q).read_bytes(),'final staged blob '+q)
 require(set(git('ls-files','--others','--exclude-standard').splitlines())=={'Manifest.toml','LocalPreferences.toml'},'unstaged new files')
 subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
 print(json.dumps({'exact_staged_blobs':len(FINAL),'all_passed':True}),flush=True)
 subprocess.run(['git','-C',str(R),'commit','-m','diagnostics: qualify Markowitz row-count fusion'],check=True)
 commit=git('rev-parse','HEAD');require(tuple(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())==FINAL,'committed names')
 for q in FINAL:require(subprocess.check_output(['git','-C',str(R),'show',commit+':'+q])==(R/q).read_bytes(),'committed blob '+q)
 subprocess.run(['git','-C',str(R),'push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
 require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={commit+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote verification')
 print(json.dumps({'commit':commit,'master':MASTER,'exact_committed_blobs':len(FINAL),'remote_verified':True}),flush=True)
if __name__=='__main__':
 require(len(sys.argv)==2 and sys.argv[1] in ('closure','publish'),'explicit phase required')
 (closure if sys.argv[1]=='closure' else publish)()
