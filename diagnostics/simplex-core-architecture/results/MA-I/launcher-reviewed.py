"""UNEXECUTED MA-F serial launch; reservation consumed even on first failure."""
import sys
sys.dont_write_bytecode=True
from control_reviewed import *
from auditor import validate,paired,complete_grid
import tomllib

def main():
 started=time.monotonic()
 require(sys.argv==[str(D/'launcher-reviewed.py'),'run'],'exact invocation')
 require(current_baseline_ok(refs()),'frozen master/primary/branch changed')
 a=read(D/'execution-seal.json');pins=read(D/'admission-pins-reviewed.json');ph=sha(D/'admission-pins-reviewed.json')
 require(seal_ok(a,refs(),ph),'execution seal')
 require(inventory_ok(pins,read(D/'required-paths-reviewed.json')),'immutable pins')
 require(not OUT.exists(),'existing attempt')
 groups=set(read(D/'host.json')['groups']);h=host(groups);require(not h['matches'],'live groups/sessions')
 require(time.monotonic()-started<750,'entry checks exhausted whole cap')
 save(D/'attempt-reserved.json',dict(time_ns=time.time_ns(),seal_sha256=sha(D/'execution-seal.json'),pin_sha256=ph,commands=[command(s) for s in STAGES],refs=refs(),host=h))
 OUT.mkdir(parents=True,exist_ok=False)
 cost_start=None;record=dict(stages=[],all_passed=False,errors=[],reservation_sha256=sha(D/'attempt-reserved.json'),seal_sha256=sha(D/'execution-seal.json'),pin_sha256=ph,started_ns=time.time_ns());raw_pairs={}
 try:
  for s in STAGES:
   if s['stage']=='cost' and cost_start is None:cost_start=time.monotonic()
   require(refs()==a['refs'] and current_baseline_ok(refs()),'refs changed')
   h=host(groups);require(not h['matches'],'groups/sessions not closed')
   limit=remaining(started,cost_start,time.monotonic(),s);cmd=command(s)
   # Guard performs fresh pin and resource checks before creating each output.
   gc=[sys.executable,str(D/'guard-reviewed.py'),'run',str(D/'admission-pins-reviewed.json'),str(OUT/s['id']),'--seconds',str(limit),'--deadline',str(min(started+750,(cost_start+600) if cost_start is not None else started+750)),'--',*cmd]
   with (OUT/(s['id']+'.guard.log')).open('x') as log:
    run=subprocess.run(gc,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   p=read(OUT/s['id']/'process.json')
   groups.update(p[k]['pgid'] for k in ('runner','child') if k in p)
   h=host(groups);require(not h['matches'],'post-run process remains')
   elapsed=time.monotonic()-started
   require(elapsed<=750 and (cost_start is None or time.monotonic()-cost_start<=600),'global elapsed')
   require(run.returncode==0 and terminal(p,limit,cmd,ph),'terminal guard failure')
   raw=tomllib.loads((OUT/s['id']/'raw.toml').read_text());validate(raw,s['stage'],s['side'])
   item=dict(stage=s,command=cmd,limit=limit,process_sha256=sha(OUT/s['id']/'process.json'),raw_sha256=sha(OUT/s['id']/'raw.toml'),post_host=h,global_elapsed=elapsed)
   record['stages'].append(item);save(OUT/(s['id']+'.audit.json'),dict(all_passed=True,**item))
   if s['stage']=='cost':
    raw_pairs.setdefault(s['pair'],{})[s['side']]=raw
    if len(raw_pairs[s['pair']])==2:paired(raw_pairs[s['pair']]['reference'],raw_pairs[s['pair']]['candidate'])
  complete_grid(raw_pairs)
  require(refs()==a['refs'] and inventory_ok(pins,read(D/'required-paths-reviewed.json')),'final pins/refs')
  require(time.monotonic()-started<=750 and time.monotonic()-cost_start<=600,'final global cap')
  record['all_passed']=True
 except BaseException as e:record['errors'].append(repr(e))
 finally:
  record['elapsed']=time.monotonic()-started;record['ended_ns']=time.time_ns();save(OUT/'invocation.json',record)
 return 0 if record['all_passed'] else 1
if __name__=='__main__':sys.exit(main())
