"""S4-Z offline admission helpers. Importing launches no process."""
from pathlib import Path
import hashlib,json,os,sys,subprocess,time,math
D=Path(__file__).resolve().parent;R=D.parents[3];Y=D.parent/'S4-Y'
OUT=R/'.superpowers/simplex-core-architecture/S4-Z/qualification-1'
WRAPPER=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
GROUPS={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746,84681,84689,89395,89399,90313,90323,128482,128483}
FINAL_NAMES=('admission-pins.json','required-paths.json','final-review.md','review.json','closure.json','publication.json')
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);tmp=p.with_name(p.name+'.pending')
 with tmp.open('x') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.link(tmp,p);tmp.unlink()
def command():
 code='using JSimplex; realpath(pathof(JSimplex)) == realpath('+json.dumps(str(R/'src/JSimplex.jl'))+') || error("wrong JSimplex source"); include('+json.dumps(str(Y/'driver-reviewed.jl'))+')'
 return ['/bin/bash',str(WRAPPER),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(R),'-e',code,'--',str(OUT)]
def guard_command():return [sys.executable,str(D/'guard.py'),'run',str(D/'launch-pins.json'),str(OUT),'--seconds','120','--',*command()]
def refs():
 return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,Path('/home/jspitz/JSimplex.jl'))}
def absent(extra=()):
 groups=GROUPS|set(extra);matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split();comm=(p/'comm').read_text().strip()
   if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches)
def manifest_ok(pins,required,hashfn=sha):
 try:
  inv=pins['inventory']
  return (pins['trees']==[] and pins['inputs']==[] and set(pins['files'])==set(inv) and set(required).issubset(inv) and
    all(inv[p]['sha256']==h for p,h in required.items()) and
    all(hashfn(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in inv.items()))
 except (KeyError,TypeError,OSError):return False
def allowance_ok(a,pin_hash,current_refs,hashfn=sha):
 try:
  mandatory={str(D/n) for n in (*FINAL_NAMES,'common.py','guard.py','launcher.py','audit.py','admission.md','launch-pins.json','numerical-review.md')}|{str(Y/'driver-reviewed.jl')}
  return (a['accepted'] is True and a['numerical_allowance'] is True and a['unresolved_findings']==[] and
   type(a['attempts']) is int and a['attempts']==1 and a['stage']=='S4-Z-qualification-1' and
   type(a['human_authorization']) is str and bool(a['human_authorization'].strip()) and
   a['refs']==current_refs and a['command']==command() and a['output']==str(OUT) and a['pins_sha256']==pin_hash and
   mandatory.issubset(a['sha256']) and a['sha256'][str(D/'launch-pins.json')]==pin_hash and
   all(hashfn(p)==h for p,h in a['sha256'].items()))
 except (KeyError,TypeError,OSError):return False
def terminal_ok(p):
 try:
  t=p['elapsed_including_launch'];m=p['terminal_memory']
  return (p['reason']=='exit0' and type(p['returncode']) is int and p['returncode']==0 and p['pins_unchanged'] is True and
   type(t) in (int,float) and math.isfinite(t) and 0<=t<=120 and
   type(m['available_kib']) is int and m['available_kib']>=6*1024**2 and type(m['swap_used_kib']) is int and 0<=m['swap_used_kib']<=1024**2)
 except (KeyError,TypeError):return False
STAGE_CHECKS=('forward_unit_solution','transpose_unit_solution','workspace_owner','dictionary_owners','maxima_owners','retained_dimensions','input_preserved')
CHECKS={f'stage_{i}_{k}' for i in range(1,5) for k in STAGE_CHECKS}|{'saved_forward_unit_solution','saved_transpose_unit_solution','saved_no_workspace_or_spare','saved_dimension','small_reset_route'}
COUNT_FIELDS=('dimension','row_dictionary_count','column_dictionary_count','row_entries','column_entries','maxima_length','valid_length','active_rows_length','active_columns_length','workspace_graph_bytes','backend_graph_bytes','lower_pool_count','upper_pool_count','core_rows')
def raw_ok(raw):
 try:
  if set(raw)!={'cases','errors','all_passed'} or raw['errors']!=[] or raw['all_passed'] is not True:return False
  cases=raw['cases']
  if type(cases) is not list or len(cases)!=2:return False
  for c,kind in zip(cases,('sparse','dense')):
   if set(c)!={'kind','checks','snapshots'} or c['kind']!=kind or set(c['checks'])!=CHECKS or not all(v is True for v in c['checks'].values()):return False
   if type(c['snapshots']) is not list or len(c['snapshots'])!=4:return False
   for i,s in enumerate(c['snapshots'],1):
    if set(s)!=set(COUNT_FIELDS)|{'label','has_spare','spare_dimension'} or s['label']!=f'stage_{i}':return False
    if not all(type(s[k]) is int and s[k]>=0 for k in COUNT_FIELDS):return False
    if type(s['has_spare']) is not bool or type(s['spare_dimension']) is not int:return False
    if s['spare_dimension']<(-1 if not s['has_spare'] else 0) or (not s['has_spare'] and s['spare_dimension']!=-1):return False
    dim=128 if i in (1,4) else 8;active=dim if kind=='sparse' else 128
    if s['dimension']!=dim or s['active_rows_length']!=active or s['active_columns_length']!=active:return False
    if any(s[k]!=128 for k in ('row_dictionary_count','column_dictionary_count','maxima_length','valid_length')):return False
  return True
 except (KeyError,TypeError,ValueError):return False
