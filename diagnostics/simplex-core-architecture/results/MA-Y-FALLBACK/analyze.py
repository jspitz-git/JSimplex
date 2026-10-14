"""New stored-data/source analysis only. Exclusive output; never imports old scripts."""
from pathlib import Path
import hashlib,json,tomllib,statistics as S
R=Path.cwd();B=R/'diagnostics/simplex-core-architecture';D=B/'results/MA-Y-FALLBACK';X=B/'results/MA-X'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
checks={};files={Path(__file__).resolve(),X/'pins.json',X/'driver.jl',X/'audit.py',B/'results/MA-R/reference.jl',B/'results/MA-R/tests.jl',B/'results/MA-R/fixtures.toml',B/'results/MA-U/candidate.jl',B/'results/MA-Y/publication.json',B/'results/MA-S-FALLBACK/analysis.json'}
pins=rd(X/'pins.json')['inventory'];pub=rd(B/'results/MA-Y/publication.json')['sha256'];spec=tomllib.loads((B/'results/MA-R/fixtures.toml').read_text())['cost_cases']
metrics=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','calls','order','side','pair','phase']
pairs=[];cases=[];checks['exact_spec_52_controls16']=len(spec)==52 and sum(not c['eligible'] for c in spec)==16
for index in (1,2,3):
 rawpath=X/f'run-{index}/raw.toml';journalpath=X/f'run-{index}/partial-windows.toml';auditpath=X/f'audit-{index}.json';files.update([rawpath,journalpath,auditpath,X/f'run-{index}/resources.jsonl',X/f'run-{index}/process.json'])
 raw=tomllib.loads(rawpath.read_text());journal=tomllib.loads(journalpath.read_text())['records'];audit=rd(auditpath)
 require([c['id'] for c in raw['costs']]==[c['id'] for c in spec],'case order')
 j={(r['kind'],r['location']):r['window'] for r in journal};require(len(j)==2080,'unique journal')
 for ci,(c,fixture) in enumerate(zip(raw['costs'],spec),1):
  if fixture['eligible']:continue
  ws=c['windows'];require(len(ws)==20,'windows')
  for pair in range(1,11):
   w={v['side']:v for v in ws if v['pair']==pair};require(set(w)=={'reference','candidate'},'pair')
   r,t=w['reference'],w['candidate']
   for side,v in w.items():
    location=f"cost/{c['id']}/{pair}/{1 if side=='reference' else 2}"
    require(j['whole-complete',location]==v,'journal complete equality')
    require(j['whole-metrics',location]=={k:val for k,val in v.items() if k not in ('output','preserved')},'journal metrics equality')
    require(v['preserved'] is True and v['output']==c['expected'],'preservation/output')
    require(v['calls']==4 and v['phase']==('warm' if pair<=3 else 'measured'),'window labels')
    require(v['order']==(1 if (index+ci+pair)%2==0 else 2) if side=='reference' else v['order']==(2 if (index+ci+pair)%2==0 else 1),'side order')
    if pair>3:require(v['compile_seconds']==v['recompile_seconds']==0,'compile zero')
   pairs.append(dict(process=index,id=c['id'],case_index=ci,pair=pair,phase=r['phase'],order='RC' if r['order']==1 else 'CR',reference={k:r[k] for k in metrics},candidate={k:t[k] for k in metrics},byte_delta=t['bytes']-r['bytes'],event_delta=t['events']-r['events'],time_delta_us=(t['seconds']-r['seconds'])*1e6/4,paired_ratio=t['seconds']/r['seconds'],outputs_equal_preserved=True))
  measured=[p for p in pairs if p['process']==index and p['id']==c['id'] and p['phase']=='measured'];sides={}
  for side in ('reference','candidate'):
   ranked=sorted(measured,key=lambda p:p[side]['seconds']);branked=sorted(measured,key=lambda p:p[side]['bytes'])
   sides[side]=dict(seconds_per_call=S.median(p[side]['seconds']/4 for p in measured),bytes=S.median(p[side]['bytes'] for p in measured),events=S.median(p[side]['events'] for p in measured),time_rank_pairs=[p['pair'] for p in ranked],time_median_pair=ranked[3]['pair'],byte_rank_pairs=[p['pair'] for p in branked],byte_median_pair=branked[3]['pair'])
  rt,ct=sides['reference']['seconds_per_call'],sides['candidate']['seconds_per_call']
  gates=dict(time=ct-rt<=max(.10*rt,.4e-6),bytes=sides['candidate']['bytes']<=sides['reference']['bytes'],events=sides['candidate']['events']<=sides['reference']['events'])
  original=next(row for row in audit['process_costs'] if row['id']==c['id'])
  require(original['pass']==all(gates.values()),'original gate')
  cases.append(dict(process=index,id=c['id'],sides=sides,paired_ratio_median=S.median(p['paired_ratio'] for p in measured),paired_byte_delta_median=S.median(p['byte_delta'] for p in measured),gates=gates,original_pass=original['pass'],time_allowance_seconds=max(.10*rt,.4e-6)))
 checks[f'process{index}_journal_and_controls']=True
measured=[p for p in pairs if p['phase']=='measured'];checks['480_pairs_336_measured']=len(pairs)==480 and len(measured)==336
summary={}
for name,predicate in [('scoped_BigFloat',lambda p:p['id'].startswith('fallback/BigFloat/')),('Rational',lambda p:'Rational{BigInt}' in p['id']),('Float64',lambda p:'Float64' in p['id']),('small_BigFloat',lambda p:not p['id'].startswith('fallback/'))]:
 rows=[p for p in measured if predicate(p)];delta=[p['byte_delta'] for p in rows]
 summary[name]=dict(pairs=len(rows),positive=sum(x>0 for x in delta),negative=sum(x<0 for x in delta),zero=sum(x==0 for x in delta),min_byte_delta=min(delta),max_byte_delta=max(delta),event_deltas=sorted(set(p['event_delta'] for p in rows)),orders={o:sum(p['order']==o for p in rows) for o in ('RC','CR')},gc_pairs=sum(p['reference']['gc_seconds']>0 or p['candidate']['gc_seconds']>0 for p in rows))
checks['scoped_no_added_bytes_events']=all(p['byte_delta']==p['event_delta']==0 for p in measured if p['id'].startswith('fallback/BigFloat/'))
checks['rational_equal_events_both_sign_bytes']=summary['Rational']['event_deltas']==[0] and summary['Rational']['positive']>0 and summary['Rational']['negative']>0
failures=[dict(process=c['process'],id=c['id'],gates=c['gates']) for c in cases if not all(c['gates'].values())]
checks['exact_two_original_failures']=failures==[dict(process=3,id='fallback/BigFloat/transpose',gates=dict(time=False,bytes=True,events=True)),dict(process=3,id='fallback/Rational{BigInt}/forward',gates=dict(time=True,bytes=False,events=True))]
checks['no_aggregate_file']=not (X/'aggregate.json').exists()
u=(B/'results/MA-U/candidate.jl').read_text();driver=(X/'driver.jl').read_text();ref=(B/'results/MA-R/reference.jl').read_text()
checks['source_rational_type_reject_first']='dest isa Vector{BigFloat} && rhs isa Vector{BigFloat} || return false' in u
checks['source_scoped_read_inline_no_MA_scratch_before_fallback']='Base.@inline Base.KeyValue.get(scope.values, key)' in u and 'return (only(v)::Base.MPFR.MPFRRoundingMode) == Base.MPFR.ROUNDING_MODE[]' in u and '_dense_ma_eligible(dest, backend, rhs) || return reference_forward!(dest, backend, rhs)\n    product = BigFloat()' in u and '_dense_ma_eligible(dest, backend, rhs) || return reference_transpose!(dest, backend, rhs)\n    product = BigFloat()' in u
checks['source_direct_ldiv']='ldiv!(destination, backend.factorization, rhs)' in ref and 'ldiv!(destination, transpose(backend.factorization), rhs)' in ref
checks['source_batch4_private_deepcopy_outside_timer']='for _ in 1:4' in driver and 't=@timed batch(f,x)' in driver and 'a,b=deepcopy(x),deepcopy(x)' in driver
checks['source_journal_after_window']='w=window(fs[side],y)' in driver and driver.index('w=window(fs[side],y)')<driver.index('journal_record(Dict("kind"=>"whole-metrics"')<driver.index('output=serialtokens(y.dest)')
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
for n in ('gmp.jl','timing.jl','mpfr.jl','dict.jl','hamt.jl','scopedvalues.jl'):files.add(base/n)
timing=(base/'timing.jl').read_text();gmp=(base/'gmp.jl').read_text()
checks['source_bytes_events_distinct']='gc_num.allocd + gc_num.deferred_alloc + gc_num.total_allocd' in timing and 'diff.malloc + diff.realloc + diff.poolalloc + diff.bigalloc' in timing
checks['source_GMP_fresh_owners_callbacks']='unsafe_rational(BigInt(), BigInt())' in gmp and 'jl_gc_counted_realloc_with_old_size' in gmp
old=rd(B/'results/MA-S-FALLBACK/analysis.json');nb=old['historical_native_binding'];files.add(Path(nb['binary']));files.add(Path(nb['source']));files.update(map(Path,nb['assemblies']))
original=rd(nb['source'])['sha256'];checks['saved_native_binary_matches_current_launch']=sha(nb['binary'])==nb['sha256']==pins[nb['binary']]['sha256']==original[nb['binary']]
checks['saved_native_asm_hashes']=all(sha(p)==original[p] for p in nb['assemblies'])
readtime={str(p):dict(sha256=sha(p),launch_pinned=str(p) in pins,resolved=str(p.resolve())) for p in sorted(files)}
checks['selected_launch_hashes_match']=all(v['sha256']==pins[p]['sha256'] and v['resolved']==pins[p]['resolved'] for p,v in readtime.items() if v['launch_pinned'])
checks['old_publication_paths_match']=all(sha(p)==h for p,h in pub.items())
require(all(checks.values()),str(checks))
obj=dict(all_passed=True,qualification_accepted=False,scope='Descriptive stored-data analysis of controls; no pooled qualification, filtering, new Julia or old script execution.',checks=checks,summaries=summary,case_medians=cases,paired_rows=pairs,original_failures=failures,readtime_pins=readtime,sha256={k:v['sha256'] for k,v in readtime.items()},historical_native_binding=nb)
with (D/'analysis.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),pins=len(readtime),summaries=summary,failures=failures),indent=2))
