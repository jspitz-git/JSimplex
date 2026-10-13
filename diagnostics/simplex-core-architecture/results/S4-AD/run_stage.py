"""Separate exclusive seal/launch/audit phases; one attempt per named stage."""
from common import *
from oracle import raw_ok
import tomllib

def seal(s,c):
 rv=read(s/'review.json');pins=read(s/'pins.json');ph=sha(s/'pins.json')
 require(rv['accepted'] is True and rv['unresolved_findings']==[] and all(v is True for v in rv['checks'].values()),'admission')
 require(rv['pins_sha256']==ph and all(sha(p)==h for p,h in rv['sha256'].items()),'review hashes')
 require('ACCEPTED S4-AD '+c['stage']+' admission.' in (s/'review.md').read_text() and ph in (s/'review.md').read_text(),'review marker')
 require(pins_ok(pins) and refs()==c['refs'],'pins/refs');h=host(c['groups']);require(not h['matches'],'host')
 require(not Path(c['output']).exists(),'output exists')
 dump(s/'allowance.json',dict(accepted=True,attempts=1,stage=c['stage'],human_authorization='Standing human short-attempt permission and explicit request to execute RED/GREEN/integration.',refs=refs(),host=h,pins_sha256=ph,sha256={str(s/n):sha(s/n) for n in ('review.md','review.json','config.json','driver-config.toml','pins.json')}))
 print('SEALED',c['stage'],len(pins['inventory']),flush=True)
def admission(s,c):
 a=read(s/'allowance.json');ph=sha(s/'pins.json');pins=read(s/'pins.json')
 require(a['accepted'] is True and type(a['attempts']) is int and a['attempts']==1 and a['stage']==c['stage'] and a['refs']==c['refs']==refs() and a['pins_sha256']==ph,'allowance/refs')
 require(all(sha(p)==h for p,h in a['sha256'].items()) and pins_ok(pins),'changed input')
 mandatory={str(D/n) for n in ('driver.jl','guard.py','common.py','oracle.py','run_stage.py','freeze_stage.py','schedule.json','synthetic.json')}|{str(s/n) for n in ('config.json','driver-config.toml')}|set(c['files'])|{str(Path(c['root'])/'src/markowitz_factorization.jl')}
 require(mandatory.issubset(pins['inventory']),'required paths missing')
 return a,pins,ph

def launch(s,c):
 with (s/'launcher.log').open('x') as log:
  inv=dict(command=guard_command(s,c),started_ns=time.time_ns(),returncode=None)
  try:
   a,pins,ph=admission(s,c);h=host(c['groups']);require(not h['matches'],'prior live process');inv['host']=h
   require(not Path(c['output']).exists(),'output exists')
   dump(s/'reservation.json',dict(stage=c['stage'],command=c['command'],output=c['output'],refs=refs(),pins_sha256=ph,allowance_sha256=sha(s/'allowance.json')))
   inv['reservation_sha256']=sha(s/'reservation.json')
   result=subprocess.run(guard_command(s,c),cwd=c['root'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);inv['returncode']=result.returncode
   p=read(Path(c['output'])/'process.json');inv['post_host']=host(set(c['groups'])|{p[k]['pgid'] for k in ('runner','child')});require(not inv['post_host']['matches'],'live postprocess')
  except BaseException as e:inv['error']=repr(e)
  finally:inv['ended_ns']=time.time_ns();dump(s/'invocation.json',inv)
 print(json.dumps(inv),flush=True)
 return 0 if inv.get('returncode')==c['expected_guard_exit'] and 'error' not in inv else 1

def audit(s,c):
 result=dict(all_passed=False,checks={},sha256={})
 try:
  a,pins,ph=admission(s,c);out=Path(c['output']);names={'process.json','current.json','pins.json','run.log','resources.jsonl','tests.toml'}
  require({p.name for p in out.iterdir()}==names and all((out/n).is_file() and not (out/n).is_symlink() for n in names),'raw files')
  p=read(out/'process.json');cur=read(out/'current.json');inv=read(s/'invocation.json');res=read(s/'reservation.json');raw=tomllib.loads((out/'tests.toml').read_text());samples=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
  require(raw_ok(raw,c),'Test result schema')
  require(p['reason']=='exit'+str(c['expected_child_exit']) and type(p['returncode']) is int and p['returncode']==c['expected_child_exit'] and p['pins_unchanged'] is True,'terminal exit')
  require(type(p['elapsed_including_launch']) in (int,float) and math.isfinite(p['elapsed_including_launch']) and 0<=p['elapsed_including_launch']<=120 and pressure_ok(p['terminal_memory']),'terminal resources')
  require(p['command']==c['command'] and p['cwd']==c['root'] and p['pins_sha256']==ph and read(out/'pins.json')==pins,'process bindings')
  require(all(cur[k]==p[k] for k in ('runner','child','command','cwd','pins_sha256','started')),'launch identity')
  groups=set(c['groups'])|{p[k]['pgid'] for k in ('runner','child')};h=host(groups)
  require(not h['matches'] and len(groups)==len(c['groups'])+2 and set(inv['host']['groups'])==set(c['groups']) and set(inv['post_host']['groups'])==groups and inv['host']['matches']==inv['post_host']['matches']==[],'all groups ANDsessions')
  require(inv['host']['boot_id']==inv['post_host']['boot_id']==h['boot_id']==p['runner']['boot_id']==p['child']['boot_id'],'boot')
  require(all(type(p[k]['start_ticks']) is int and p[k]['start_ticks']>0 and bool(p[k]['command']) for k in ('runner','child')),'process identities')
  require(type(inv['returncode']) is int and inv['returncode']==c['expected_guard_exit'] and 'error' not in inv and inv['command']==guard_command(s,c) and inv['ended_ns']>=inv['started_ns'],'invocation')
  require(res==dict(stage=c['stage'],command=c['command'],output=c['output'],refs=c['refs'],pins_sha256=ph,allowance_sha256=sha(s/'allowance.json')) and inv['reservation_sha256']==sha(s/'reservation.json'),'reservation linkage')
  require(bool(samples),'resource samples');last=-1
  for x in samples:
   require(type(x['elapsed']) in (int,float) and math.isfinite(x['elapsed']) and last<=x['elapsed']<=120 and pressure_ok(x),'resource sample');last=x['elapsed']
  result.update(all_passed=True,checks=dict.fromkeys(('exact_Test_results','terminal_exit_and_caps','all_source_runtime_admission_pins','process_current_identity','fresh_full_groups_ANDsessions_noJulia','invocation_reservation_allowance','every_resource_sample','refs_unchanged'),True),host=h,counts={x['file']:x['counts'] for x in raw['files']},resources=dict(samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_kib=max(x['swap_used_kib'] for x in samples),elapsed_including_launch=p['elapsed_including_launch']),sha256={str(q):sha(q) for q in [*[out/n for n in sorted(names)],*[s/n for n in ('config.json','driver-config.toml','pins.json','review.md','review.json','allowance.json','reservation.json','invocation.json','launcher.log')]]})
 except BaseException as e:result['error']=repr(e)
 # Preserve every existing raw file even on failure; never overwrite.
 out=Path(c['output']);portable=s/'raw';portable.mkdir()
 for p in out.iterdir():
  require(p.is_file() and not p.is_symlink(),'raw object');q=portable/p.name
  with q.open('xb') as f:f.write(p.read_bytes())
  require(sha(q)==sha(p),'portable mismatch')
 result['portable_sha256']={str(p):sha(p) for p in portable.iterdir()}
 dump(s/'audit.json',result);print(json.dumps({k:result[k] for k in result if k not in ('sha256','portable_sha256')}),flush=True)
 return 0 if result['all_passed'] else 1
if __name__=='__main__':
 require(len(sys.argv)==3 and sys.argv[1] in ('seal','launch','audit') and sys.argv[2] in ('red','green','master'),'phase and stage required')
 s=D/sys.argv[2];c=read(s/'config.json');require(c['stage']==sys.argv[2],'stage identity')
 sys.exit({'seal':seal,'launch':launch,'audit':audit}[sys.argv[1]](s,c) or 0)
