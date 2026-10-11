"""Audit a finished guarded whole-pipeline comparison; emit all group summaries."""
from pathlib import Path
import collections,json,statistics,sys,tomllib
assert len(sys.argv)==3, "Expected preserved partial cost-2 and completed remaining attempt"
raws=list(map(Path,sys.argv[1:]))
datasets=[]
for index,raw in enumerate(raws):
 process=json.loads((raw/'process.json').read_text())
 assert process['returncode']==(1 if index==0 else 0) and process['pins_unchanged']
 data=tomllib.loads((raw/'cost.toml').read_text())
 assert tuple(len(data[k]) for k in ('samples','warmups','setups'))==((828,276,23) if index==0 else (108,36,3))
 if index==0:
  log=(raw/'run.log').read_text()
  assert 'AssertionError: isnothing(JS._primal_iteration!' in log and 'fixture(T::Type{Float32}' in log
 datasets.append(data)
assert len({d['pipeline_source_hash'] for d in datasets})==1
assert len({d['baseline_helper_hash'] for d in datasets})==1
data=datasets[0].copy()
for key in ('samples','warmups','setups'):data[key]=sum((d[key] for d in datasets),[])
expected={("Float64",m,"native",kind,history) for m in ('pfi','huangfu_hall','forrest_tomlin','suhl_suhl','bartels_golub') for kind in ('sparse','dense') for history in (0,8)}
expected|={("Float32",m,"markowitz",kind,history) for m in ('pfi','huangfu_hall') for kind in ('sparse','dense') for history in (0,8) if not(kind=='dense' and history==8)}
fixture_fields=('type','manager','backend','matrix','history')
assert len(data['setups'])==26 and {tuple(x[k] for k in fixture_fields) for x in data['setups']}==expected
fields=('type','manager','backend','matrix','history','operation','mode')
groups=collections.defaultdict(list)
for row in data['samples']:groups[tuple(row[k] for k in fields)].append(row)
assert len(groups)==156
assert set(groups)=={f+(op,mode) for f in expected for op in ("ftran","btran","pricing") for mode in ("sparse","dense")}
summaries=[]
for key,rows in groups.items():
 assert len(rows)==6
 assert all(x['compile_seconds']==0 for x in rows)
 assert len({x['output_hash'] for x in rows})==1
 assert len({x['actual_mode'] for x in rows})==1
 sides={v:[x for x in rows if x['variant']==v] for v in ('control','candidate')}
 for side in sides.values():assert sorted(x['pair'] for x in side)==[1,2,3]
 medians={v:statistics.median(x['seconds'] for x in side) for v,side in sides.items()}
 summaries.append(dict(zip(fields,key))|{'actual_mode':rows[0]['actual_mode'],
  'ratio_of_medians':medians['candidate']/medians['control'],'median_seconds':medians,
  'paired_ratios':[next(x for x in sides['candidate'] if x['pair']==i)['seconds']/next(x for x in sides['control'] if x['pair']==i)['seconds'] for i in (1,2,3)],
  'bytes':{v:[x['bytes'] for x in side] for v,side in sides.items()},
  'allocations':{v:[x['allocations'] for x in side] for v,side in sides.items()}})
print(json.dumps({'groups':summaries,'samples':len(data['samples']),'warmups':len(data['warmups']),
 'coverage':'26 of 28 fixtures; Float32/Markowitz dense/history8 PFI and HH fail identically before timing; preserved partial exit1 plus targeted exit0 follow-up',
 'source_sha256':data['pipeline_source_hash'],'baseline_sha256':data['baseline_helper_hash']},indent=2))
