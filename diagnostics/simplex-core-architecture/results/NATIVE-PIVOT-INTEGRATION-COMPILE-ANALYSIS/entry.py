from pathlib import Path
import json,subprocess,time,hashlib
Q=Path(__file__).resolve().parent;R=Q.parents[3];K=Q.parent/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION'
def need(x,m):
 if not x: raise RuntimeError(m)
def save(n,z):
 with (Q/n).open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
groups=json.loads((K/'closure-host.json').read_text())['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];inaccessible=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();c=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:inaccessible.append(int(p.name))
  except FileNotFoundError:pass
  if int(s[2]) in groups or int(s[3]) in groups or c.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(s[2]),sid=int(s[3]),start_ticks=int(s[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=c,exe=exe,boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
head=git('rev-parse','HEAD');master=git('rev-parse','master');remote=dict((b,a) for a,b in (x.split() for x in git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master').splitlines()))
z=dict(time=time.time(),boot_id=boot,head=head,master=master,remote=remote,groups=groups,matches=matches,inaccessible_exe_pids=inaccessible,scope='Process stat/comm/readable executable; inaccessible exe links remain visibility limit')
save('host.json',z)
need(head=='e649eb18798611c0a46ca3ef5e12b1416acc2b40' and master=='6f68e24e8ddac42b948da8fcc2d636c010751194','Refs')
need(remote['refs/heads/codex/simplex-core-architecture']==head and remote['refs/heads/master']==master,'Remote')
need(len(groups)==218 and not matches,'Processes')
need(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes')
for src,dest in [('diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-compile-analysis'),('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-compile-analysis')]:
 with (Q/dest).open('xb') as f:f.write((R/src).read_bytes())
print(dict(entry=True,groups=len(groups),head=head,master=master))
