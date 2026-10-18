from pathlib import Path
import json,os,time,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';entry=json.loads((E/'host.json').read_text());groups=set(entry['groups']);matches=[];hidden=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text();x=st[st.rindex(')')+2:].split();comm=(p/'comm').read_text().strip();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');exe=''
  try:exe=os.readlink(p/'exe')
  except OSError:hidden.append(int(p.name))
  if int(x[2]) in groups or int(x[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(x[2]),session=int(x[3]),start_ticks=int(x[19]),command=cmd,comm=comm,exe=exe))
 except (OSError,ValueError):pass
refs={k:subprocess.check_output(['git','rev-parse',k],text=True).strip() for k in entry['refs']}
r=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_exe_pids=hidden,refs=refs,scope=entry['scope'])
with (E/'host-closure.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
if matches or refs!=entry['refs']:raise RuntimeError('host gate')
print('Fresh host closure: refs unchanged,',len(groups),'groups AND sessions, no visible Julia; exe visibility limits recorded')
