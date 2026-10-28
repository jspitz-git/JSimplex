from pathlib import Path
import sys,json,tomllib,statistics as stats,math,re,hashlib,datetime,collections
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28')
sys.path.insert(0,str(D))
import common_final as c

def check(v,message):
 if not v: raise AssertionError(message)
def read(n):return json.loads((D/n).read_text())
def digest(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def publish(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
c.unchanged()
for name,count in [('pins.json',1251),('pins-ready.json',1268),('pins-final.json',1285)]:
 pins=read(name);check(len(pins['inventory'])==count,name+' count')
 for n,v in pins['inventory'].items():check(str(Path(n).resolve(strict=True))==v['resolved'] and digest(n)==v['sha256'],n)
 for tree in pins['trees']:check({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},tree)
for name in ['admission.json','admission-final.json','audit.json']:
 for n,v in read(name)['bindings'].items():check(digest(n)==v,'bound '+n)
check(read('admission.json')['accepted'] is False and read('admission-final.json')['accepted'] is True,'admission preservation')
con=read('contract-final.json');proc=read('output/process.json');sup=read('supervisor.json');done=read('completed.json');inv=read('invocation.json');res=read('reservation.json');cur=read('output/current.json');gate=read('output/gate.json');permit=read('output/permit.json')
check(proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True,'child')
check(sup['accepted'] is True and sup['returncode']==0 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','abnormal_cleanup_attempted','child_cleanup_attempted','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup,'supervisor')
check(done['accepted'] is True and done['pins_unchanged'] is True and done['limit_seconds']==900 and 0<=sup['elapsed_seconds']<=done['elapsed_shared_seconds']<=900,'inclusive completion')
check(proc['command']==inv['Julia_command']==con['command'],'Julia command')
check(proc['pins_sha256']==res['pins_sha256']==digest(D/'pins-final.json')==digest(D/'output/pins.json'),'pins')
check(res['admission_sha256']==digest(D/'admission-final.json'),'admission sha')
check(res['attempt']==1 and res['started_monotonic']==inv['common_started'] and res['guard_deadline']==res['started_monotonic']+892==inv['guard_deadline'] and res['outer_deadline']==res['started_monotonic']+900==inv['outer_deadline'],'deadlines')
check(proc['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and proc['child']==cur['child']==gate['identity'],'identities')
check(gate['command']==permit['command']==cur['command']==con['command'] and gate['parent_death_signal']==9,'gate')
check(gate['current_sha256']==permit['current_sha256']==digest(D/'output/current.json') and gate['permit_sha256']==digest(D/'output/permit.json'),'gate hashes')
check(sup['guard_identity']['command']==' '.join(inv['command'])+' ','actual runner invocation')
check(con['attempts']==1 and con['contexts']==19 and con['cases']==1192 and con['measured_windows']==21456 and con['ordinary_Test'] is True and con['shared_limit_seconds']==900 and con['guard_limit_seconds']==892 and con['expected_exit']==0,'contract')
check(proc['command'][-2]==str(D/'driver-final.jl') and proc['command'][-1]==str(D/'output/results.toml'),'canonical driver')
for flag in ['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project=/home/jspitz/JSimplex.jl']:check(flag in proc['command'],'launch flag '+flag)
log=(D/'output/run.log').read_text();check(not re.search(r'Test Failed|Error During Test|^ERROR:|Test Broken',log,re.M),'no failure')
match=re.search(r'^Residual pivot crash whole-function comparison\s*\|\s*(\d+)\s+(\d+)\s+(.+)$',log,re.M);check(match is not None and match[1]==match[2]=='45382','ordinary pass counts')
check(next(x for x in log.splitlines() if x.startswith('Test Summary:')).split('|')[1].split()==['Pass','Total','Time'],'ordinary schema')
check(log.count('RESIDUAL_PIVOT_CRASH_COMPLETE cells=1192')==1,'unique completion')
grid=read('expected-cases.json');check(tomllib.loads((D/'grid.toml').read_text())['cells']==grid,'TOML grid');contexts=list(dict.fromkeys(x['context'] for x in grid));check(re.findall(r'^CONTEXT (.*)$',log,re.M)==contexts,'contexts')
raw=tomllib.loads((D/'output/results.toml').read_text());check(set(raw)=={'cells','preparation'} and len(raw['cells'])==1192 and len(raw['preparation'])==1230,'raw roots and count')
costkeys={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
def cost(v):
 check(set(v)==costkeys,'cost schema')
 for k in costkeys:
  if k in ('bytes','events'):check(type(v[k]) is int and v[k]>=0,'counter')
  else:check(type(v[k]) in (int,float) and math.isfinite(v[k]) and v[k]>=0,'time')
def sample(v):
 check(set(v)==costkeys|{'result','capture_preparation'},'sample schema');cost({k:v[k] for k in costkeys});cost(v['capture_preparation'])
summary=[];gcwindows=[];metrics={};windows_count=0
for spec,cell in zip(grid,raw['cells']):
 check(set(cell)==set(spec)|{'windows'} and all(type(cell[k]) is type(v) and cell[k]==v for k,v in spec.items()),'typed cell')
 check(len(cell['windows'])==18,'windowcount');windows_count+=18
 for i,w in enumerate(cell['windows']):
  pair=i//2+1;expected=('original',spec['variant']) if pair%2 else (spec['variant'],'original')
  check(type(w['pair']) is int and w['pair']==pair and w['arm']==expected[i%2],'alternating pairs')
  sample({k:v for k,v in w.items() if k not in ['pair','arm']});check(w['compile_seconds']==w['recompile_seconds']==0,'no measured compilation')
  check((type(w['result']) is int and w['result']>=0) if spec['scope']=='crash' else (type(w['result']) is float and math.isfinite(w['result'])),'typed result')
  if w['gc_seconds']>0:gcwindows.append(dict(cell=spec['id'],pair=pair,arm=w['arm'],gc_seconds=w['gc_seconds']))
 pairs=[]
 for pair in range(1,10):
  a=next(w for w in cell['windows'] if w['pair']==pair and w['arm']=='original');b=next(w for w in cell['windows'] if w['pair']==pair and w['arm']==spec['variant'])
  check(type(a['result']) is type(b['result']) and a['result']==b['result'],'all paired checksums');pairs.append((a,b))
 row=dict(spec)
 for k in ('seconds','bytes','events'):
  ratios=[1.0 if a[k]==b[k]==0 else b[k]/a[k] if a[k]>0 else None for a,b in pairs];valid=None not in ratios;med=stats.median(ratios) if valid else None
  row[k]=dict(before=stats.median(a[k] for a,b in pairs),after=stats.median(b[k] for a,b in pairs),paired_ratios=ratios,paired_median=med,paired_min=min(ratios) if valid else None,paired_max=max(ratios) if valid else None,paired_MAD=stats.median(abs(x-med) for x in ratios) if valid else None,undefined_zero_baseline=ratios.count(None))
 summary.append(row)
check(windows_count==21456 and len(gcwindows)==14,'windows and GC count')
check(summary==read('summary.json'),'all recomputed summary fields match published')
prep=raw['preparation'];pos=0;prep_totals=collections.defaultdict(lambda:dict(seconds=0.0,bytes=0,events=0,gc_seconds=0.0,compile_seconds=0.0,recompile_seconds=0.0))
def add(kind,v):
 cost(v)
 for k in costkeys:prep_totals[kind][k]+=v[k]
for context in contexts:
 for category in ['correctness','GC']:
  p=prep[pos];pos+=1;check(set(p)=={'context',category} and p['context']==context,'context prep order');add(category,p[category])
 for spec in (x for x in grid if x['context']==context):
  p=prep[pos];pos+=1;check(set(p)=={'cell','fixture','validation','final_validation','cold','warm','resets'} and p['cell']==spec['id'],'cellprep')
  for category in ['fixture','validation','final_validation']:add(category,p[category])
  check(len(p['cold'])==2 and len(p['warm'])==6 and len(p['resets'])==18,'prep lengths')
  for category in ['cold','warm']:
   for z in p[category]:
    check(set(z)=={'cost','reset'},'warm/cold schema');sample(z['cost']);add(category,{k:z['cost'][k] for k in costkeys});add(category+'_capture',z['cost']['capture_preparation']);add(category+'_reset',z['reset'])
  for z in p['resets']:add('measured_reset',z)
check(pos==1230,'prep consumed')
for cell in raw['cells']:
 for z in cell['windows']:add('measured',{k:z[k] for k in costkeys});add('measured_capture',z['capture_preparation'])
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()];check(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resources')
check(all(a['elapsed']<=b['elapsed'] for a,b in zip(resources,resources[1:])),'resource ordering')
check(proc['terminal_memory']['available_kib']>=6*1024**2 and proc['terminal_memory']['swap_used_kib']<=1024**2,'terminal memory')
resource_stats=dict(samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_used_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=proc['child_maxrss_kib'],last_sample_elapsed=resources[-1]['elapsed'])
# Independently reconstruct fixture signs/nnz and bounded row rankings using exact integers.
ranking_comparisons={}
for spec in grid:
 if spec['scope']!='crash':continue
 n=spec['n'];dense=spec['density']=='dense';shape=spec['shape'];values=[]
 for i in range(1,n+1):
  if not dense and i%4:values.append(0);continue
  negative=shape=='negative' or shape=='mixed' and (i if dense else i//4)%2==1
  values.append((-1 if negative else 1)*((i*7)%n+1))
 check(sum(v!=0 for v in values)==(n if dense else n//4),'actual sparse density')
 check(shape!='mixed' or any(v<0 for v in values) and any(v>0 for v in values),'actual mixed signs')
 rows=[];comparisons=0;negative_comparisons=0
 for i,v in enumerate(values,1):
  if not v:continue
  position=None
  for j,r in enumerate(rows):
   comparisons+=1;negative_comparisons+=v<0
   if abs(v)>abs(values[r-1]):position=j;break
  if position is None:
   if len(rows)<spec['cap']:rows.append(i)
  else:
   rows.insert(position,i)
   if len(rows)>spec['cap']:rows.pop()
 check(all(w['result']==sum(rows) for w in next(x for x in raw['cells'] if x['id']==spec['id'])['windows']),'independent crash expected checksum')
 ranking_comparisons[spec['id']]=dict(left_abs_calls_removed=comparisons,negative_left_abs_calls_removed=negative_comparisons,expected_rows=rows)
# Check allocation-event savings against independent operation counts for all targeted measured pairs.
for cell in raw['cells']:
 for pair in range(1,10):
  a=next(x for x in cell['windows'] if x['arm']=='original' and x['pair']==pair);b=next(x for x in cell['windows'] if x['arm']==cell['variant'] and x['pair']==pair)
  if cell['type']=='BigFloat':
   expected=4*(cell['n']-1) if cell['variant']=='A' else (0 if cell['shape']=='negative' else 12) if cell['variant']=='B' else 4*ranking_comparisons[cell['id']]['left_abs_calls_removed']
   check(a['events']-b['events']==expected,'predicted BF work events '+cell['id'])
  elif cell['variant']=='C' and cell['type']=='Rational{BigInt}':check(a['events']-b['events']==2*ranking_comparisons[cell['id']]['negative_left_abs_calls_removed'],'predicted rational C events')
groups=[]
for keys in [('variant','type'),('variant','type','shape'),('variant','type','density','shape'),('variant','type','n','mode','cap','recycled')]:
 bins=collections.defaultdict(list)
 for row in summary:bins[tuple(row[k] for k in keys)].append(row)
 for key,rows in bins.items():
  group=dict(grouping=list(keys),key=dict(zip(keys,key)),cells=len(rows))
  for metric in ('seconds','bytes','events'):
   ratios=[x[metric]['paired_median'] for x in rows];check(None not in ratios,'defined cell medians')
   group[metric]=dict(median_of_paired_cell_medians=stats.median(ratios),min_cell_median=min(ratios),max_cell_median=max(ratios),lower_cells=sum(x<1 for x in ratios),equal_cells=sum(x==1 for x in ratios),higher_cells=sum(x>1 for x in ratios),median_cell_MAD=stats.median(x[metric]['paired_MAD'] for x in rows))
  groups.append(group)
extra=[proc[k][v] for k in ['runner','child'] for v in ['pgid','sid']];host=c.host(extra);check(len(host['groups'])==661,'all groups plus completed owned sessions')
check(c.git(['ls-remote','origin','refs/heads/master']).split()[0]==c.TARGET,'live master')
check(c.git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],c.R).split()[0]=='94394f8b91a4670c24f7fb9e7c23c468e4cadfd4','live diagnostics')
check(len(read('audit-host.json')['groups'])==661 and read('audit.json')['auditor_in_actual_launchpins'] is True,'authoraudit host scope/membership')
remaining_correctness=45382-sum(18+2*(6+(2 if x['variant']=='B' else 1 if x['variant']=='C' else 0)) for x in grid)
out=dict(accepted_raw=True,assertions=45382,correctness_only_assertions=remaining_correctness,cases=1192,windows=21456,preparation_records=1230,measured_compilation_zero=True,gc_windows=gcwindows,groups=groups,preparation_totals=prep_totals,resources=resource_stats,ranking_work_counts=ranking_comparisons,all_published_summary_fields_recomputed=True,all_targeted_allocation_event_deltas_match_source_work_counts=True,completed_elapsed_seconds=done['elapsed_shared_seconds'],limitations=['first saved cell calls occur after correctness and are not isolated process startup or first-ever per-variant compilation','single process and nine pairs per cell; no independent process repetitions','all GC and outliers retained; short timings show quantization/control noise','PFI update numerical comparison only; other shared helper users require production regressions','no whole solver trajectory or native retained memory claim'])
publish('result-review-statistics.json',out);publish('result-review-host.json',host)
paths=['admission-final.json','ADMISSION-FINAL.md','admission-final-evidence.json','pins.json','pins-ready.json','pins-final.json','fixtures-final.jl','driver-final.jl','Reference.jl','A.jl','B.jl','C.jl','changes.json','contract-final.json','common_final.py','launch-final.py','audit-final.py','grid.toml','expected-cases.json','SCOPE-ERRATUM.md','FINAL-HARNESS-NOTE.md','audit.json','summary.json','completed.json','supervisor.json','invocation.json','reservation.json','launch-host.json','host-after.json','audit-host.json','audit-invoker.json','output/results.toml','output/run.log','output/process.json','output/resources.jsonl','output/current.json','output/gate.json','output/permit.json','output/pins.json','result-review-statistics.json','result-review-host.json']
publish('result-review-bindings.json',{str(D/n):digest(D/n) for n in paths})
print(json.dumps(dict(accepted_raw=True,assertions=45382,correctness_only_assertions=remaining_correctness,cases=1192,windows=21456,prep=1230,gc_windows=len(gcwindows),source_work_event_counts_verified=True,resources=resource_stats,host_time=host['time_utc'],groups=661)))
