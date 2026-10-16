"""New one-shot offline source binding check; no Julia parsing or execution."""
from control import *
import re
checks={}
def check(n,v):
 checks[n]=bool(v);require(v,n)
validate_environment();validate_sources();check('fresh_environment_baseline_stages_runtime',True)
check('no_phase_seal_reservation_or_output',not (D/'runs').exists())
check('master_and_diagnostic_entry',git('rev-parse','HEAD')==ENTRY and git('rev-parse','master')==MASTER)
check('no_tracked_or_staged_changes',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
check('entry_lineage_hashes',bindings(rd(D/'entry.json')))
for n,v in rd(D/'reused-helpers.json').items():check('copied_'+n,sha(D/n)==sha(Path(v['source']))==v['sha256'])
check('new_pure_offline_tests',rd(D/'offline-tests.json')['all_passed'] is True)
s=rd(D/'stages.json');red=Path(s['red']['path']);green=Path(s['green']['path'])
check('exact_stage_counts',len(s['red']['sha256'])==75 and len(s['green']['sha256'])==81)
for dst,src in [('src/slot-upper.jl','slot-upper-reviewed.jl'),('src/dynamic-bg.jl','dynamic-bg-reviewed.jl'),('test/slot-upper-tests.jl','slot-upper-tests-reviewed.jl'),('test/dynamic-bg-tests.jl','dynamic-bg-tests-reviewed.jl')]:check('frozen_'+src,(green/dst).read_bytes()==(C/src).read_bytes())
symbols=re.findall(r'@test isdefined\(JSimplex,:(\w+!?)\)',(D/'red.jl').read_text())
check('eight_contract_presence_tests',len(symbols)==len(set(symbols))==8)
redtext='\n'.join(p.read_text() for p in (red/'src').rglob('*.jl'));greentext='\n'.join(p.read_text() for p in (green/'src').rglob('*.jl'))
check('missing_new_symbols_in_red',all(re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',redtext) is None for n in symbols))
check('new_symbols_in_green',all(re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',greentext) for n in symbols))
driver=(D/'driver.jl').read_text()
check('invokelatest_at_each_include_boundary',all(n in driver for n in ['Base.invokelatest(run_dynamic_bg_red)','Base.invokelatest(DynamicBGSlotTests.run_slots)','Base.invokelatest(getfield(DynamicBGTests,name))']))
check('raw_before_aggregate_validation',driver.index('TOML.print(io,raw)')<driver.index('valid=raw["complete"]'))
check('no_cost_driver',not (D/'cost.jl').exists())
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-ADAPTER-PREPARATION'
live={R/'diagnostics/simplex-core-architecture/STATUS.md':D/'STATUS.md.before-Task3',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':D/'roadmap.md.before-Task3'}
maps=[]
for n in ['closure.json','closure-supplement.json','publication-final.json','publication-amendment-review.json']:
 j=rd(P/n)
 for old,h in j['sha256'].items():
  actual=path(old);new=live.get(actual,actual);require(sha(new)==h,'Prior binding '+n+' '+old)
  if actual in live:
   require(sha(actual)==h,'Continuation changed early');maps.append(dict(record=str(P/n),field='sha256',key=old,sha256=h,preserved=str(new)))
 for old,b in j.get('git_blobs',{}).items():
  actual=path(old);new=live.get(actual,actual);require(git('hash-object','--',str(new))==b,'Prior blob '+old)
  if actual in live:maps.append(dict(record=str(P/n),field='git_blobs',key=old,git_blob=b,preserved=str(new)))
check('all_prior_current_continuation_bindings',len(maps)==10)
save(D/'continuation-map.json',dict(scope='Only Task2 current continuation bindings map here; all older mappings unchanged',maps=maps))
files=[D/'source-check.py',D/'continuation-map.json',D/'driver.jl',D/'red.jl',D/'slot-suite.jl',D/'expected-tests.json',D/'expected-tests.toml',D/'work-ledger.json',D/'REPORT.md',D/'ADMISSION.md']
save(D/'source-check.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in files}))
print('Task3 source checks PASS',len(checks),'continuation mappings',len(maps))
