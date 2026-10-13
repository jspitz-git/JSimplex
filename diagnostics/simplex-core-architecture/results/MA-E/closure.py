from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-E';O=D.parent/'MA-D'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
checks={};review=read(D/'review-final.json');host=read(D/'host.json')
checks['final_review_accepted']=review['accepted'] is True and review['unresolved_findings']==[]
checks['reviewed_manifest_digest']=review['pins_sha256']==sha(D/'admission-pins-reviewed.json')
checks['review_bindings']=all(sha(Path(p) if Path(p).is_absolute() else R/p)==h for p,h in review['sha256'].items())
for n in ('admission-pins.json','admission-pins-reviewed.json'):
 m=read(D/n);checks[n]=set(m['files'])==set(m['inventory']) and m['inputs']==m['trees']==[] and all(sha(Path(p))==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in m['inventory'].items())
checks['offline_suites']=all(read(D/n)['all_passed'] for n in ('synthetic-reviewed.json','synthetic-admission-reviewed.json','review-fix-green.json'))
checks['failed_records_preserved']=not read(D/'synthetic.json')['all_passed'] and not read(D/'review-fix-red.json')['all_passed'] and read(D/'review.json')['accepted'] is False
mapping={'diagnostics/simplex-core-architecture/STATUS.md':D/'STATUS.md.before-MA-E','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':D/'roadmap.md.before-MA-E'}
for n in ('closure.json','publication.json'):
 checks['MA_D_'+n+'_bindings_mapped']=all(sha(mapping.get(p,R/p))==h for p,h in read(O/n)['sha256'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip()==host['refs']['master']
checks['protected_files']=all(sha(Path(p))==h for p,h in host['protected_sha256'].items())
checks['actual_production_test_env_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github') and not git('diff','master','--','src','test','Project.toml','.github')
checks['no_numerical_attempt_artifacts']=not any((D/n).exists() for n in ('execution-seal.json','attempt-reserved.json')) and not (R/'.superpowers/simplex-core-architecture/MA-F/attempt-1').exists()
# Fresh host read: all previous groups AND sessions, not just leader PIDs.
matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if int(f[2]) in host['groups'] or int(f[3]) in host['groups'] or comm.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks['fresh44groups_ANDsessions_noJulia']=len(set(host['groups']))==44 and not matches
names=read(D/'publication-names.json');prefix=str(D.relative_to(R))+'/'
checks['explicit_directory_names']=set(str(p.relative_to(R)) for p in D.rglob('*') if p.is_file())=={n for n in names if n.startswith(prefix)}-{prefix+'closure.json',prefix+'whitespace.json',prefix+'publication.json'}
# New authored files clean; byte-exact copied source files retain prior whitespace.
wh=[];invalid=[]
for n in names:
 p=R/n
 if not p.exists():continue
 q=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],text=True,capture_output=True)
 if not(q.stdout or q.stderr):continue
 provenance=None
 if '/overlays/' in n:
  rel=p.relative_to(D/'overlays');side=rel.parts[0];tail=Path(*rel.parts[1:]);src=R/tail
  if src.is_file() and sha(src)==sha(p):provenance=str(src)
  else:
   for old in ('candidate-markowitz.jl','candidate-JSimplex.jl','candidate-runtests.jl','candidate-tests-reviewed.jl'):
    if sha(O/old)==sha(p):provenance=str(O/old);break
 if p.name=='reference-upper.jl' and p.read_text()==(O/'helpers.jl').read_text().split('\n_markowitz_ma_rounding_matches')[0].split('# Private scalar scratch exists only during a single upper substitution.\n')[1].replace('_markowitz_upper_solve!','reference_upper!',1):provenance=str(O/'helpers.jl')+' exact helper extraction'
 record=dict(path=n,stdout=q.stdout,stderr=q.stderr,returncode=q.returncode,sha256=sha(p),preserved_source=provenance)
 wh.append(record)
 if provenance is None or q.stderr:invalid.append(n)
checks['whitespace_only_exact_preserved_sources']=not invalid
save(D/'whitespace.json',dict(all_passed=not invalid,records=wh,invalid=invalid))
inputs=[n for n in names if n not in (prefix+'closure.json',prefix+'publication.json')]
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={n:sha(R/n) for n in inputs},host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=host['groups'],matches=matches),scope='MA-E OFFLINE closure; no Julia/runtime/performance acceptance'))
print(json.dumps(checks,indent=2));print('complete names',len(names),'preserved whitespace files',len(wh))
if not all(checks.values()):raise SystemExit('closure failed; stop before stage')
