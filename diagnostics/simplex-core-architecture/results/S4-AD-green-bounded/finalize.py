"""New S4-AD final closure and exact publication; never executes prior scripts."""
from common import *
A=D.parent/'S4-AD';B=D.parent/'S4-AD-repair';BASE='8f1a9e4522990ab5553f2925baa58978162ebe1a';OLDMASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
CONT=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
PROD=['src/markowitz_factorization.jl','test/markowitz_workspace_reuse_allocation_tests.jl']
def git(*a,root=R):return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
def check_hash(p,h):
 p=Path(p);p=p if p.is_absolute() else R/p
 if sha(p)==h:return
 mapping={R/CONT[0]:A/'STATUS.md.before-S4-AD',R/CONT[1]:A/'roadmap.md.before-S4-AD',R/PROD[0]:A/'source.before-S4-AD.jl',R/PROD[1]:A/'test.before-S4-AD.jl',P/PROD[0]:A/'source.before-S4-AD.jl',P/PROD[1]:A/'test.before-S4-AD.jl'}
 require(p in mapping and sha(mapping[p])==h,'unmapped hash '+str(p))
def bindings(x):
 for k in ('sha256','portable_sha256'):
  for p,h in x.get(k,{}).items():check_hash(p,h)
def accepted(p):
 x=read(p);require(x['accepted'] is True and x['unresolved_findings']==[] and all(v is True for v in x['checks'].values()),'review '+str(p));bindings(x)
def names():return read(D/'publication-names.json')['names']
def scope():
 i=read(D/'integration.json');require(refs()==i['after_refs'],'current refs')
 require(set(git('diff','--name-only').splitlines())==set(CONT),'tracked scope')
 require(not git('diff','--cached','--name-only'),'index not empty')
 require(set(git('diff','--name-only',OLDMASTER,'HEAD',root=P).splitlines())==set(PROD),'master changed files')
 require(not git('diff',str(i['after_refs'][str(P)]),'--','src','test','.github','Project.toml'),'root/master production identity')
 for rel in PROD:require((R/rel).read_bytes()==(P/rel).read_bytes(),'actual master bytes')
 for p,h in i['preserved_user_files'].items():require(sha(p)==h,'user file changed')
 for root,commit in [(R,i['production_commit']),(P,i['after_refs'][str(P)])]:
  require(set(git('diff-tree','--no-commit-id','--name-only','-r',commit,root=root).splitlines())==set(PROD),'production commit scope')
  for rel in PROD:require(subprocess.check_output(['git','-C',str(root),'show',commit+':'+rel])==(R/rel).read_bytes(),'production commit blob')
 return i

def closure():
 i=scope();files=names();cl=str((D/'closure.json').relative_to(R));pub=str((D/'publication.json').relative_to(R));nonself=[p for p in files if p not in (cl,pub)]
 actual={str(p.relative_to(R)) for d in (A,B,D) for p in d.rglob('*') if p.is_file()}
 require(actual=={p for p in nonself if any(p.startswith(str(x.relative_to(R))+'/') for x in (A,B,D))},'evidence completeness')
 require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(nonself)-set(CONT)|{'Manifest.toml','LocalPreferences.toml'},'untracked scope')
 for rel,saved in zip(CONT,['STATUS.md.before-S4-AD','roadmap.md.before-S4-AD']):require(subprocess.check_output(['git','-C',str(R),'show',BASE+':'+rel])==(A/saved).read_bytes(),'before continuation')
 for n in ('review.json','closure.json','publication.json'):bindings(read(AC/n))
 pin_counts={}
 for folder in [A/'red',B/'red',B/'green',D/'green',D/'master']:
  pins=read(folder/'pins.json');require(set(pins['files'])==set(pins['inventory']),'manifest membership')
  for p,v in pins['inventory'].items():check_hash(p,v['sha256']);require(str(Path(p).resolve(strict=True))==v['resolved'],'resolved path')
  pin_counts[str(folder.relative_to(R))]=len(pins['inventory']);accepted(folder/'review.json')
  a=read(folder/'audit.json');bindings(a)
  if folder==A/'red':
   require(a['all_passed'] is False and 'raw files' in a['error'],'original false audit')
   require('UndefVarError: `push_testset` not defined' in (folder/'raw/run.log').read_text(),'original cause')
   require(not (folder/'raw/tests.toml').exists(),'initial test absence')
  elif folder==B/'green':
   require(a['all_passed'] is False and read(folder/'raw/process.json')['reason']=='wall_time' and not (folder/'raw/tests.toml').exists(),'preserved timeout')
   rv=read(folder/'result-review.json');require(rv['accepted'] is False and rv['diagnosis_accepted'] is True and rv['unresolved_findings']==[],'rejected GREEN review');bindings(rv)
  else:require(a['all_passed'] is True and len(a['checks'])==8 and all(v is True for v in a['checks'].values()),'stage audit')
 for folder in [D/'green',D/'master']:accepted(folder/'result-review.json')
 accepted(D/'final-review.json')
 require((R/PROD[0]).read_bytes()==(AC/'candidate-source.jl').read_bytes(),'exact source')
 require((R/PROD[1]).read_bytes()==(AC/'candidate-test.jl').read_bytes()==(A/'test.before-S4-AD.jl').read_bytes()+(AC/'test-append.jl').read_bytes(),'exact test/prefix')
 h=host(read(D/'master/audit.json')['host']['groups']);require(len(h['groups'])==44 and not h['matches'],'fresh44groups ANDsessions noJulia')
 checks=dict.fromkeys(('refs_and_two_file_commits','actual_master_source_test_identity','user_files_preserved','exact_complete_names','before_continuation_mapping','all_AC_final_bindings','all_five_launch_manifests_reconciled','original_failed_attempt_preserved','expected_RED_and_GREEN_and_master_audits','all_raw_portable_bindings','all_admission_and_result_reviews','exact_qualified_candidate_and_test_prefix','fresh44groups_ANDsessions_noJulia','final_independent_acceptance'),True)
 dump(D/'closure.json',dict(all_passed=True,checks=checks,sha256={p:sha(R/p) for p in nonself},host=h,pin_counts=pin_counts,production_commit=i['production_commit'],master=i['after_refs'][str(P)],historical_mapping='AC current continuation -> AD before copies ONLY. Original/replacement RED actual source/test -> AD before source/test ONLY when exact historical SHA matches. All older maps unchanged.'))
 print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(nonself),pins=pin_counts)))
def publish():
 i=scope();files=names();pub=str((D/'publication.json').relative_to(R));nonself=[p for p in files if p!=pub]
 c=read(D/'closure.json');require(c['all_passed'] is True and all(c['checks'].values()),'closure');bindings(c)
 expected_remote={BASE+'\trefs/heads/codex/simplex-core-architecture',OLDMASTER+'\trefs/heads/master'}
 require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())==expected_remote,'remote baseline')
 subprocess.run(['git','-C',str(R),'add','--',*nonself],check=True)
 require(git('diff','--cached','--name-only').splitlines()==nonself,'exact staged names')
 for p in nonself:require(subprocess.check_output(['git','-C',str(R),'show',':'+p])==(R/p).read_bytes(),'staged blob '+p)
 subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
 dump(D/'publication.json',dict(all_passed=True,checks=dict.fromkeys(('separate_PASS_closure','fixed_complete_names','exact_staged_names_blobs','diff_clean','remote_baseline','both_integration_commits_verified'),True),expected_staged_names=files,sha256={p:sha(R/p) for p in nonself},self_exclusion='Self hash excluded; actual final staged and committed blobs verified before push.'))
 subprocess.run(['git','-C',str(R),'add','--',pub],check=True)
 require(git('diff','--cached','--name-only').splitlines()==files,'final staged names')
 for p in files:require(subprocess.check_output(['git','-C',str(R),'show',':'+p])==(R/p).read_bytes(),'final staged blob')
 require(set(git('ls-files','--others','--exclude-standard').splitlines())=={'Manifest.toml','LocalPreferences.toml'},'untracked after staging')
 subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
 print('PASS exact staged names/blobs',len(files),flush=True)
 subprocess.run(['git','-C',str(R),'commit','-m','diagnostics: verify Markowitz row-count integration'],check=True)
 commit=git('rev-parse','HEAD');require(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==files,'committed names')
 for p in files:require(subprocess.check_output(['git','-C',str(R),'show',commit+':'+p])==(R/p).read_bytes(),'committed blob')
 subprocess.run(['git','-C',str(R),'push','--atomic','origin','HEAD:refs/heads/codex/simplex-core-architecture',i['after_refs'][str(P)]+':refs/heads/master'],check=True)
 require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={commit+'\trefs/heads/codex/simplex-core-architecture',i['after_refs'][str(P)]+'\trefs/heads/master'},'remote verification')
 print(json.dumps(dict(diagnostic_commit=commit,master=i['after_refs'][str(P)],files=len(files),remote_verified=True)))
if __name__=='__main__':
 require(len(sys.argv)==2 and sys.argv[1] in ('closure','publish'),'phase');{'closure':closure,'publish':publish}[sys.argv[1]]()
