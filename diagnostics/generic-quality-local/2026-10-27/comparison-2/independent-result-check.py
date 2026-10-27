from pathlib import Path
import json,tomllib,math,hashlib,re,statistics,datetime,os,subprocess,itertools
Q=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27/comparison-2')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((Q/n).read_text())
proc=read('output/process.json');supervisor=read('supervisor.json');completed=read('completed.json');audit=read('audit.json');summary=read('summary.json');pins=read('pins.json');admission=read('admission.json');contract=read('contract.json')
assert proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True
assert supervisor['accepted'] is True and not supervisor['soft_timeout'] and not supervisor['hard_timeout'] and 'cleanup_error' not in supervisor
assert completed['accepted'] is True and completed['elapsed_shared_seconds']<=600 and audit['accepted'] is True
log=(Q/'output/run.log').read_text();match=re.search(r'^Local quality whole-function comparison\s*\|\s*(\d+)\s+(\d+)\s+',log,re.M);assert match and match[1]==match[2] and 'Test Failed' not in log and 'Error During Test' not in log and log.count('LOCAL_QUALITY_COMPARISON_COMPLETE cells=2172')==1
for n,v in admission['bindings'].items():assert sha(n)==v,n
for n,v in audit['bindings'].items():assert sha(n)==v,n
for n,v in pins['inventory'].items():assert str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],n
for tree in pins['trees']:assert {str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)}
for n,v in {**read('protected-before.json')['files'],**read('protected-before.json')['indexes']}.items():assert sha(n)==v
M=Path('/home/jspitz/JSimplex.jl');refs=subprocess.check_output(['/usr/bin/git','-C',str(M),'rev-parse','HEAD','master','origin/master'],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().splitlines();assert set(refs)=={'ca64312f7f74b1d7bec047718399f229674b3e1d'}
data=tomllib.loads((Q/'output/results.toml').read_text());contexts=[(f'BF{b}_RoundingMode{{:{m}}}()','BigFloat') for b in [64,128,256] for m in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']];keys=[]
for label,t in contexts:
 pats=['positive','negative','mixed','zero'] if t=='BigFloat' else ['mixed']
 keys.extend((label,t,n,s,d,p,0,a) for n,s,d,p,a in itertools.product([32,96],['quality','quality_transposed'],['sparse','dense'],pats,['A','B','AB']))
 if t in ['BigFloat','Float32','Float64']:keys.extend((label,t,n,'finish','vector',p,0,'B') for n,p in itertools.product([32,96],pats))
 keys.extend((label,t,n,'audit',d,p,m,'C') for n,m,d,p in itertools.product([32,96],[4,16],['sparse','dense'],pats))
assert len(keys)==len(data['cells'])==len(summary['cases'])==2172
fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']
def valid(v):assert all(type(v[f]) in [int,float] and math.isfinite(v[f]) and v[f]>=0 for f in fields)
computed=[];gcwindows=0;names=['context','type','n','scope','density','pattern','basis_rows','variant']
for cell,key,author in zip(data['cells'],keys,summary['cases']):
 assert tuple(cell[n] for n in names)==key
 ident='/'.join(str(v) for v in [key[0],key[2],*key[3:]]);assert cell['id']==ident
 assert len(cell['windows'])==18;byarm={};ratios=[]
 for k in range(1,10):
  pair=cell['windows'][2*k-2:2*k];assert [w['arm'] for w in pair]==(['original',key[-1]] if k%2 else [key[-1],'original'])
  for w in pair:
   valid(w);assert w['pair']==k and type(w['sink']) is int and w['compile_seconds']==w['recompile_seconds']==0
   assert cell['scope']!='audit' or w['sink']==1
   assert cell['scope'] not in ['quality','quality_transposed'] or w['sink']==4
   gcwindows+=int(w['gc_seconds']>0)
  assert pair[0]['sink']==pair[1]['sink'];lookup={w['arm']:w for w in pair};assert lookup['original']['seconds']>0;ratios.append(lookup[key[-1]]['seconds']/lookup['original']['seconds'])
 r={n:cell[n] for n in names};r['id']=ident;r['paired_ratio']=statistics.median(ratios);r['ratio_MAD']=statistics.median(abs(v-r['paired_ratio']) for v in ratios);r['ratio_min']=min(ratios);r['ratio_max']=max(ratios)
 for source,dest in [('original','original'),(key[-1],'candidate')]:r[dest]={f:statistics.median(w[f] for w in cell['windows'] if w['arm']==source) for f in ['seconds','bytes','events']}
 for f in ['bytes','events']:
  r['all_pairs_lower_'+f]=all(next(w[f] for w in cell['windows'] if w['pair']==k and w['arm']==key[-1])<next(w[f] for w in cell['windows'] if w['pair']==k and w['arm']=='original') for k in range(1,10))
 for n,v in author.items():assert r[n]==v,(ident,n,r.get(n),v)
 computed.append(r)
prep=data['preparation'];assert len(prep)==2210
assert [(v['context'],v['phase']) for v in prep if 'phase' in v]==[(label,p) for label,t in contexts for p in ['correctness_and_snapshots','context_GC']]
assert [v['cell'] for v in prep if 'phase' not in v]==[c['id'] for c in data['cells']]
for v in prep:
 if 'phase' in v:valid(v)
 else:
  valid(v['fixture']);valid(v['validation_and_snapshots'])
  for f,n in [('cold',2),('warm',6),('resets',18)]:
   assert len(v[f])==n
   for w in v[f]:valid(w)
assert gcwindows==summary['GC_affected_windows']==audit['GC_affected_windows'];assert audit['assertions']==int(match[1]) and audit['cells']==2172 and audit['windows']==39096
resources=[json.loads(v) for v in (Q/'output/resources.jsonl').read_text().splitlines()];assert resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources)
h=read('host-seed.json');groups=set(h['groups'])|{proc[k][v] for k in ['runner','child'] for v in ['pgid','sid']};assert len(groups)==589;assert h['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();processes=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();assert int(st[2]) not in groups and int(st[3]) not in groups;assert not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]);processes.append(dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd))
 except (FileNotFoundError,ProcessLookupError):pass
aggregates=[]
for typ,arm,scope,pattern in itertools.product(['BigFloat','Float32','Float64','Rational{BigInt}','Rational{Int64}'],['A','B','AB','C'],['quality','quality_transposed','finish','audit'],['positive','negative','mixed','zero']):
 rows=[r for r in computed if (r['type'],r['variant'],r['scope'],r['pattern'])==(typ,arm,scope,pattern)]
 if not rows:continue
 ratios=[r['paired_ratio'] for r in rows];agg=dict(type=typ,arm=arm,scope=scope,pattern=pattern,cells=len(rows),ratio_median=statistics.median(ratios),ratio_min=min(ratios),ratio_max=max(ratios),cells_ratio_below_one=sum(r<1 for r in ratios),all_pairs_lower_bytes=sum(r['all_pairs_lower_bytes'] for r in rows),all_pairs_lower_events=sum(r['all_pairs_lower_events'] for r in rows),median_bytes_saved=statistics.median(r['original']['bytes']-r['candidate']['bytes'] for r in rows),median_events_saved=statistics.median(r['original']['events']-r['candidate']['events'] for r in rows));aggregates.append(agg)
representatives=[r for r in computed if r['context']=='BF128_RoundingMode{:Nearest}()' and r['n']==96 and (r['scope']=='quality' and r['density']=='sparse' and r['pattern'] in ['negative','positive','mixed','zero'] or r['scope']=='finish' and r['pattern']=='mixed' or r['scope']=='audit' and r['density']=='sparse' and r['basis_rows']==16 and r['pattern']=='mixed')]
evidence=dict(accepted=True,findings=[],assertions=int(match[1]),cells=2172,windows=39096,preparation_records=2210,GC_affected_windows=gcwindows,inventory_files_verified=len(pins['inventory']),admission_bindings_verified=len(admission['bindings']),groups=sorted(groups),fresh_no_Julia=True,fresh_processes=processes,boot_id=h['boot_id'],elapsed_seconds=completed['elapsed_shared_seconds'],child_maxrss_kib=proc['child_maxrss_kib'],min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),aggregates=aggregates,representatives=representatives,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checker_sha256=sha(__file__),bindings={str(Q/n):sha(Q/n) for n in ['output/results.toml','output/run.log','output/process.json','output/resources.jsonl','supervisor.json','completed.json','audit.json','summary.json','pins.json','admission.json','audit.py']})
with Path('/tmp/local-quality-comparison2-result-evidence.json').open('x') as f:json.dump(evidence,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in evidence.items() if k not in ['groups','fresh_processes','bindings','aggregates','representatives']}))
for a in aggregates:print(json.dumps(a))
print('REPRESENTATIVES')
for r in representatives:print(json.dumps(r))
