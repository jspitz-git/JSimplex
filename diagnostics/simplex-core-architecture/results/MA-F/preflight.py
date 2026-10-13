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
def save(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
h=read(E/'host.json');review=read(E/'review-final.json');pins=read(E/'admission-pins-reviewed.json');checks={}
checks['review_accepted']=review['accepted'] is True and review['unresolved_findings']==[] and review['pins_sha256']==sha(E/'admission-pins-reviewed.json')
checks['review33_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
checks['pins1761']=len(pins['inventory'])==1761 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['required1760']=all(p in pins['inventory'] and pins['inventory'][p]['sha256']==v for p,v in read(E/'required-paths-reviewed.json').items())
for n in ('publication.json','closure-final.json'):
 d=read(E/n);checks[n]=d['all_passed'] is True and all(sha(R/p)==v for p,v in d['sha256'].items())
refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),branch=git('branch','--show-current'),primary=subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip(),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
checks['refs']=refs['head']=='bf4f941328538134e6df6251655f2465370a1405' and refs['master']==refs['primary']==h['refs']['master'] and refs['branch']=='codex/simplex-core-architecture' and all(x in refs['remote'] for x in (refs['head'],refs['master']))
checks['protected_files']=all(sha(p)==v for p,v in h['protected_sha256'].items())
checks['actual_src_test_Project_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['unused_attempt']=not (E/'execution-seal.json').exists() and not (E/'attempt-reserved.json').exists() and not (R/'.superpowers/simplex-core-architecture/MA-F/attempt-1').exists()
matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks['fresh44groups_ANDsessions_noJulia']=len(set(h['groups']))==44 and not matches
save('preflight.json',dict(all_passed=all(checks.values()),checks=checks,refs=refs,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=h['groups'],matches=matches,time=time.time(),protected_sha256=h['protected_sha256'],sha256={str(E/n):sha(E/n) for n in ('admission-pins-reviewed.json','review-final.json','closure-final.json','publication.json')}))
print(checks)
if not all(checks.values()):raise SystemExit('preflight refused')
for path,name in [('diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-F'),('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-F')]:
 with (D/name).open('xb') as f:f.write((R/path).read_bytes())
