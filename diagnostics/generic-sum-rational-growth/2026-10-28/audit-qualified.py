from common_ready import *
import tomllib,re,statistics as stats,math

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
 con=read('contract-ready.json');p=read('output/process.json');sup=read('supervisor.json');log=(D/'output/run.log').read_text();inv=read('invocation.json');res=read('reservation.json')
 need(p['returncode']==1 and p['pins_unchanged'] is True,'original failed child/pins preserved')
 need(sup['accepted'] is False and sup['returncode']==1 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'original rejected supervisor preserved')
 need(sup['elapsed_seconds']<=900,'original inclusive900deadline');need(not (D/'completed.json').exists(),'no original accepted completion')
 need(p['command']==con['command']==inv['Julia_command'] and p['pins_sha256']==sha(D/'pins-ready.json'),'exact command/pins')
 gate=read('output/gate.json');cur=read('output/current.json');permit=read('output/permit.json')
 need(p['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and p['child']==cur['child']==gate['identity'],'process identity linkage')
 need(gate['command']==permit['command']==cur['command']==con['command'] and gate['parent_death_signal']==9,'entry command/signal')
 need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'entry hash linkage')
 need(sha(D/'output/pins.json')==sha(D/'pins-ready.json'),'exact copied pins')
 need(res['guard_deadline']==res['started_monotonic']+892 and res['outer_deadline']==res['started_monotonic']+900,'shared deadlines')
 need('Error During Test' not in log,'no test errors')
 errors=re.findall(r'^ERROR: (.*)$',log,re.M);need(errors==['LoadError: Some tests did not pass: 111259 passed, 90 failed, 0 errored, 0 broken.'],'only original known Test failure error')
 line=next((x for x in log.splitlines() if x.startswith('Sum rational growth whole-function comparison') and '|' in x),None);need(line is not None,'ordinary root summary')
 header=next(x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x);need(header.split('|',1)[1].split()==['Pass','Fail','Total','Time'],'exact original summary schema')
 cols=line.split('|',1)[1].split();need(len(cols)==4 and [int(v) for v in cols[:3]]==[111259,90,111349],'exact preserved original totals');assertions=111259
 locations=re.findall(r'Test Failed at (.*?):(\d+)',log);need(len(locations)==90 and all(p==str(D/'extra-tests-ready.jl') and int(n)==127 for p,n in locations),'only exact decoder oracle failures')
 need('SUM_RATIONAL_GROWTH_COMPLETE' not in log,'no fabricated original success marker')
 qualified=read('correctness-qualification/audit.json');review=read('correctness-qualification/result-review.json')
 need(qualified['accepted'] is True and qualified['assertions']==28227 and qualified['measured_windows']==0 and review['accepted'] is True and review['findings']==[],'separate correctness qualification')
 for p,h in review['bindings'].items():need(sha(p)==h,'qualified review binding '+p)
 raw=tomllib.loads((D/'output/results.toml').read_text());grid=read('expected-cases.json');cells=raw['cells'];prep=raw['preparation'];need(len(cells)==con['cases']==2636 and len(prep)==2674,'complete grid and preparation')
 contexts=list(dict.fromkeys(v['context'] for v in grid));need(re.findall(r'^CONTEXT (.*)$',log,re.M)==contexts and len(contexts)==19,'ordered contexts')
 need(set(raw)=={'cells','preparation'},'complete raw roots')
 ci=0;pi=0;gcwindows=0;summary=[]
 for context in contexts:
  for key in ['correctness','GC']:
   pp=prep[pi];pi+=1;need(set(pp)=={'context',key} and pp['context']==context,'context preparation');costcheck(pp[key])
  for spec in [v for v in grid if v['context']==context]:
   cell=cells[ci];ci+=1
   need(set(cell)==set(spec)|{'windows'},'complete cell fields')
   need(all(type(cell[k]) is type(v) and cell[k]==v for k,v in spec.items()),'exact typed cell order '+spec['id'])
   windows=cell['windows'];need(len(windows)==18,'fixed9pairs')
   for j,w in enumerate(windows):
    pair=j//2+1;arms=['original',spec['variant']] if pair%2 else [spec['variant'],'original']
    need(type(w['pair']) is int and w['pair']==pair and type(w['arm']) is str and w['arm']==arms[j%2],'alternating typed pair order')
    samplecheck({k:v for k,v in w.items() if k not in ['pair','arm']});need(w['compile_seconds']==w['recompile_seconds']==0,'all measured compilezero');gcwindows+=w['gc_seconds']>0
    if spec['scope'] in ['growth','rows']:need(type(w['result']) is float and math.isfinite(w['result']),'float result')
    elif spec['scope']=='scheduled':need(type(w['result']) is str and w['result'] in ['none','limit','fill','pivot_growth','residual','cost'],'symbol result')
    else:need(type(w['result']) is int and w['result'] in [0,1],'integer result')
   pairrows=[]
   for pair in range(1,10):
    a=next(w for w in windows if w['pair']==pair and w['arm']=='original');b=next(w for w in windows if w['pair']==pair and w['arm']==spec['variant']);need(type(a['result']) is type(b['result']) and a['result']==b['result'],'all measured typed results')
    pairrows.append((a,b))
   row=dict(spec)
   for k in ['seconds','bytes','events']:
    ratios=[quotient(a[k],b[k]) for a,b in pairrows];valid=all(x is not None for x in ratios);median=stats.median(ratios) if valid else None
    row[k]=dict(before=stats.median(a[k] for a,b in pairrows),after=stats.median(b[k] for a,b in pairrows),paired_ratios=ratios,paired_median=median,paired_min=min(ratios) if valid else None,paired_max=max(ratios) if valid else None,paired_MAD=stats.median(abs(x-median) for x in ratios) if valid else None,undefined_zero_baseline=sum(x is None for x in ratios))
   summary.append(row)
   pp=prep[pi];pi+=1;need(set(pp)=={'cell','fixture','validation','final_validation','cold','warm','resets'} and pp['cell']==spec['id'],'complete cell prep')
   for k in ['fixture','validation','final_validation']:costcheck(pp[k])
   need(len(pp['cold'])==2 and len(pp['warm'])==6 and len(pp['resets'])==18,'prep counts')
   for arr in [pp['cold'],pp['warm']]:
    for z in arr:need(set(z)=={'cost','reset'},'cold/warm fields');samplecheck(z['cost']);costcheck(z['reset'])
   for z in pp['resets']:costcheck(z)
 need(ci==2636 and pi==2674 and sum(len(v['windows']) for v in cells)==47448,'full grid counts')
 resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()];need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resources')
 need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal RAM/swap')
 unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];put('audit-host.json',host(extra));put('summary-qualified.json',summary)
 put('audit-qualified.json',dict(accepted=True,original_run_accepted=False,original_assertions_passed=assertions,original_failed_assertions=90,qualification_assertions=qualified['assertions'],postexit_auditor_not_launchpin=True,cases=2636,windows=47448,preparation=2674,gc_windows=gcwindows,compiled_zero=True,elapsed_shared_seconds=sup['elapsed_seconds'],bindings={str(D/n):sha(D/n) for n in ['audit-qualified.py','contract-ready.json','pins-ready.json','output/results.toml','output/run.log','output/process.json','summary-qualified.json','correctness-qualification/audit.json','correctness-qualification/result-review.json']}))
 print(json.dumps({k:v for k,v in read('audit-qualified.json').items() if k!='bindings'}))
if __name__=='__main__':main()
