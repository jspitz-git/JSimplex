"""One non-retryable current-master profile sequence, up to three serial guarded processes."""
from pathlib import Path
import json,hashlib,subprocess,sys,time,os
import audit
D=Path(__file__).resolve().parent;R=D.parents[3]
def sha(p):return audit.sha(p)
def read(p):return json.loads(Path(p).read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
def save(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def host(groups):
 old=read(D/'host.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
   if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
    matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 refs={k:subprocess.check_output(['git',*a],cwd=R,text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
 require(not matches and refs==old['refs'],'host/ref gate failed')
 return dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,refs=refs)
def main():
 require(sys.argv==[str(D/'launcher.py'),'run'],'exact invocation')
 pins=read(D/'pins.json');rev=read(D/'admission-review.json');ph=sha(D/'pins.json');required=read(D/'required-paths.json')
 require(rev['accepted'] is True and rev['findings']==[] and rev['pins_sha256']==ph,'admission missing')
 require(all(sha(p)==s for p,s in rev['sha256'].items()),'review drift')
 require(set(required)==set(pins['inventory']),'manifest membership')
 require(all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'pin drift')
 require(set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'source membership drift')
 groups=list(read(D/'host.json')['groups']);commands=read(D/'commands.json')
 require(all(not (D/f'run-{i}').exists() and not (D/f'reservation-{i}.json').exists() for i in (1,2,3)),'prior attempt exists')
 save(D/'sequence-reservation.json',dict(pins_sha256=ph,review_sha256=sha(D/'admission-review.json'),maximum_processes=3,total_cap_seconds=360,no_retry=True))
 total=0.0
 for i in (1,2,3):
  save(D/f'prelaunch-{i}.json',host(groups));cmd=commands[str(i)];out=D/f'run-{i}'
  save(D/f'reservation-{i}.json',dict(command=cmd,pins_sha256=ph,review_sha256=sha(D/'admission-review.json'),host_sha256=sha(D/f'prelaunch-{i}.json'),seconds=120,sequence_sha256=sha(D/'sequence-reservation.json')))
  started=time.monotonic();gc=[sys.executable,'-B',str(D/'guard.py'),'run',str(D/'pins.json'),str(out),'--seconds','114','--deadline',str(started+114),'--',*cmd]
  record=dict(command=gc,reservation_sha256=sha(D/f'reservation-{i}.json'))
  try:
   with (D/f'launcher-{i}.log').open('x') as f:record['returncode']=subprocess.run(gc,cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True).returncode
  finally:
   record['elapsed_seconds']=time.monotonic()-started;total+=record['elapsed_seconds'];record['cumulative_seconds']=total;save(D/f'invocation-{i}.json',record)
  if (out/'process.json').exists():
   proc=read(out/'process.json')
   for who in ('runner','child'):
    if who in proc:groups+=list({proc[who]['pgid'],proc[who]['sid']})
  groups=sorted(set(groups));save(D/f'posthost-{i}.json',host(groups))
  result=audit.stage(i);save(D/f'audit-{i}.json',result)
  require(record.get('returncode')==0 and record['elapsed_seconds']<=120 and total<=360 and result['all_passed'],'failed qualification; sequence stopped, no retry')
 print('all3 guarded processes qualified; attribution requires independent review')
if __name__=='__main__':main()
