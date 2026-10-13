from pathlib import Path
import json,hashlib,subprocess,time
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;P='diagnostics/simplex-core-architecture/results/MA-D/'
FILES='''STATUS.md.before-MA-D candidate-JSimplex.jl candidate-Project.toml candidate-markowitz.jl candidate-runtests.jl candidate-tests-complete.jl candidate-tests-reviewed.jl candidate-tests.jl continuation-map.json cost-schedule-reviewed.md cost-schedule.md fixtures.json helpers.jl host.json inverse.json ledger-final.md ledger.md oracle-checks.json oracle.py original-upper-loop.jl preparation.json prepare.py report.before-review.md review-final.json review-final.md review-fix.json review-fix.py review.json review.md roadmap.md.before-MA-D source-check.json source-check.py test-contract-reviewed.md test-contract.md closure.py closure.json whitespace.json publication-names.json publication.json'''.split()
DOCS=['diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-PREPARATION.md','docs/superpowers/plans/2026-10-13-ma-markowitz-upper-admission.md','diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
NAMES=sorted(DOCS+[P+p for p in FILES])
def obj(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def require(v,msg):
 if not v:raise SystemExit(msg)
report=DOCS[0]
def bindings(x,old=False):
 def path(p):
  actual=R/p
  return D/'report.before-review.md' if old and actual==R/report else actual
 return all(sha(path(p))==v for p,v in x['sha256'].items())
checks={};rf=obj(D/'review-final.json');host=obj(D/'host.json');m=obj(D/'continuation-map.json')
checks['final_review_accepted']=rf['accepted'] is True and not rf.get('unresolved_findings',[])
checks['final_review_bindings']=bindings(rf)
checks['initial36_bindings_preserved']=bindings(obj(D/'source-check.json'),True)
checks['initial_preparation_pins_preserved']=bindings(obj(D/'preparation.json'))
checks['initial_review_bindings_preserved']=bindings(obj(D/'review.json'),True)
checks['correction8_bindings']=bindings(obj(D/'review-fix.json')) and obj(D/'review-fix.json')['all_passed']
checks['python_oracle8_pass']=obj(D/'oracle-checks.json')['all_passed']
checks['source11_pass']=obj(D/'source-check.json')['all_passed']
checks['protected_files']=all(sha(Path(p))==v for p,v in host['protected_sha256'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master']
checks['no_actual_production_test_env_CI_diff']=not git('diff','HEAD','--','src','test','Project.toml','.github') and not git('diff','master','--','src','test','Project.toml','.github')
checks['continuation_before_copies']=all(sha(R/v['preserved'])==v['sha256'] for v in m['mapping'].values())
for f in ['closure.json','publication.json']:
 b=obj(R/'diagnostics/simplex-core-architecture/results/MA-C'/f)['sha256']
 checks['MA_C_'+f+'_maps']=all(b.get(p,b.get(str(R/p)))==v['sha256'] for p,v in m['mapping'].items())
groups=host['groups'];matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=cmd))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
checks['fresh44groups_ANDsessions_noJulia']=len(set(groups))==44 and not matches
# Preserve exactly the reviewed helper insertion separator; do not rewrite a bound snippet.
wh=[]
for name in NAMES:
 p=R/name
 if not p.exists():continue
 q=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],text=True,capture_output=True)
 if q.stdout or q.stderr:wh.append(dict(path=name,stdout=q.stdout,stderr=q.stderr,returncode=q.returncode,sha256=sha(p)))
checks['only_bound_helper_separator_whitespace']=len(wh)==1 and wh[0]['path']==P+'helpers.jl' and wh[0]['stderr']=='' and wh[0]['stdout']==str(D/'helpers.jl')+':78: new blank line at EOF.\n' and (D/'helpers.jl').read_bytes().endswith(b'\n\n') and (D/'helpers.jl').read_text() in (D/'candidate-markowitz.jl').read_text()
save(D/'whitespace.json',dict(all_passed=checks['only_bound_helper_separator_whitespace'],records=wh,reason='Exact reviewed helper insertion includes its separating blank line; preserve bound candidate/inverse. All other files clean.'))
save(D/'publication-names.json',NAMES)
checks['exact_directory_inventory']=set(p.name for p in D.iterdir())==set(FILES)-{'closure.json','publication.json'}
inputs=[n for n in NAMES if n not in (P+'closure.json',P+'publication.json')]
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={p:sha(R/p) for p in inputs},host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=groups,matches=matches),scope='MA-D OFFLINE ONLY, no runtime/performance acceptance'))
print(json.dumps(checks,indent=2));print('Exact publication names:',len(NAMES));require(all(checks.values()),'closure failed: stop before staging')
