from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-R';a=json.loads((E/'source-contract.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks={}
checks['full570_readtime_rehash']=len(a['sha256'])==570 and all(sha(p)==h for p,h in a['sha256'].items())
q=json.loads((D/'results/S4-Q/cost-1-pins.json').read_text())['inventory']
checks['independent_Q558_same']=len(q)==558 and all(sha(p)==v['sha256'] for p,v in q.items())
checks['literal_checks24_pass']=len(a['checks'])==24 and all(a['checks'].values()) and a['all_passed']
checks['GI8_hash_comparisons']=len(a['comparisons'])==8 and all(a['comparisons'].values())
prod=(R/'src/huangfu_hall_factorization.jl').read_text();clone=(D/'reproduce/hh_history_cost_clone.jl').read_text()
expected=prod[prod.index('_hh_refactor_lu!(F::Float64UMFPACK'):prod.index('function copy_basis_factorization(f::HuangfuHallFactorization')]
expected=expected.replace('_hh_refactor_lu!','_s4q_refactor_lu!').replace('_hh_refactor_backend','_s4q_refactor_backend').replace('function refactorize!','function _s4q_refactorize!').replace('reuse_symbolic=false','reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))')
checks['independent_forward_clone_exact']=expected==clone
report=(D/'S4-PUBLIC-CONTROLLER-REUSE-CONTRACT.md').read_text();plan=(R/'docs/superpowers/plans/2026-10-12-hh-isolated-module-loading-contract.md').read_text()
checks['explicit_no_numerical_plan']=('No numerical plan or new LP' in report and 'No Julia, module loading' in plan and 'SOURCE/EVIDENCE ONLY' in plan)
checks['production_test_CI_same']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
oldpaths=['diagnostics/simplex-core-architecture/results/S4-'+s for s in 'EFGHIJKLMNOPQ']
checks['old_E_Q_evidence_untouched']=not subprocess.check_output(['git','diff','HEAD','--',*oldpaths,'diagnostics/simplex-core-architecture/reproduce'])
result=dict(checks=checks,all_passed=all(checks.values()),scope='Separate author check, full570/Q558 hashes and forward-clone reconstruction, no Julia and no old script rerun')
with (E/'independent.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result));assert result['all_passed']
