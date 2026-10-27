from pathlib import Path
import sys,json,re,tomllib,statistics,math
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import common as c
p=c.read('output/process.json');s=c.read('supervisor.json');done=c.read('completed.json');contract=c.read('contract.json');log=(D/'output/run.log').read_text()
c.need(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and s['accepted'] is True and done['accepted'] is True,'exit/guards')
c.need(done['elapsed_shared_seconds']<=600 and p['command']==contract['command'] and p['pins_sha256']==c.sha(D/'pins.json'),'deadline/command/pins')
root_summary=re.search(r'^Interval setup Devex whole-function comparison\s*\|\s*(\d+)\s+(\d+)\s+',log,re.M);c.need(root_summary and int(root_summary[1])==int(root_summary[2]) and int(root_summary[1])>1000,'ordinary fullpass summary')
c.need('Test Failed at ' not in log and 'Error During Test' not in log and not re.search(r'^ERROR:',log,re.M),'no errors/failures')
c.need('INTERVAL_SETUP_DEVEX_COMPARISON_COMPLETE cells=1813' in log,'completion')
data=tomllib.loads((D/'output/results.toml').read_text());fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'];c.need(data['cost_fields']==fields and data['window_fields']==['pair','arm',*fields,'sink'],'typed column schema')
contexts=[(f'BF{bits}_RoundingMode{{:{mode}}}()','BigFloat') for bits in [64,128,256] for mode in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
expected=[]
for label,t in contexts:
 for n,rows_count in [(16,8),(64,16)]:
  for density in ['sparse','dense']:
   for shape in (['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):
    for scope in ['rows','feasible','reduced','witness']:expected.append((label,t,n,rows_count,scope,density,shape,'A'))
    for scope in ['new','cold','rebase']:expected.append((label,t,n,rows_count,scope,density,shape,'B'))
    for scope in ['devex_shared','devex_solve']:expected.append((label,t,n,rows_count,scope,density,shape,'C'))
 for shape in (['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):expected.append((label,t,16,8,'leaving','sparse',shape,'C'))
c.need(len(data['cells'])==len(expected)==contract['cases']==1813,'exact matrix length')
def validcost(v):
 return type(v) is list and len(v)==6 and all(type(x) in [int,float] and math.isfinite(x) and x>=0 for x in v) and type(v[1]) is int and type(v[2]) is int
rows=[];gc=0
for cell,key in zip(data['cells'],expected):
 names=['context','type','n','rows','scope','density','shape','variant'];c.need(tuple(cell[k] for k in names)==key,'ordered exact matrix');c.need(cell['id']=='/'.join(map(str,[key[0],*key[2:]])),'cell id')
 raw=cell['windows'];c.need(len(raw)==18,'ninepairs');ratios=[];arm=cell['variant']
 for pair_id in range(1,10):
  pair=raw[2*pair_id-2:2*pair_id];c.need([w[1] for w in pair]==(['original',arm] if pair_id%2 else [arm,'original']),'alternation')
  c.need(all(len(w)==9 and type(w[0]) is int and w[0]==pair_id and type(w[8]) is int and validcost(w[2:8]) and w[6]==w[7]==0 for w in pair),'typed costs and compilezero')
  c.need(pair[0][8]==pair[1][8]==(2*cell['rows'] if cell['scope']=='rows' else 2*(cell['n']+cell['rows']) if cell['scope']=='reduced' else 1),'complete expected numerical path')
  by={w[1]:w for w in pair};c.need(by['original'][2]>0,'positive timer');ratios.append(by[arm][2]/by['original'][2]);gc+=sum(w[5]>0 for w in pair)
 r={k:cell[k] for k in names};median=statistics.median(ratios);r.update(paired_ratio=median,ratio_MAD=statistics.median(abs(v-median) for v in ratios),ratio_min=min(ratios),ratio_max=max(ratios))
 for source,dest in [('original','original'),(arm,'candidate')]:r[dest]={f:statistics.median(w[i+2] for w in raw if w[1]==source) for i,f in enumerate(fields[:3])}
 for offset,field in [(3,'bytes'),(4,'events')]:r['all_pairs_lower_'+field]=all(next(w[offset] for w in raw if w[0]==i and w[1]==arm)<next(w[offset] for w in raw if w[0]==i and w[1]=='original') for i in range(1,10))
 rows.append(r)
prep=data['preparation'];c.need(len(prep)==1813+38,'all preparation records');c.need([(v['context'],v['phase']) for v in prep if 'phase' in v]==[(label,phase) for label,t in contexts for phase in ['correctness_and_snapshots','context_GC']],'context preparation order')
c.need([v['cell'] for v in prep if 'phase' not in v]==[v['id'] for v in data['cells']],'cell preparation linkage')
for v in prep:
 if 'phase' in v:c.need(validcost(v['cost']),'context prep')
 else:
  c.need(validcost(v['fixture']) and validcost(v['validation_and_snapshots']),'fixture and snapshots')
  c.need(len(v['resets'])==18 and all(validcost(x) for x in v['resets']),'every measured reset cost')
  for k,count in [('cold',2),('warm',6)]:c.need(len(v[k])==count and all(len(x)==13 and validcost(x[:6]) and type(x[6]) is int and validcost(x[7:]) for x in v[k]),'cold/warm calls and reset costs')
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()];c.need(resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources),'all resources')
c.unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];c.put('audit-host.json',c.host(extra));c.put('summary.json',dict(cases=rows,measured_windows=len(rows)*18,GC_affected_windows=gc))
c.put('audit.json',dict(accepted=True,assertions=int(root_summary[1]),cells=len(rows),windows=len(rows)*18,GC_affected_windows=gc,elapsed_seconds=done['elapsed_shared_seconds'],min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),bindings={str(D/n):c.sha(D/n) for n in ['output/results.toml','output/run.log','output/process.json','pins.json','summary.json','audit.py']}))
print(json.dumps({k:v for k,v in c.read('audit.json').items() if k!='bindings'}))
