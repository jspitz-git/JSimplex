"""Independent offline byte/AST review. Never imports or executes reviewed programs."""
from pathlib import Path
import ast,hashlib,json,re,struct,subprocess,tomllib
from fractions import Fraction
E=Path(__file__).resolve().parent
R=E.parents[3]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def bound_path(n):return Path(n) if Path(n).is_absolute() else R/n
pins=rd(E/'preparation-pins.json')
ck('1826_exact_pins',len(pins['sha256'])==1826 and set(pins['sha256'])==set(rd(E/'required-paths.json')['paths']))
ck('all_1826_sha256',all(sha(bound_path(n))==h for n,h in pins['sha256'].items()))
ck('entry_head',git('rev-parse','HEAD')=='0601df628f30ee3f226066d5ace9ab16928193aa')
ck('master',git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
ck('no_tracked_diff',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
ck('no_runs',not (E/'runs').exists())
inv=rd(E/'source-inverse.json');names=rd(E/'probe-renames.json')
for filename,meta in inv['probe'].items():
 s=(E/filename).read_text()
 if 'prefix' in meta:
  ck('prefix_'+filename,s.startswith(meta['prefix']));s=s[len(meta['prefix']):]
  for anchor,extra in meta['insertions']:
   ck('one_counter_'+str(len(checks)),s.count(extra)==1);s=s.replace(extra,'')
 original=Path(meta['original']).read_text()
 for a in sorted(names,key=len,reverse=True):original=re.sub(r'(?<![\w])'+re.escape(a)+r'(?![\w!])',names[a],original)
 ck('exact_renamed_inverse_'+filename,s==original)
ck('all_original_bindings',all(sha(p)==h for p,h in inv['originals'].items()))
stage=rd(E/'stages.json')['cost'];S=Path(stage['path']);G=Path(inv['stage_source'])
ck('83_stage_files',len(stage['sha256'])==83 and {str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}==set(stage['sha256']))
ck('stage_hashes',all(sha(S/n)==h for n,h in stage['sha256'].items()))
old={str(p.relative_to(G)):p for p in G.rglob('*') if p.is_file()}
ck('81_green_files',len(old)==81)
ck('only_root_and_two_new_sources',set(stage['sha256'])-set(old)=={'src/probe-slots.jl','src/probe-bg.jl'} and all((S/n).read_bytes()==p.read_bytes() for n,p in old.items() if n!='src/JSimplex.jl'))
ck('root_exact_inverse',(S/'src/JSimplex.jl').read_text().replace(inv['stage_addition'],'')==(G/'src/JSimplex.jl').read_text())
ck('probe_stage_equal',all((S/'src'/n).read_bytes()==(E/n).read_bytes() for n in ['probe-slots.jl','probe-bg.jl']))
ck('oracle_exact_inverse',(E/'probe-oracles.jl').read_text()==Path(inv['oracles_original']).read_text().replace('using Test\n','').replace('::J.BGSlotUpper','::Union{J.BGSlotUpper,J.ProbeBGSlotUpper}'))
ck('input_formats',rd(E/'inputs.json')==tomllib.loads((E/'inputs.toml').read_text()))
ck('old_input_tokens_exact',all((E/n).read_bytes()==(E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'/n).read_bytes() for n in ['inputs.json','inputs.toml']))
cost=(E/'cost.jl').read_text();body=cost.split('function lifecycle',1)[1].split('# No extra factor solves',1)[0]
ck('top_level_definitions',cost.index('include("probe-oracles.jl")')<cost.index('include("probe.jl")')<cost.index('function main()'))
ck('timed_no_probe_or_full_scan',not any(x in body for x in ['Probe','_probe','summarysize','_check_bg','_bg_probe_counts']))
ck('original_factories','J._dynamic_bg_factor(B,backend,policy(backend))' in cost and 'J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)' in cost)
ledger=rd(E/'work-ledger.json');t=ledger['timed'];c=ledger['controls'];p=ledger['probe'];total=ledger['total']
ck('timed_counts',all(t[k]==v for k,v in dict(windows=160,warm=48,measured=112,constructors=160,refactors=320,updates=1280,ftran=2560,btran=1280,copies=0).items()))
ck('untimed_counts',c==dict(constructors=16,refactors=32,exports=48,explicit_solves=0) and all(p[k]==v for k,v in dict(constructors=24,refactors=48,updates=192,ftran=384,btran=192,copies=0,checkpoints=88,output_vectors=576).items()))
ck('600_entries',total['backend_factorization_entries']==total['exports']==t['constructors']+t['refactors']+c['constructors']+c['refactors']+p['constructors']+p['refactors']==600 and total['native_orientation_solve_upper_bound']==300)
ck('exact_residual_counts',ledger['exact_residuals']==dict(timed=3840,probe=576))
for n,want in [('offline-tests.json',91),('prefix-tests.json',23),('source-check.json',16),('author-check.json',10)]:
 j=rd(E/n);ck('saved_'+n,j['all_passed'] is True and len(j['checks'])==want and all(j['checks'].values()))
# Inspect all Python syntax without importing/evaluating any reviewed module.
for p in E.glob('*.py'):ast.parse(p.read_text())
ck('python_ast_parse',True)
maps=rd(E/'author-check.json')['maps'];ck('six_mappings',len(maps)==6)
for i,m in enumerate(maps):
 j=rd(m['record']);ck('map_'+str(i),j[m['field']][m['key']]==m['value'] and (sha(m['preserved']) if m['field']=='sha256' else git('hash-object','--',m['preserved']))==m['value'])
# A static counterexample: the ONLY cross-window bitwise comparison is guarded
# by cell completion. Timeout prefixes deliberately omit that completion file.
tree=ast.parse((E/'evidence.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='output_checks')
parents={child:node for node in ast.walk(fn) for child in ast.iter_child_nodes(node)}
comparisons=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='Direct bitwise paired outputs/modes' for x in n.args)]
ck('single_pair_check',len(comparisons)==1)
n=comparisons[0];ancestors=[]
while n in parents:
 n=parents[n]
 if isinstance(n,ast.If):ancestors.append(ast.unparse(n.test))
ck('pair_check_only_under_completed_cell','end in names' in ancestors)
positive=struct.pack('>d',0.0).hex();negative=struct.pack('>d',-0.0).hex()
ck('signed_zero_counterexample',positive!=negative and Fraction(struct.unpack('>d',bytes.fromhex(positive))[0])==Fraction(struct.unpack('>d',bytes.fromhex(negative))[0])==0)
predecessor=next(n for n in ast.parse((E/'control.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='predecessor')
ck('second_process_no_cost_gate',not any(x in ast.unparse(predecessor) for x in ['time_median_gate','allocation_gate','memory_gate','statistics']))
proof=dict(all_checks_passed=True,checks=checks,pins_sha256=sha(E/'preparation-pins.json'),pin_count=1826,scope='Independent read-only SHA/AST/text checks only; no existing program imported or executed; no Julia',findings_proof=dict(timeout_pair_guard=ancestors,signed_zero_tokens=[positive,negative],valid_prefix_files=['started-1.toml','preflight-1.toml','probe-1.toml','window-1-1.toml','window-1-2.toml'],missing_completion='cell-1.toml',consequence='Valid exact-residual signed-zero discrepancy in completed pair is not compared in partial=True timeout admission',second_process_gate='Only all_passed and pure_timeout; no performance eligibility predicate'))
with (E/'independent-review-proof-v1.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print('Independent checks',len(checks),'PASS; all1826pins verified; two review concerns preserved; NO JULIA')
