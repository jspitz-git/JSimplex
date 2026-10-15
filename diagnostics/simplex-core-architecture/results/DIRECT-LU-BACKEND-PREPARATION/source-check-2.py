"""One new source-only preparation check; no Julia parsing/execution."""
from control import *
import guard
A=D.parent/'DIRECT-LU-COST-PREPARATION';C=D.parent/'DIRECT-LU-REFERENCE-DIAGNOSIS'
U=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers')
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];driver=(D/'driver.jl').read_text();wrap=(U/'wrappers.jl').read_text()
f=next(x for x in rd(A/'inputs.json')['fixtures'] if x['name']=='sparse96')
t=next(x for x in tomllib.loads((A/'inputs.toml').read_text())['fixtures'] if x['name']=='sparse96')
W=R/'.superpowers/direct-lu-markowitz-green-2/candidate'
checks=dict(production514_unchanged=len(base)==514 and all(sha(R/n)==h for n,h in base.items()),
 ordinary_four_sources_unchanged=all(sha(W/'src'/n)==sha(R/'src'/n) for n in ('factorization.jl','triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl')),
 input_json_toml=f==t,dimensions=f['n']==96 and len(f['matrices'])==9 and len(f['steps'])==8,
 fixed_prefix='for k in 1:4' in driver and 'mats[5]' in driver and 'f["matrices"][1:5]' in driver,
 fresh_native='fresh=J._factorize_basis(mats[5],Val(:native))' in driver,
 ordinary_native='J.ForrestTomlinFactorization(mats[1],Val(:native))' in driver,
 output_allocations='fresh_out=[zeros(96) for _ in 1:3]' in driver and 'prefix=[zeros(96) for _ in 1:12]' in driver and 'tail=[zeros(96) for _ in 1:3]' in driver,
 metadata_two='snapshot(fresh,mats[5])' in driver and 'snapshot(factor.base,mats[5])' in driver,
 direct_combined_export=driver.count('API.umfpack_dl_get_numeric(')==1 and 'C_NULL,recip,rs,F.numeric' in driver,
 no_orientation_solve='_hh_scale_mode(' not in driver and '_hh_extract_parts' not in driver,
 installed_abi='do_recip::Ptr{Int64}' in wrap and 'const UMFPACK_INFO = 90' in wrap and 'const UMFPACK_CONTROL = 20' in wrap and 'const UMFPACK_IRSTEP = 7' in wrap,
 raw_before_assert=driver.index('save("raw.toml",raw)')<driver.index('need(raw["completed"]'),
 old_false_preserved=rd(A/'cost1-audit.json')['all_passed'] is False,
 inherited_guards=sha(D/'guard.py')==sha(A/'guard.py') and sha(D/'supervisor.py')==sha(A/'supervisor.py'),
 no_stage_no_reservation=not any(D.glob('probe-*')),
 synthetics52=rd(D/'offline-tests.json')['all_passed'] is True and len(rd(D/'offline-tests.json')['checks'])==52)
paths=[D/'driver.jl',D/'analysis.py',D/'control.py',D/'evidence.py',D/'launch.py',D/'seal.py',D/'audit.py',D/'scaling-contract.md',D/'offline-tests.json',Path(__file__),U/'umfpack.jl',U/'wrappers.jl',D.parent/'S4-L/upstream-umfpack-v7.10.1.h']
paths += [R/'src'/n for n in ('factorization.jl','triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl','huangfu_hall_factorization.jl')]
record=dict(all_passed=all(checks.values()),checks=checks,source_counts=dict(decoded_matrices=5,decoded_step_vectors=15,solve_output_vectors=18,solve_output_entries=1728,ordinary_snapshot_entries=192,factor_snapshots=2,maximum_triangular_nnz_each=4656,maximum_live_native_factors=3,control_entries=20,info_entries=90),sha256={str(p):sha(p) for p in paths})
save(D/'source-check.json',record);print(json.dumps(checks));req(record['all_passed'],'Preparation source checks failed')
