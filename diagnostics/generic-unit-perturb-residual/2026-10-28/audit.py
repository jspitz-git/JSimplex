from common import *
import tomllib,re,statistics as stats,math
import os
# Record this new postexit observer's identity without granting any exception.
observation_stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
observation=dict(pid=os.getpid(),ppid=os.getppid(),pgid=int(observation_stat[2]),sid=int(observation_stat[3]),start_ticks=int(observation_stat[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=[x.decode(errors='replace') for x in Path('/proc/self/cmdline').read_bytes().split(b'\0') if x])
put('audit-invoker.json',observation)

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
 con=read('contract.json');p=read('output/process.json');sup=read('supervisor.json');log=(D/'output/run.log').read_text();inv=read('invocation.json');res=read('reservation.json')
 need(p['returncode']==0 and p['pins_unchanged'] is True,'successful child and pins')
 need(sup['accepted'] is True and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'successful guard supervisor')
 need(sup['elapsed_seconds']<=900 and read('completed.json')['accepted'] is True,'inclusive900completed')
 need(p['command']==con['command']==inv['Julia_command'] and p['pins_sha256']==sha(D/'pins.json'),'exact command/pins')
 gate=read('output/gate.json');cur=read('output/current.json');permit=read('output/permit.json')
 need(p['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and p['child']==cur['child']==gate['identity'],'process identity linkage')
 need(gate['command']==permit['command']==cur['command']==con['command'] and gate['parent_death_signal']==9,'entry command/signal')
 need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'entry hashes')
 need(sha(D/'output/pins.json')==sha(D/'pins.json'),'copied pins')
 need(res['guard_deadline']==res['started_monotonic']+892 and res['outer_deadline']==res['started_monotonic']+900,'shared deadlines')
 need(not re.search(r'Test Failed|Error During Test|^ERROR:|Test Broken',log,re.M),'ordinary all pass')
 header=next(x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x);need(header.split('|',1)[1].split()==['Pass','Total','Time'],'ordinary root schema')
 line=next(x for x in log.splitlines() if x.startswith('Unit perturb residual whole-function comparison') and '|' in x);cols=line.split('|',1)[1].split()
 need(len(cols)==3 and cols[0].isdigit() and cols[0]==cols[1] and int(cols[0])>1000,'ordinary root totals');assertions=int(cols[0])
 need('UNIT_PERTURB_RESIDUAL_COMPLETE cells='+str(con['cases']) in log,'completion marker')
 raw=tomllib.loads((D/'output/results.toml').read_text());grid=read('expected-cases.json');cells=raw['cells'];prep=raw['preparation']
 need(len(cells)==con['cases']==len(grid) and len(prep)==len(grid)+38,'complete grid and prep')
 contexts=list(dict.fromkeys(v['context'] for v in grid));need(re.findall(r'^CONTEXT (.*)$',log,re.M)==contexts and len(contexts)==19,'ordered contexts')
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
    if spec['scope'] in ['dual','primal']:need(type(w['result']) is int and w['result']>=0,'row index checksum')
    else:need(type(w['result']) is float and math.isfinite(w['result']),'float result checksum')
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
 need(ci==len(grid) and pi==len(grid)+38 and sum(len(v['windows']) for v in cells)==con['measured_windows'],'full counts')
 resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()]
 need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'resources')
 need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminalmemory')
 unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];put('audit-host.json',host(extra));put('summary.json',summary)
 put('audit.json',dict(accepted=True,assertions=assertions,cases=len(grid),windows=con['measured_windows'],preparation=len(prep),gc_windows=gcwindows,compiled_zero=True,elapsed_shared_seconds=sup['elapsed_seconds'],auditor_bound_separately_to_admission=True,auditor_in_actual_launchpins=True,bindings={str(D/n):sha(D/n) for n in ['audit.py','contract.json','pins.json','output/results.toml','output/run.log','output/process.json','summary.json','audit-invoker.json']}))
 print(json.dumps({k:v for k,v in read('audit.json').items() if k!='bindings'}))
if __name__=='__main__':main()
