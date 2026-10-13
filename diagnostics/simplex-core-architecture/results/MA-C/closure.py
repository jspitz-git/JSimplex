from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[4]
D=Path(__file__).resolve().parent
PREFIX='diagnostics/simplex-core-architecture/results/MA-C/'
DOCS=['diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-CONTRACT.md','docs/superpowers/plans/2026-10-13-ma-markowitz-upper-preparation.md','diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
FILES=['host.json','STATUS.md.before-MA-C','roadmap.md.before-MA-C','continuation-map.json','source-evidence.json','ledger.md','author-check.json','review.md','review.json','report.before-review.md','plan.before-review.md','review-fix.json','review-final.md','review-final.json','closure.py','closure.json','publication-names.json','publication.json']
NAMES=sorted(DOCS+[PREFIX+x for x in FILES])
def require(v,msg):
 if not v:raise SystemExit(msg)
def obj(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
save(D/'publication-names.json',NAMES)
checks={}
e=obj(D/'source-evidence.json');h=obj(D/'host.json');m=obj(D/'continuation-map.json');rf=obj(D/'review-final.json')
checks['source_gates']=e['all_passed'] and all(e['checks'].values())
checks['twenty_readtime_hashes']=len(e['sha256'])==20 and all(sha(R/p)==v for p,v in e['sha256'].items())
checks['accepted_final_review']=rf['accepted'] is True and not rf.get('unresolved_findings',[])
checks['final_review_bindings']=all(sha(R/p)==v for p,v in rf['sha256'].items())
checks['offline_fix']=obj(D/'review-fix.json')['all_passed']
oldmap={DOCS[0]:D/'report.before-review.md',DOCS[1]:D/'plan.before-review.md'}
checks['initial_review_and_author_preserved']=all(all(sha(oldmap.get(str(Path(p).relative_to(R)) if Path(p).is_absolute() and str(p).startswith(str(R)+'/') else p,R/p))==v for p,v in obj(D/f)['sha256'].items()) for f in ['review.json','author-check.json'])
checks['continuation_copies']=all(sha(R/v['preserved'])==v['sha256'] for v in m['mapping'].values())
for f in ['closure.json','publication.json','final-review.json']:
 b=obj(R/'diagnostics/simplex-core-architecture/results/S4-AD-green-bounded'/f)['sha256']
 checks['old_'+f+'_maps']=all(b.get(p,b.get(str(R/p)))==v['sha256'] for p,v in m['mapping'].items())
checks['protected_files']=all(sha(Path(p))==v for p,v in h['protected_sha256'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master']
checks['source_test_environment_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github') and not git('diff','master','--','src','test','Project.toml','.github')
groups=h['groups'];matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=cmd))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
checks['fresh_44groups_ANDsessions_noJulia']=len(set(groups))==44 and not matches
inputs=[p for p in NAMES if p not in [PREFIX+'closure.json',PREFIX+'publication.json']]
checks['exact_new_directory_names']=set(p.name for p in D.iterdir())==set(FILES)-{'closure.json','publication.json'}
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={p:sha(R/p) for p in inputs},host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=groups,matches=matches),scope='MA-C source/design only; no numerical/performance acceptance'))
print(json.dumps(checks,indent=2));require(all(checks.values()),'closure failed; stop before staging')
