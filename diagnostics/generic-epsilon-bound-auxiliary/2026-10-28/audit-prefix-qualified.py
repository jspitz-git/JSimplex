from common_qualified import *
import tomllib,re,statistics as stats,math
import os
# Record this new postexit observer's identity without granting any exception.
observation_stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
observation=dict(pid=os.getpid(),ppid=os.getppid(),pgid=int(observation_stat[2]),sid=int(observation_stat[3]),start_ticks=int(observation_stat[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=[x.decode(errors='replace') for x in Path('/proc/self/cmdline').read_bytes().split(b'\0') if x])
put('prefix-audit-invoker.json',observation)

def numeric(x):return type(x) in (int,float)
def costcheck(x):
 need(set(x)=={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'},'complete cost fields')
 need(all(numeric(x[k]) and math.isfinite(x[k]) and x[k]>=0 for k in ['seconds','gc_seconds','compile_seconds','recompile_seconds']),'finite nonnegative times')
 need(all(type(x[k]) is int and x[k]>=0 for k in ['bytes','events']),'integer allocation counters')
def samplecheck(x):
 need(set(x)=={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','result','capture_preparation'},'complete measurement fields')
 costcheck({k:x[k] for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']});costcheck(x['capture_preparation'])
def quotient(a,b):return 1.0 if a==b==0 else b/a if a>0 else None

def main():
 con=dict(read('contract-qualified.json'),cases=1196,measured_windows=21528);p=read('output/process.json');sup=read('supervisor.json');log=(D/'output/run.log').read_text();inv=read('invocation.json');res=read('reservation.json')
 need(p['returncode']==1 and p['pins_unchanged'] is True,'preserved failed child and unchanged pins')
 need(sup['accepted'] is False and sup['returncode']==1 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'failed Test exit, no timeout or cleanup error')
 need(sup['elapsed_seconds']<=900 and not (D/'completed.json').exists(),'failed attempt remains incomplete')
 need(p['command']==con['command']==inv['Julia_command'] and p['pins_sha256']==sha(D/'pins-qualified.json'),'exact command/pins')
 gate=read('output/gate.json');cur=read('output/current.json');permit=read('output/permit.json')
 need(p['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and p['child']==cur['child']==gate['identity'],'process identity linkage')
 need(gate['command']==permit['command']==cur['command']==con['command'] and gate['parent_death_signal']==9,'entry command/signal')
 need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'entry hashes')
 need(sha(D/'output/pins.json')==sha(D/'pins-qualified.json'),'copied pins')
 need(res['guard_deadline']==res['started_monotonic']+892 and res['outer_deadline']==res['started_monotonic']+900,'shared deadlines')
 need(log.count('Test Failed at ')==1 and log.count('Error During Test at ')==2,'exact preserved failure/error counts')
 need('fixtures.jl:162' in log and 'precision(::Type{Rational{BigInt}})' in log,'unsupported baseline rational route')
 header=next(x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x);need(header.split('|',1)[1].split()==['Pass','Fail','Error','Total','Time'],'failed root schema')
 line=next(x for x in log.splitlines() if x.startswith('Epsilon bound auxiliary whole-function comparison') and '|' in x);cols=line.split('|',1)[1].split()
 need(cols[:4]==['55626','1','2','55629'] and len(cols)==5,'exact failed original counts');assertions=55629
 need('EPSILON_BOUND_AUXILIARY_COMPLETE' not in log,'no successful completion claim')
 raw=tomllib.loads((D/'output/results.toml').read_text());grid=read('expected-cases.json')[:1196];cells=raw['cells'];prep=raw['preparation']
 need(len(cells)==con['cases']==len(grid) and len(prep)==len(grid)+36,'complete grid and prep')
 contexts=list(dict.fromkeys(v['context'] for v in grid));need(re.findall(r'^CONTEXT (.*)$',log,re.M)==contexts and len(contexts)==18,'ordered contexts')
 need(set(raw)=={'cells','preparation'},'complete raw roots')
 ci=0;pi=0;gcwindows=0;summary=[]
 for context in contexts:
  for k in ['correctness','GC']:
   pp=prep[pi];pi+=1;need(set(pp)=={'context',k} and pp['context']==context,'context prep');costcheck(pp[k])
  for spec in [v for v in grid if v['context']==context]:
   cell=cells[ci];ci+=1;need(set(cell)==set(spec)|{'windows'},'cell fields')
   need(all(type(cell[k]) is type(v) and cell[k]==v for k,v in spec.items()),'typed cell order '+spec['id'])
   windows=cell['windows'];need(len(windows)==18,'9pairs')
   for j,w in enumerate(windows):
    pair=j//2+1;arms=['original',spec['variant']] if pair%2 else [spec['variant'],'original']
    need(type(w['pair']) is int and w['pair']==pair and type(w['arm']) is str and w['arm']==arms[j%2],'alternating typed pair')
    samplecheck({k:v for k,v in w.items() if k not in ['pair','arm']});need(w['compile_seconds']==w['recompile_seconds']==0,'measuredcompilezero');gcwindows+=w['gc_seconds']>0
    if spec['scope']=='direction':need(type(w['result']) is bool and w['result']==(spec['mode']=='good'),'direction Boolean result')
    elif spec['scope']=='auxiliary':need(type(w['result']) is int and w['result']==con['optimal_status'],'whole auxiliary optimal status')
    else:need(type(w['result']) is float and math.isfinite(w['result']),'finite metric checksum')
   pairs=[]
   for pair in range(1,10):
    a=next(w for w in windows if w['pair']==pair and w['arm']=='original');b=next(w for w in windows if w['pair']==pair and w['arm']==spec['variant'])
    need(type(a['result']) is type(b['result']) and a['result']==b['result'],'all measured typed outputs');pairs.append((a,b))
   row=dict(spec)
   for k in ['seconds','bytes','events']:
    ratios=[quotient(a[k],b[k]) for a,b in pairs];valid=all(x is not None for x in ratios);median=stats.median(ratios) if valid else None
    row[k]=dict(before=stats.median(a[k] for a,b in pairs),after=stats.median(b[k] for a,b in pairs),paired_ratios=ratios,paired_median=median,paired_min=min(ratios) if valid else None,paired_max=max(ratios) if valid else None,paired_MAD=stats.median(abs(x-median) for x in ratios) if valid else None,undefined_zero_baseline=sum(x is None for x in ratios))
   summary.append(row)
   pp=prep[pi];pi+=1;need(set(pp)=={'cell','fixture','validation','final_validation','cold','warm','resets'} and pp['cell']==spec['id'],'complete cellprep')
   for k in ['fixture','validation','final_validation']:costcheck(pp[k])
   need(len(pp['cold'])==2 and len(pp['warm'])==6 and len(pp['resets'])==18,'prep counts')
   for arr in [pp['cold'],pp['warm']]:
    for z in arr:need(set(z)=={'cost','reset'},'coldwarmfields');samplecheck(z['cost']);costcheck(z['reset'])
   for z in pp['resets']:costcheck(z)
 need(ci==len(grid) and pi==len(grid)+36 and sum(len(v['windows']) for v in cells)==con['measured_windows'],'full counts')
 resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()]
 need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'resources')
 need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminalmemory')
 unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];put('prefix-audit-host.json',host(extra));put('summary-prefix.json',summary)
 put('audit-prefix.json',dict(accepted=True,scope='completed-prefix-only; original attempt remains failed',original_root_passed=55626,original_root_failed=1,original_root_errors=2,original_attempt_accepted=False,assertions=assertions,cases=len(grid),windows=con['measured_windows'],preparation=len(prep),gc_windows=gcwindows,compiled_zero=True,failed_supervisor_elapsed_seconds=sup['elapsed_seconds'],auditor_bound_to_original_admission=False,auditor_in_actual_launchpins=False,prefix_auditor_separately_bound_to_remaining_admission=True,bindings={str(D/n):sha(D/n) for n in ['audit-prefix-qualified.py','audit-prefix.py','audit-qualified.py','contract-qualified.json','pins-qualified.json','output/results.toml','output/run.log','output/process.json','summary-prefix.json','prefix-audit-invoker.json','supervisor.json']}))
 print(json.dumps({k:v for k,v in read('audit-prefix.json').items() if k!='bindings'}))
if __name__=='__main__':main()
