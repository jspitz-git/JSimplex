"""Fresh offline source inverses and refusal predicates; no Julia/cost execution."""
from pathlib import Path
import sys,json,copy,tempfile
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
from clone_source import clone_sources
import evidence as e
from analysis import first_process_viable,qualify,summarize
checks={}
def ck(v,n):checks[n]=bool(v)
def refuses(fn):
 try:fn();return False
 except (RuntimeError,ValueError,KeyError,TypeError):return True
clones,edits,header=clone_sources(c.C);inv=c.rd(D/'probe-inverse.json');stage=Path(c.rd(D/'stages.json')['cost']['path']);seed=Path(inv['seed'])
for name,s in clones.items():ck((D/('probe-'+name+'.jl')).read_text()==s==(stage/'src'/('_bgxsp_'+name+'.jl')).read_text(),'clone_inverse_'+name)
ck(inv['edits']==edits and inv['header']==header,'instrumentation_inventory')
ck((stage/'src/JSimplex.jl').read_text().replace(inv['stage_addition'],'')==(seed/'src/JSimplex.jl').read_text(),'root_only_four_probe_includes')
for p in seed.rglob('*'):
 if p.is_file() and p!=seed/'src/JSimplex.jl':ck(p.read_bytes()==(stage/p.relative_to(seed)).read_bytes(),'seed_'+str(p.relative_to(seed)))
ck(len(c.rd(D/'stages.json')['cost']['sha256'])==87,'exact87_stage')
for n,v in c.rd(D/'reused-files.json').items():ck(c.sha(D/n)==c.sha(v['path'])==v['sha256'],'byte_exact_'+n)
ck(c.rd(D/'inputs.json')==e.tomllib.loads((D/'inputs.toml').read_text()),'json_toml_exact_inputs')
ck([f['name'] for f in c.rd(D/'inputs.json')['fixtures']]==['sparse32','dense32','sparse96','dense96'],'four_original_fixtures')
text=(D/'cost.jl').read_text();ck('factory(::Val{:candidate},F,B,backend) = J._bgxs_factor(B,backend,policy(backend))' in text and '_bgxsp_' not in text,'timed_uninstrumented_candidate')
ck(text.index('include("probe.jl")')<text.index('function main()') and 'for pair in 1:10' in text and '"measured"=>pair>3' in text,'top_level_and_pair_schedule')
ck('k==4' in text and 'k==8' in text and 'timed=@timed lifecycle' in text and 'retained=Base.summarysize(factor)' in text,'whole_lifecycle_graph_outside')
ck('st[\'memory_gate\']=st[\'memory_gate\'] and memory and all(' in (D/'evidence.py').read_text(),'both_process_probe_memory_gate')
c.validate_environment();c.validate_sources();files,groups=c.predecessor('cost1-300');ck(len(groups)==265 and bool(files),'accepted_specialized_GREEN_predecessor')
for phase in ('cost1-300','cost2-300','cost1-600','cost2-600'):ck(c.config(phase)['seconds'] in (300,600) and c.config(phase)['command'][-3]==phase,'command_'+phase)
for phase in ('green2-300','cost1','cost3-300'):ck(refuses(lambda:c.config(phase)),'phase_rejection_'+phase)
ck(refuses(lambda:c.predecessor('cost2-300')),'no_second_without_first_result')
# Exact scalar statistics selection tests, synthetic values, never measured data.
fixtures=c.rd(D/'inputs.json')['fixtures'];cells=[]
for f in fixtures:
 for b in ('native','markowitz'):
  cells.append(dict(fixture=f['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default',statistics=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,probe_memory_gate=True,faster_pairs=3)))
a=dict(all_passed=True,pure_timeout=False,cells=cells);ck(first_process_viable(a,fixtures),'synthetic_first_all8')
for key,value in [('time_median_gate',False),('allocation_gate',False),('memory_gate',False),('probe_memory_gate',False),('faster_pairs',2)]:
 v=copy.deepcopy(a);v['cells'][7]['statistics'][key]=value;ck(not first_process_viable(v,fixtures),'reject_one_cell_'+key)
for label,v in [('missing',dict(a,cells=cells[:-1])),('failed',dict(a,all_passed=False)),('timeout',dict(a,pure_timeout=True))]:ck(not first_process_viable(v,fixtures),'reject_'+label)
s=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,faster_pairs=5);ck(qualify(s,s) and not qualify(s,dict(s,faster_pairs=4)) and not qualify(s,dict(s,memory_gate=False)),'combined14_pair_gate')
valid=dict(present=True,dimension=64,charge=520,limit=600,seen_bytes=8,orientation_bytes=0,graph_bytes=600);e.cache(valid);ck(True,'synthetic_cache_valid')
for name,delta in [('over_budget',dict(limit=519)),('bad_dimension',dict(dimension=65)),('bad_charge',dict(charge=521)),('bad_present',dict(present=1)),('negative',dict(graph_bytes=-1))]:
 ck(refuses(lambda:e.cache(dict(valid,**delta))),'cache_reject_'+name)
with tempfile.TemporaryDirectory(prefix='bgx-cost-prefix-') as tmp:
 t=Path(tmp);out=t/'runs/cost1-300/output';out.mkdir(parents=True)
 for name in ('inputs.json','loaded-paths.json'):(t/name).write_bytes((D/name).read_bytes())
 for name in ('pins.json','current.json','process.json','resources.jsonl','run.log'):(out/name).write_text('')
 ck(e.output_checks(out,c.config('cost1-300'),partial=True)[1]['windows']==0,'synthetic_empty_valid_prefix')
 (out/'window-1-1.toml').write_text('');ck(refuses(lambda:e.output_checks(out,c.config('cost1-300'),partial=True)),'reject_orphan_window')
for p in D.glob('*.py'):compile(p.read_text(),str(p),'exec')
ck(True,'Python_syntax_only');ck(not (D/'runs').exists(),'no_seal_or_launch')
paths=sorted(p for p in D.iterdir() if p.is_file());v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):c.sha(p) for p in paths},scope='New offline inverse/source/synthetic admission predicates only, not numerical or cost evidence')
c.save(D/'source-check.json',v);print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),failed=[n for n,b in checks.items() if not b])));c.require(v['all_passed'],'Preserve offline failure')
