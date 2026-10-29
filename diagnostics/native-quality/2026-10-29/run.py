from pathlib import Path
import sys,json,time,subprocess,os
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D/'guard'))
import supervisor_reviewed as supervisor
import guard_reviewed as guard

def host(extra=()):
 h=json.loads((D/'historical-groups.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(h['groups']) if boot==h['boot_id'] else set();groups.update(extra);conflicts=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=guard.process_identity(int(p.name));comm=(p/'comm').read_text().strip()
   if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 if conflicts:raise RuntimeError('active Julia/group/session '+str(conflicts))
 mem=guard.memory()
 if guard.pressure(mem):raise RuntimeError('memory pressure')
 return dict(boot=boot,checked_groups=sorted(groups),conflicts=conflicts,memory=mem,refs={ref:subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse',ref],text=True).strip() for ref in ['HEAD','master','origin/master']})
if __name__=='__main__':
 name=sys.argv[1];command=json.loads((D/sys.argv[2]).read_text());pins=D/sys.argv[3];seconds=int(sys.argv[4]);out=D/name;out.mkdir()
 with (out/'preflight.json').open('x')as f:json.dump(host(),f,indent=2)
 start=time.monotonic();cmd=[sys.executable,'-B',str(D/'guard/guard_reviewed.py'),'run',str(pins),str(out/'guard'),'--expected-exit','0','--seconds',str(seconds-10),'--deadline',str(start+seconds-10),'--',*command]
 with(out/'invocation.json').open('x')as f:json.dump(dict(command=cmd,limit_seconds=seconds),f,indent=2)
 with(out/'guard.log').open('x')as log:result=supervisor.run(cmd,log,str(out/'guard'),start,seconds-2)
 with(out/'supervisor.json').open('x')as f:json.dump(result,f,indent=2)
 proc=json.loads((out/'guard/process.json').read_text());extra=[proc[k][v] for k in ['runner','child']for v in ['pgid','sid']]
 with(out/'postflight.json').open('x')as f:json.dump(host(extra),f,indent=2)
 print(json.dumps(dict(supervisor=result,reason=proc['reason'],pins_unchanged=proc['pins_unchanged'],returncode=proc['returncode'])))
 if proc['reason']!='exit0' or not proc['pins_unchanged']:sys.exit(1)
