"""Independent review: hashes, text membership and integer ledger arithmetic only."""
from pathlib import Path
import hashlib,json,re,tomllib
R=Path(__file__).resolve().parents[4]
E=Path(__file__).resolve().parent
C=R/'diagnostics/direct-bg-block-upper/reproduce'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
manifest=json.loads((C/'source-bindings-reviewed.json').read_text());stage=Path(manifest['path']);base=Path(manifest['source'])
checks['identical_final_manifests']=(C/'source-bindings-reviewed.json').read_bytes()==(E/'overlay-reviewed.json').read_bytes()
checks['exact_stage_membership']=set(manifest['sha256'])=={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
checks['all78_stage_hashes']=len(manifest['sha256'])==78 and all(H(stage/p)==h for p,h in manifest['sha256'].items())
checks['all75_baseline_hashes']=len(manifest['baseline'])==75 and all(H(base/p)==h for p,h in manifest['baseline'].items())
addition=b'\n'+manifest['root_addition'].encode()+b'\nend\n';root=(stage/'src/JSimplex.jl').read_bytes()
checks['exact_root_inverse']=root.count(addition)==1 and root.replace(addition,b'\nend\n')==(base/'src/JSimplex.jl').read_bytes()
checks['unchanged74_files']=all((stage/p).read_bytes()==(base/p).read_bytes() for p in manifest['baseline'] if p!='src/JSimplex.jl')
checks['three_candidate_copies']=all((stage/d).read_bytes()==(C/s).read_bytes() for d,s in [('src/block-upper.jl','block-upper.jl'),('test/block-oracles.jl','block-oracles.jl'),('test/block-upper-tests.jl','block-upper-tests.jl')])
source=(C/'block-upper.jl').read_text();fields=re.findall(r'^    (\w+)::([^\n]+)',source.split('\nend',1)[0],re.M)
checks['23_vector_4_int_fields']=len(fields)==27 and sum(t.startswith('Vector') for _,t in fields)==23 and sum(t=='Int' for _,t in fields)==4
budget=json.loads((E/'budget-final.json').read_text());recomputed=[]
for case in range(1,9):
    raw=tomllib.loads((E.parent/f'DIRECT-BG-DYNAMIC-COST-PREPARATION/runs/cost1-300/output/probe-{case}.toml').read_text())
    n=32 if case<=4 else 96;dense=case in [3,4,7,8];m=raw['states'][0]['live']
    k0=sum((j+31)//32 for j in range(1,n+1)) if dense else n
    graph=lambda c,r,k:16*c+4*r+28*k+32*n+656+8*n+24+40*(n+26)+216
    checks[f'case{case}_initial_graph']=budget['initial'][case-1]['modeled_U_graph_min']==graph(m,m,k0)
    seed=m;seedk=k0
    for i,s in enumerate(raw['states']):
        live=s['live']
        if s['refactored']:seed=live;seedk=k0 if dense and live==m else max(n,(live+31)//32)
        c=seed+max(0,(live-seed+255)//256)*256;r=max(seed,live);k=max(seedk,n,(live+31)//32)
        x=s['graphs'][1]-s['arena_graph_bytes']+graph(c,r,k)
        item=budget['checkpoint_lower_bounds'][(case-1)*11+i]
        recomputed.append(x==item['modeled_factor_lower'] and (10*x>11*s['graphs'][0])==item['lower_exceeds'])
checks['all88_conditional_lower_arithmetic']=len(recomputed)==88 and all(recomputed)
checks['false_original_retained']=json.loads((E/'budget.json').read_text())['all_passed'] is False
checks['final_budget_no_proven_failure']=budget['all_passed'] and not any(x['lower_exceeds'] for x in budget['checkpoint_lower_bounds'])
checks['14_named_testsets']=len(re.findall(r'@testset "', (C/'block-upper-tests.jl').read_text()))==14
checks['gap_suffix_proof_precondition']='Int(U.gap_length[r])>0 && return nothing' in source and 'for k in rank:d\n        p=k+gap;_bgu_back!' in source
files=[C/f for f in ['block-upper.jl','block-oracles.jl','block-upper-tests.jl','source-bindings-reviewed.json']]+[E/f for f in ['MEMORY-WORK.md','budget-final.py','budget-final.json','budget.json','overlay-reviewed.json','source-check.json','reserve-fix.json']]+[Path(__file__)]+[R/f'docs/superpowers/{d}/2026-10-16-direct-bg-block-upper.md' for d in ['specs','plans']]+[R/f'diagnostics/direct-bg-dynamic-upper/reproduce/{f}' for f in ['slot-upper-reviewed.jl','dynamic-bg-reviewed.jl']]
record={'review_scope':'OFFLINE Task1 only; no Julia invocation, parsing, import, compile, test, numeric simulation, or benchmark','all_passed':all(checks.values()),'checks':checks,'sha256':{str(p.relative_to(R)):H(p) for p in files},'limitations':'Text/hash/arithmetic checks supplement independent manual semantic review; they are not runtime correctness or memory/performance acceptance.'}
with (E/'independent-check-v1.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':record['all_passed'],'checks':len(checks),'candidate_hashes':{p.name:H(p) for p in files[:3]},'failed':[k for k,v in checks.items() if not v]},indent=2))
assert record['all_passed']
