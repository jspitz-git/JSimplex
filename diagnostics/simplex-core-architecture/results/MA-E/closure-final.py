"""Separate closure supplement; original failed closure/whitespace stay frozen."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-E';prefix=str(D.relative_to(R))+'/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
old=read(D/'closure.json');w=read(D/'whitespace.json');h=read(D/'host.json');checks={}
checks['original15gates_pass']=sum(v is True for v in old['checks'].values())==15 and old['checks']['whitespace_only_exact_preserved_sources'] is False and old['all_passed'] is False
checks['all_original_closure_bindings_unchanged']=all(sha(R/p)==v for p,v in old['sha256'].items())
name=prefix+'finite_oracle.py';record=next(r for r in w['records'] if r['path']==name)
expected=(D.parent/'MA-D/oracle.py').read_text().split("if __name__=='__main__':")[0]
checks['oracle_exact_original_prefix']=(D/'finite_oracle.py').read_text()==expected
checks['only_one_unmapped_warning']=w['invalid']==[name] and record['sha256']==sha(D/'finite_oracle.py') and record['stdout']==str(D/'finite_oracle.py')+':37: new blank line at EOF.\n' and record['stderr']==''
checks['other12warnings_source_preserved']=len(w['records'])==13 and all(r['preserved_source'] is not None for r in w['records'] if r['path']!=name)
save(D/'whitespace-supplement.json',dict(all_passed=all(checks.values()),checks=checks,reason='Verbatim finite oracle definitions extracted from MA-D before main; preserve their final separator and reviewed hash. No source correction or numerical rerun.',sha256={str(D/'finite_oracle.py'):sha(D/'finite_oracle.py'),str(D.parent/'MA-D/oracle.py'):sha(D.parent/'MA-D/oracle.py'),str(D/'whitespace.json'):sha(D/'whitespace.json')}))
checks['refs_unchanged']=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master']
checks['protected_unchanged']=all(sha(p)==v for p,v in h['protected_sha256'].items())
checks['no_actual_src_test_Project_CI_diff']=not git('diff','HEAD','--','src','test','Project.toml','.github')
# Closure-only fresh process check, no Julia or old auditor execution.
matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=f[2],sid=f[3],start_ticks=f[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks['fresh_groups_ANDsessions_noJulia']=not matches
names=read(D/'publication-names-final.json')
checks['exact_final_names']=set(str(p.relative_to(R)) for p in D.rglob('*') if p.is_file())=={n for n in names if n.startswith(prefix)}-{prefix+'closure-final.json',prefix+'publication.json'}
newfiles=['closure-final.py','publication-names-final.json','whitespace-supplement.json']
checks['supplement_authored_whitespace_clean']=all(not subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(D/n)],capture_output=True,text=True).stdout for n in newfiles)
inputs=[n for n in names if n not in (prefix+'closure-final.json',prefix+'publication.json')]
save(D/'closure-final.json',dict(all_passed=all(checks.values()),checks=checks,sha256={p:sha(R/p) for p in inputs},host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=h['groups'],matches=matches),scope='Separate offline closure correction for exact preserved whitespace; original15/16failure retained. All numerical inputs/review unchanged.'))
print(json.dumps(checks,indent=2));print('exact final names',len(names))
if not all(checks.values()):raise SystemExit('final closure failed before staging')
