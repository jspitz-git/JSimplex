from pathlib import Path
import json,hashlib,re,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-S';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.loads((E/'source-contract.json').read_text());m=json.loads((E/'manifest.json').read_text());checks={}
checks['full586_rehash']=len(a['sha256'])==586 and all(sha(p)==v for p,v in a['sha256'].items())
checks['28_recorded_checks_pass']=len(a['checks'])==28 and all(a['checks'].values()) and a['all_passed']
root=(R/'src/JSimplex.jl').read_text()
for name in ['LinearAlgebra','Logging','SparseArrays']:root=root.replace('using '+name+'\n','const '+name+' = Main.JSimplex.'+name+'\nusing .'+name+'\n')
root=root.replace('import OrderedCollections\n','const OrderedCollections = Main.JSimplex.OrderedCollections\n').replace('using PrecompileTools: @setup_workload, @compile_workload\n','# S4-S: no PrecompileTools import in the isolated solver core.\n').replace('include("moi.jl")\n','# S4-S: MOI integration excluded from isolated public solve scope.\n').replace('include("precompile.jl")\n','# S4-S: package precompile workload excluded, not suppressed by mutable state.\n')
checks['independent_root_forward_transform']=root==(E/'isolated-root.txt').read_text()
order=[]
def visit(path,body=None):
 order.append(path)
 for line in (body if body is not None else (R/path).read_text()).splitlines():
  if line.startswith('include("'):visit(str(Path(path).parent/line.split('"')[1]))
visit('src/JSimplex.jl',root)
checks['independent64_include_order']=len(order)==64 and order==m['selected_load_order']
checks['128_entries_follow_order']=all([x['relative_source'] for x in m['entries'] if x['side']==side]==order for side in ['reference','candidate']) and len(m['entries'])==128
alltext='\n'.join((R/p).read_text() for p in order);owners={x['owner'] for x in m['external_methods'] if x['selected']}
checks['nine_owners_are_local_structs']=len(owners)==9 and all(re.search(r'\bstruct\s+'+re.escape(name)+r'\b',alltext) for name in owners)
checks['all62_complete_owned_signatures']=len(m['external_methods'])==62 and all(re.search(r'\b'+re.escape(x['owner'])+r'\b',x['signature']) for x in m['external_methods'])
checks['original_solver_per_side_unchanged']=all(x['source_sha256']==x['proposed_sha256']==sha(R/'src/solver.jl') for x in m['entries'] if x['relative_source']=='src/solver.jl')
checks['source_test_CI_same']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['Q_raw_sha_unchanged']=sha(D/'results/S4-Q/cost-1-report.toml')=='d33e04007dd9c3f7afee9983b9dce845d9b1115545ef4c66a422c2a1ec1f6387'
obj=dict(checks=checks,all_passed=all(checks.values()),scope='Separate author full586 hash verification and independently reconstructed root/include order; not runtime module proof')
with (E/'independent.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(obj));assert obj['all_passed']
