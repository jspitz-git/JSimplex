"""Narrow publication correction; preserve original failed closure and pinned bytes."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F-repair';prefix=str(D.relative_to(R))+'/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
old=read(D/'closure.json');w=read(D/'whitespace.json');checks={};name=prefix+'finite_oracle.py'
checks['original15gates_preserved']=old['all_passed'] is False and sum(v is True for v in old['checks'].values())==15 and old['checks']['authored_whitespace_clean_verbatim_copies_preserved'] is False
checks['original_closure_all_bindings_unchanged']=all(sha(R/p)==v for p,v in old['sha256'].items())
r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',name],capture_output=True,text=True)
expected=name+':37: new blank line at EOF.\n'
checks['only_exact_frozen_oracle_warning']=w['invalid']==[name] and len(w['warnings'])==1 and w['warnings'][0]['source']==str(D.parent/'MA-E/finite_oracle.py') and sha(R/name)==sha(D.parent/'MA-E/finite_oracle.py')==w['warnings'][0]['sha256'] and r.stdout==expected and not r.stderr and r.returncode==3
checks['red_old_exit_predicate_green_exact_correction']=(r.returncode not in (0,1)) and (r.returncode==3 and r.stdout==expected and not r.stderr)
review=read(D/'closure-review.json');checks['independent_correction_accepted']=review['accepted'] is True and review['unresolved_findings']==[] and all(sha(p)==v for p,v in review['sha256'].items())
host=read(D/'host.json');post=read(D/'postprocess.json');groups=post['host']['groups'];matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  t=(p/'stat').read_text();f=t[t.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['fresh90groups_ANDsessions_noJulia']=len(groups)==90 and not matches and boot==host['boot_id']
checks['refs_protected_unchanged']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==host['refs']['head'] and subprocess.check_output(['git','rev-parse','master'],text=True).strip()==host['refs']['master'] and all(sha(p)==v for p,v in host['protected_sha256'].items())
checks['empty_index']=not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip()
names=read(D/'publication-names-final.json');missing=[prefix+'closure-final.json',prefix+'publication.json']
checks['exact_complete_names_before_outputs']=set(str(p.relative_to(R)) for p in D.rglob('*') if p.is_file())=={n for n in names if n.startswith(prefix)}-set(missing)
new=[prefix+n for n in ('closure-final.py','publication-final.py','publication-names-final.json','closure-amendment.json','closure-review.md','closure-review.json')]
checks['new_authored_files_clean']=all(not subprocess.run(['git','diff','--no-index','--check','--','/dev/null',n],capture_output=True,text=True).stdout for n in new)
save('closure-final.json',dict(all_passed=all(checks.values()),checks=checks,sha256={n:sha(R/n) for n in names if n not in missing},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),scope='Separate PASS closure for preserved exact-source EOF warning; original15/16FAIL remains; numerical performance gate remains NOT ACCEPTED.'))
print(json.dumps(checks,indent=2))
if not all(checks.values()):raise SystemExit('final closure failed')
