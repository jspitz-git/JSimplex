"""Prospective one-use fail-closed auditor. No Julia or launcher imports/calls."""
from common import *
import tomllib
def evidence_ok(raw,p,inv,res,a,pins,ph,resources,hashfn=sha):
 try:
  require(raw_ok(raw),'raw schema/oracle')
  require(terminal_ok(p),'terminal process')
  require(inv['returncode']==0 and type(inv['returncode']) is int and 'error' not in inv,'invocation result')
  require(inv['command']==guard_command() and inv['ended_ns']>=inv['started_ns'],'invocation command/times')
  require(inv['host']['matches']==[] and inv['post_host']['matches']==[],'host closure')
  require(set(inv['host']['groups'])==GROUPS,'full prior groups')
  require(set(inv['post_host']['groups'])==GROUPS|{p['runner']['pgid'],p['child']['pgid']},'full post groups')
  require(inv['host']['boot_id']==inv['post_host']['boot_id']==p['runner']['boot_id']==p['child']['boot_id'],'boot identities')
  for k in ('runner','child'):
   require(type(p[k]['pid']) is int and type(p[k]['start_ticks']) is int and p[k]['start_ticks']>0 and bool(p[k]['command']),'process identity')
  require(p['command']==command() and p['cwd']==str(R) and p['pins_sha256']==ph,'process command/pins/cwd')
  require(res['command']==command() and res['output']==str(OUT) and res['pins_sha256']==ph and res['refs']==a['refs'],'reservation linkage')
  require(res['allowance_sha256']==hashfn(D/'allowance.json') and inv['reservation_sha256']==hashfn(D/'attempt-reserved.json'),'reserved hashes')
  require(allowance_ok(a,ph,a['refs'],hashfn),'allowance hashes')
  require(bool(resources),'no resource samples')
  last=-1
  for s in resources:
   require(type(s['elapsed']) in (int,float) and math.isfinite(s['elapsed']) and last<=s['elapsed']<=120,'resource elapsed')
   last=s['elapsed'];require(type(s['available_kib']) is int and s['available_kib']>=6*1024**2 and type(s['swap_used_kib']) is int and 0<=s['swap_used_kib']<=1024**2,'resource pressure')
  return True
 except (KeyError,TypeError,ValueError,OSError):return False

def main():
 result={'all_passed':False,'checks':{},'sha256':{}}
 try:
  names=['process.json','current.json','pins.json','run.log','resources.jsonl','qualification.toml']
  require({p.name for p in OUT.iterdir()}==set(names),'output incomplete or extra paths')
  require(all((OUT/n).is_file() and not (OUT/n).is_symlink() for n in names),'output files')
  paths=[OUT/n for n in names]+[D/n for n in ('launcher.log','invocation.json','attempt-reserved.json','allowance.json','launch-pins.json','numerical-review.md')]
  require(all(p.is_file() and not p.is_symlink() for p in paths),'missing terminal/launcher evidence')
  ph=sha(D/'launch-pins.json');pins=read(D/'launch-pins.json');a=read(D/'allowance.json')
  require(manifest_ok(pins,read(D/'required-paths.json')),'changed launch pins')
  require({str(D/n) for n in FINAL_NAMES}.issubset(pins['inventory']),'final dependencies')
  require(read(OUT/'pins.json')==pins,'guard manifest differs')
  p=read(OUT/'process.json');cur=read(OUT/'current.json')
  require(all(cur[k]==p[k] for k in ('runner','child','command','cwd','pins_sha256','started')),'current/terminal identity')
  raw=tomllib.loads((OUT/'qualification.toml').read_text());resources=[json.loads(s) for s in (OUT/'resources.jsonl').read_text().splitlines()]
  inv=read(D/'invocation.json');res=read(D/'attempt-reserved.json')
  require(evidence_ok(raw,p,inv,res,a,pins,ph,resources),'raw/process/allowance/invocation audit')
  require(refs()==a['refs'],'refs changed')
  require(not absent([p['runner']['pgid'],p['child']['pgid']])['matches'],'live group/session/Julia')
  review=(D/'numerical-review.md').read_text();require('ACCEPTED S4-AB numerical admission.' in review and ph in review,'numerical review')
  result['checks']=dict.fromkeys(['exact_24_lifecycles_4_work_12_cost_cases','terminal_limits_exit_pins','complete_logs_invocation_reservation','full_groups_sessions_and_identities','all_launch_and_admission_bindings','current_refs_unchanged'],True)
  from oracle import analyze
  result['summary']=analyze(raw)
  result['sha256']={str(q):sha(q) for q in paths};result['all_passed']=True
 except BaseException as e:result['error']=repr(e)
 dump(D/'audit.json',result)
 print(json.dumps(result['checks']))
 return 0 if result['all_passed'] else 1
if __name__=='__main__':sys.exit(main())
