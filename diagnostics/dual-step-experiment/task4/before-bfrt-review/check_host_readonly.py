from pathlib import Path
import json,os,time,subprocess,fcntl,hashlib
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task4';O=Path('/tmp/task4-green-review');h=json.loads((D/'host.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(h['checked_groups']);red=json.loads((D/'red-run/guard/process.json').read_text());actual=[]
for k in ['runner','child']:
 a=red[k]
 if a['boot_id']==boot:groups.update((a['pgid'],a['sid']));actual.append({k:{x:a[x] for x in ['pid','pgid','sid','start_ticks','boot_id']}})
seen=0;conflicts=[];julia=[];denied=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  s=(proc/'stat').read_text();f=s[s.rfind(')')+2:].split();a={'pid':int(proc.name),'pgid':int(f[2]),'sid':int(f[3]),'state':f[0]};comm=(proc/'comm').read_text().strip();seen+=1
  if a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  if comm.lower().startswith('julia'):julia.append(a|{'comm':comm})
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError as e:denied.append(str(e))
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
refs={'experiment':git(W,'rev-parse','HEAD'),'branch':git(W,'branch','--show-current'),'master':git('/home/jspitz/JSimplex.jl','rev-parse','HEAD'),'origin_master':git(W,'rev-parse','origin/master'),'diagnostic':git('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl','rev-parse','HEAD')}
mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};memory={'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']}
lock=Path('/tmp')/f'jsimplex-numerical-{os.getuid()}.lock';lock_free=True
if lock.exists():
 try:
  fd=os.open(lock,os.O_RDONLY|os.O_NOFOLLOW)
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(fd,fcntl.LOCK_UN)
  finally:os.close(fd)
 except OSError:lock_free=False
v={'at_unix':time.time(),'processes_scanned':seen,'permission_denials':denied,'known_group_session_ids':len(groups),'historical_ids':len(h['checked_groups']),'actual_RED_identities':actual,'conflicts':conflicts,'julia':julia,'boot_id':boot,'boot_matches':boot==h['boot_id'],'refs':refs,'memory':memory,'global_lock_available':lock_free,'green_output_unreserved':not(D/'green-run').exists()};v['passed']=seen>3 and not denied and not conflicts and not julia and v['boot_matches'] and memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2 and lock_free and v['green_output_unreserved'];(O/'host-evidence.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
