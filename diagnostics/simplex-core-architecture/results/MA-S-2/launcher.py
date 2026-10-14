"""MA-S-2 one reserved sequence, three serial short processes, no numerical retry.
Requires a later fresh launch-context and independent numerical-review seal.
This preparation alone cannot launch Julia.
"""
from pathlib import Path
import json,subprocess,sys,time
import audit
D=Path(__file__).resolve().parent;R=D.parents[3]
sha=audit.sha;read=audit.read;require=audit.require
def save(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def validate_admission(pins,required,prep,seal,context):
 ph=sha(D/'pins.json')
 require(prep.get('accepted') is True and prep.get('findings')==[] and prep.get('pins_sha256')==ph,'preparation review missing')
 require(seal.get('accepted') is True and seal.get('findings')==[] and seal.get('pins_sha256')==ph and seal.get('context_sha256')==sha(D/'launch-context.json') and seal.get('preparation_review_sha256')==sha(D/'admission-review.json'),'numerical seal missing')
 require(set(seal['sha256']) >= {str(D/'pins.json'),str(D/'launch-context.json'),str(D/'admission-review.json')},'seal membership')
 require(context.get('standing_short_run_permission') is True and context.get('maximum_processes')==3 and context.get('maximum_seconds_per_process')==120,'context limits')
 for rev in (prep,seal):require(bool(rev['sha256']) and all(sha(p)==s for p,s in rev['sha256'].items()),'review drift')
 require(set(required)==set(pins['inventory'])==set(pins['files']),'manifest membership')
 require(all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'pin drift')
 require(set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'source membership drift')

def host(groups,context):
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   f=(p/'stat').read_text().rsplit(')',1)[1].split();exe=(p/'exe').resolve().name
   if int(f[2]) in groups or int(f[3]) in groups or exe.startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except (FileNotFoundError,ProcessLookupError):pass
 refs={k:subprocess.check_output(['git',*a],cwd=R,text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
 require(not matches and refs==context['refs'] and boot==context['boot_id'],'host/ref gate failed')
 return dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,refs=refs)

def main():
 require(sys.argv==[str(D/'launcher.py'),'run'],'exact invocation')
 pins=read(D/'pins.json');prep=read(D/'admission-review.json');seal=read(D/'numerical-review.json');context=read(D/'launch-context.json');required=read(D/'required-paths.json')
 validate_admission(pins,required,prep,seal,context)
 groups=sorted(set(read(D/'host.json')['groups'])|set(context['groups']));commands=read(D/'commands.json')
 require(all(not (D/f'run-{i}').exists() and not (D/f'reservation-{i}.json').exists() and not (D/f'invocation-{i}.json').exists() for i in (1,2,3)),'prior attempt exists')
 host(groups,context)
 save(D/'sequence-reservation.json',dict(pins_sha256=sha(D/'pins.json'),review_sha256=sha(D/'numerical-review.json'),context_sha256=sha(D/'launch-context.json'),maximum_processes=3,total_cap_seconds=360,no_retry=True))
 total=0.0
 for i in (1,2,3):
  save(D/f'prelaunch-{i}.json',host(groups,context));cmd=commands[str(i)];out=D/f'run-{i}'
  save(D/f'reservation-{i}.json',dict(command=cmd,pins_sha256=sha(D/'pins.json'),review_sha256=sha(D/'numerical-review.json'),context_sha256=sha(D/'launch-context.json'),host_sha256=sha(D/f'prelaunch-{i}.json'),seconds=120,sequence_sha256=sha(D/'sequence-reservation.json')))
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
  groups=sorted(set(groups));save(D/f'posthost-{i}.json',host(groups,context))
  result=audit.stage(i);save(D/f'audit-{i}.json',result)
  require(record.get('returncode')==0 and record['elapsed_seconds']<=120 and total<=360 and result['all_passed'],'failed qualification; stop, no retry')
 print('3 processes qualified; aggregate per-case cost gate remains')
if __name__=='__main__':main()
