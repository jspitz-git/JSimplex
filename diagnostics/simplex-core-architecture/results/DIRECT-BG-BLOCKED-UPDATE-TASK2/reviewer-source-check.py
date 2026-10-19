from pathlib import Path
import hashlib,json,re,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
C=R/'diagnostics/direct-bg-blocked-update/reproduce'
Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
m=json.loads((C/'adapter-source-map.json').read_text())
src=(R/'src/triangular_factorization.jl').read_text();adapter=(C/'factor.jl').read_text()
checks['original_suffix_in_original_source']=m['original_suffix'] in src
checks['qualified_suffix_in_adapter']=m['qualified_suffix'] in adapter
rest=m['qualified_suffix'].replace('            _emit(probe,:pure,column_index,last_pure)\n','').replace('        _emit(probe,:scalar_pivot,column_index,J._upper_value(column,column_index),\n              J._upper_value(column,column_index+1),swapped)\n','')
for n in m['substitutions']['namespace_symbols']:rest=rest.replace('J.'+n,n)
rest=re.sub(r'\bFloat64\b','T',rest);rest=re.sub(r'\br\b','position',rest)
checks['scalar_suffix_inverse']=rest==m['original_suffix']
fault=(C/'factor-fault.jl').read_text().replace('BGBlockedAdapterFault','BGBlockedAdapter').replace('BGBlockedPanelFault','BGBlockedPanel')
checks['fault_adapter_inverse']=fault==adapter
panel=(C/'panel-fault.jl').read_text().replace('BGBlockedPanelFault','BGBlockedPanel').replace(m['fault_control'],'')
for anchor,hook in m['fault_hooks']:
 checks['fault_hook_'+hook.strip()]=panel.count(anchor+hook)==1
 panel=panel.replace(anchor+hook,anchor)
checks['fault_panel_inverse']=panel==(C/'panel.jl').read_text()
o=json.loads((C/'overlay-manifest.json').read_text());S=Path(o['stage'])
checks['original_hashes']=all(sha(R/p)==v for p,v in o['original_sha256'].items())
checks['stage_hashes']=all(sha(S/p)==v for p,v in o['stage_sha256'].items())
checks['root_include_inverse']=(S/'src/JSimplex.jl').read_text().replace(o['root_insertion'],'',1)==(R/'src/JSimplex.jl').read_text()
checks['stage_unchanged_files']=all((S/p).read_bytes()==(R/p).read_bytes() for p in o['original_sha256'] if p!='src/JSimplex.jl')
checks['ordinary_files']=all(sha(R/'diagnostics/direct-lu-policy-adapters/reproduce'/p)==v and sha(S/'src'/p)==v for p,v in o['ordinary'].items())
f=json.loads((C/'fixtures.json').read_text());t=tomllib.loads((C/'fixtures.toml').read_text())
checks['fixture_json_toml_exact_data']=f['fixtures']==t['fixtures']
old=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/inputs.json'
checks['old_fixture_pin']=sha(old)==f['old_input_sha256']
for p in json.loads(old.read_text())['fixtures']:
 a=next(x for x in f['fixtures'] if x['name']==p['name']);b=p['matrices'][0]
 checks['old_fixture_'+p['name']]=a['initial']==dict(n=b['n'],colptr=b['colptr'],rowval=b['rowval'],bits=b['nzval']) and a['steps']==p['steps']
checks['fixture_dimensions']=all(len(x['initial']['colptr'])==x['n']+1 and len(x['initial']['rowval'])==len(x['initial']['bits']) and all(len(s[k])==x['n'] for s in x['steps'] for k in ('a','dse','unit')) for x in f['fixtures'])
checks['all_finite_success_bits']=all(int(v,16)&0x7ff0000000000000!=0x7ff0000000000000 for x in f['fixtures'] for v in x['initial']['bits']+[v for s in x['steps'] for k in ('a','dse','unit') for v in s[k]])
files=[C/n for n in ('factor.jl','factor-fault.jl','panel-fault.jl','lifecycle-tests.jl','numerical-tests.jl','fixtures.json','fixtures.toml','overlay-manifest.json','adapter-source-map.json','adapter-work-memory.md','panel.jl','panel-tests.jl','source-map.json','work-memory-ledger.md')]
files += [Q/'REPORT.md',Q/'tests-first.json',Q/'fixture-preparation.json',Q/'source-check.json',Q/'reviewer-source-check.py']
result=dict(scope='New independent source/hash/byte checks only; no Julia, old checker execution or numerical simulation',all_passed=all(checks.values()),checks=checks,fixture_count=len(f['fixtures']),updates_per_arm=sum(len(x['steps']) for x in f['fixtures']),sha256={str(p.relative_to(R)):sha(p) for p in files})
with (Q/'reviewer-source-check.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='sha256'},indent=2))
