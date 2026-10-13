"""One-shot MA-F failure-provenance closure, never a numerical acceptance."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F';E=D.parent/'MA-E'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
review=read(D/'review.json');post=read(D/'postcheck.json');pre=read(D/'preflight.json');names=read(D/'publication-names.json');checks={}
checks['independent_failure_review_accepted']=review['accepted'] is True and review['unresolved_findings']==[]
checks['review_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
checks['postcheck15_provenance_PASS']=post['all_passed'] is True and len(post['checks'])==15 and all(post['checks'].values())
checks['postcheck_bindings']=all(sha(p)==v for p,v in post['sha256'].items())
map_paths={'diagnostics/simplex-core-architecture/STATUS.md':D/'STATUS.md.before-MA-F','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':D/'roadmap.md.before-MA-F'}
for name in ('closure.json','closure-final.json','publication.json'):
 old=read(E/name)
 checks['MA_E_'+name+'_exact_before_mapping']=all(sha(map_paths.get(p,R/p))==v for p,v in old['sha256'].items())
checks['original_false_closure_preserved']=read(E/'closure.json')['all_passed'] is False and read(E/'closure-final.json')['all_passed'] is True
checks['refs_unchanged']=git('rev-parse','HEAD')==pre['refs']['head'] and git('rev-parse','master')==pre['refs']['master'] and subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip()==pre['refs']['primary']
checks['protected_unchanged']=all(sha(p)==v for p,v in pre['protected_sha256'].items())
checks['actual_src_test_Project_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['empty_initial_index']=not git('diff','--cached','--name-only')
groups=post['host']['groups'];matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks['fresh_full46groups_ANDsessions_noJulia']=len(groups)==46 and boot==post['host']['boot_id'] and not matches
prefix=str(D.relative_to(R))+'/'
checks['explicit_names_complete_before_outputs']=set(str(p.relative_to(R)) for p in D.rglob('*') if p.is_file())=={p for p in names if p.startswith(prefix)}-{prefix+'closure.json',prefix+'publication.json'}
# Raw command records have intentional space before LF inside JSON string, not source whitespace.
checkpaths=[p for p in names if p not in (prefix+'closure.json',prefix+'publication.json')]
checks['all_authored_and_preserved_files_whitespace_clean']=all(not subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(R/p)],capture_output=True,text=True).stdout for p in checkpaths)
save('closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={p:sha(R/p) for p in checkpaths},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),continuation_map={p:str(v.relative_to(R)) for p,v in map_paths.items()},scope='Diagnostic failure closure only; RED, candidate qualification and cost NOT accepted.'))
print(json.dumps(checks,indent=2))
if not all(checks.values()):raise SystemExit('closure failed; do not stage/commit')
