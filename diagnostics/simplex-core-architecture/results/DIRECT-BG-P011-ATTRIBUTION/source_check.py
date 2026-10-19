"""One-shot source/saved-result analysis. No Julia, parser, compiler or old auditor."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-HARNESS');run=D/'runs/p011-300'
B=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
P=R/'diagnostics/direct-bg-blocked-update/reproduce/panel.jl';F=E.with_name('DIRECT-BG-P011-DIAGNOSTIC')/'driver.jl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
s=P.read_text();n=(B/'ntuple.jl').read_text();b=(B/'boot.jl').read_text();t=(B/'timing.jl').read_text();f=F.read_text();a=rd(run/'audit.json');v=a['result'];checks={}
checks['saved_diagnostic_pass']=a['all_passed'] is True and rd(run/'result-review.json')['accepted'] is True
checks['residual_four_pairs']=v['descriptive_sample_counters']['concrete']['inner_bytes']==[400]*4 and v['descriptive_sample_counters']['concrete']['inner_events']==[3]*4
checks['all_consumed_same']=all(x['consumed_result']['bytes']==400 and x['consumed_result']['events']==3 for x in v['records'])
checks['samples_compile_recompile_gc_zero']=all(x[k][m]==0 for x in v['records'] if x['phase']=='sample' for k in ['bytes_wrapper','events_wrapper','consumed_result'] for m in ['compile_seconds','recompile_seconds','gc_seconds'])
checks['dimension_return_before_scans']='n=length(inner.upper);d=_bgb_dimensions(n,r)\n    d.accepted || return d' in s
checks['dimension_builds_dynamic_twenty']='BGPanelDecision(r,b,ok,ok ? :eligible : :dimensions,true,ntuple(_->0,20))' in s
checks['three_candidate_zero_constructors']=len(re.findall(r'ntuple\(_\s*->\s*0,\s*20\)',s))==3
checks['base_integer_threshold_ten']='n == 10 ?' in n and '_ntuple(f, n)' in n
checks['base_noinline_array_splat']='function _ntuple(f::F, n::Int) where F\n    @noinline' in n and '([f(i) for i = 1:n]...,)' in n
checks['base_static_val_alternative']='@inline function ntuple(f::F, ::Val{N}) where {F,N}' in n and ':(@ntuple $N i -> f(i))' in n
checks['array_separate_memory']='mem = fieldtype(fieldtype(self, :ref), :mem)(undef, m)' in b and 'Expr(:new, :self, :(memoryref(mem)), :((m,))' in b
checks['unchanged_concrete_body']='function concrete_call(f::Carrier)::Decision\n    K._bgb_eligibility(f,1)' in f
checks['measurement_noinline']='@noinline f(args...)' in t and 'Base.gc_bytes(b0)' in t
checks['sink_preexisting']='sink = Ref(Decision(' in f and 'sink[] = concrete_call(f)' in f
paths=[P,F,*[B/x for x in ['ntuple.jl','boot.jl','array.jl','timing.jl','refvalue.jl']],run/'audit.json',run/'result-review.json',E.with_name('DIRECT-BG-P011-RESULT')/'REPORT.md',E.with_name('DIRECT-BG-P011-RESULT')/'review.md',R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl',Path(__file__).resolve()]
paths+=sorted((run/'payload').iterdir())
pins=rd(run/'launch-pins.json')['inventory'];comparability={str(p):{'current_sha256':sha(p),'launch_entry':pins.get(str(p))} for p in paths if p in [P,F,*[B/x for x in ['ntuple.jl','boot.jl','array.jl','timing.jl','refvalue.jl']]]}
# Inventory entries are structured; compare using their actual SHA field.
checks['sources_launch_match']=all(x['launch_entry'] is not None and x['launch_entry']['sha256']==x['current_sha256'] for x in comparability.values())
result={'all_passed':all(checks.values()),'checks':checks,'sha256':{str(p):sha(p) for p in paths},'comparability':comparability,'scope':'Literal source and saved JSON checks only. No runtime allocation-site attribution or size accounting.'}
with (E/'source-check.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':checks,'hashes':len(paths)}))
if not result['all_passed']:raise SystemExit(1)
