"""New post-exit provenance/statistics; never invokes a launcher or old auditor."""
from pathlib import Path
import json,hashlib,subprocess,time,tomllib,shutil,statistics
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F-repair';O=R/'.superpowers/simplex-core-architecture/MA-F/attempt-2'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
inv=read(O/'invocation.json');pins=read(D/'admission-pins-reviewed.json');h=read(D/'host.json');seal=read(D/'execution-seal.json');reservation=read(D/'attempt-reserved.json');checks={};groups=set(h['groups']);procs={};raws={};samples=[]
for p in sorted(O.glob('*/process.json')):
 q=read(p);procs[p.parent.name]=q;groups.update(q[k][t] for k in ('runner','child') if k in q for t in ('pgid','sid'))
 for line in (p.parent/'resources.jsonl').read_text().splitlines():samples.append(json.loads(line))
 if (p.parent/'raw.toml').exists():raws[p.parent.name]=tomllib.loads((p.parent/'raw.toml').read_text())
matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['fresh_full_groups_ANDsessions_noJulia']=not matches and boot==h['boot_id']
checks['all1817pins_unchanged']=len(pins['inventory'])==1817 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['seal_reservation_link']=inv['reservation_sha256']==sha(D/'attempt-reserved.json') and inv['seal_sha256']==reservation['seal_sha256']==sha(D/'execution-seal.json') and inv['pin_sha256']==seal['pin_sha256']==reservation['pin_sha256']==sha(D/'admission-pins-reviewed.json') and seal['commands']==reservation['commands']
checks['all_process_commands_admitted']=all(p['command'] in seal['commands'] and p['pins_sha256']==inv['pin_sha256'] and p['pins_unchanged'] is True for p in procs.values())
checks['raw_pin_copies_exact']=all(sha(O/n/'pins.json')==sha(D/'admission-pins-reviewed.json') for n in procs)
checks['protected_files_unchanged']=all(sha(p)==v for p,v in h['protected_sha256'].items())
checks['actual_src_test_Project_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),primary=subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip(),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
checks['refs_unchanged']=refs['head']==h['refs']['head'] and refs['master']==refs['primary']==h['refs']['master'] and refs['remote']==h['refs']['remote']
checks['resources_in_bounds']=bool(samples) and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples+[p['terminal_memory'] for p in procs.values()])
checks['accepted_stage_hashes']=all(sha(O/s['stage']['id']/'process.json')==s['process_sha256'] and sha(O/s['stage']['id']/'raw.toml')==s['raw_sha256'] for s in inv['stages'])
shutil.copytree(O,D/'attempt-2');names=sorted(str(p.relative_to(O)) for p in O.rglob('*') if p.is_file())
checks['portable_exact']=names==sorted(str(p.relative_to(D/'attempt-2')) for p in (D/'attempt-2').rglob('*') if p.is_file()) and all(sha(O/n)==sha(D/'attempt-2'/n) for n in names)
summary={n:dict(errors=r.get('errors'),counts=r.get('counts'),records=len(r.get('records',[])),body_seconds=r.get('body_seconds'),ambient_ok=r.get('ambient_ok')) for n,r in raws.items()}
measure=[]
if inv['all_passed'] is True:
 for index,ref in enumerate(raws['pair04-reference']['records']):
  ratios=[];entries=[]
  for pair in range(4,11):
   a=raws[f'pair{pair:02d}-reference']['records'][index];b=raws[f'pair{pair:02d}-candidate']['records'][index]
   ratio=b['steady_full']['seconds']/a['steady_full']['seconds'];ratios.append(ratio)
   entries.append(dict(pair=pair,ratio=ratio,reference={k:a[k] for k in ['construction','first_full','steady_full','first_upper','steady_upper']},candidate={k:b[k] for k in ['construction','first_full','steady_full','first_upper','steady_upper']}))
  med=statistics.median(ratios);name=ref['name'];scalar=ref['scalar'];target=scalar in ('BigFloat256','BigFloat512','RationalBigInt') and 'star' in name and '32' in name;control=scalar in ('Float32','Float64') or 'core' in name
  measure.append(dict(name=name,scalar=scalar,median_ratio=med,min_ratio=min(ratios),max_ratio=max(ratios),MAD=statistics.median(abs(r-med) for r in ratios),faster_pairs=sum(r<1 for r in ratios),target_gate=(med<=.95 and sum(r<1 for r in ratios)>=6) if target else None,control_gate=(med<=1.05) if control else None,pairs=entries))
save('postprocess.json',dict(all_passed=all(checks.values()),checks=checks,numerical_all_passed=inv['all_passed'],invocation_errors=inv['errors'],process_count=len(procs),accepted_stage_count=len(inv['stages']),raw_summary=summary,measurements=measure,benefit_accepted=bool(measure) and all(m['target_gate'] is not False and m['control_gate'] is not False for m in measure),resources=dict(sample_count=len(samples),minimum_available_kib=min(s['available_kib'] for s in samples),maximum_swap_kib=max(s['swap_used_kib'] for s in samples),inclusive_launcher_seconds=inv['elapsed']),host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,refs=refs),sha256={str(D/'attempt-2'/n):sha(D/'attempt-2'/n) for n in names},scope='Provenance PASS is separate from numerical and benefit acceptance. Existing audited outcomes reused, no old auditor rerun. All raw retained; stats only if complete.' ))
print(json.dumps(dict(checks=checks,numerical=inv['all_passed'],errors=inv['errors'],processes=len(procs),stages=len(inv['stages']),raw_summary=summary),indent=2))
if not all(checks.values()):raise SystemExit('post-exit provenance failed')
