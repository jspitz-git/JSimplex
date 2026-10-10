"""Audit guarded numerical evidence without starting Julia."""
from pathlib import Path
import hashlib,itertools,json,math,re,shutil,statistics,tomllib
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'.superpowers/bg-certificate-diagnosis'
DEST=ROOT/'diagnostics/bg-certificate-diagnosis/results'
DEST.mkdir(exist_ok=True)
expected={'targeted','cost-baseline','cost-production','semantic','external','project-suite','runtime'}
entry=json.loads((RAW/'entry-semantic/process.json').read_text())
assert entry['returncode']==0 and entry['sources_unchanged']
completed=json.loads((RAW/'validation-results.json').read_text())
assert len(completed)==len(expected) and {x['job'] for x in completed}==expected
assert all(x['returncode']==0 for x in completed if x['job']!='project-suite')
provenance={}
for directory in sorted(RAW.iterdir()):
    if not (directory/'process.json').exists():continue
    name=directory.name;p=json.loads((directory/'process.json').read_text())
    assert p['sources_unchanged'],name
    pre=json.loads((directory/'preflight.json').read_text())
    log=(directory/'run.log').read_text()
    match=re.search(r'Maximum resident set size \(kbytes\): (\d+)',log)
    p['max_rss_kib']=int(match[1]) if match else None
    p['preflight_sha256']=hashlib.sha256((directory/'preflight.json').read_bytes()).hexdigest()
    src={k:v for k,v in pre.items() if '/src/' in k}
    p['source_manifest_sha256']=hashlib.sha256(json.dumps(src,sort_keys=True).encode()).hexdigest()
    p['key_hashes']={k:v for k,v in pre.items() if k.endswith(('native_cleanup_recovery.jl','native_cleanup_recovery.jl.baseline','runtime.mps','3-internal.bin','Project.toml','Manifest.toml','LocalPreferences.toml','guard.py','julia.sh')) or '/bg-certificate-diagnosis/reproduce/' in k}
    if name=='red1':
        assert p['returncode']!=0 and 'Test Failed' in log
        p['classification']='Expected regression failure on the original implementation.'
    elif name=='stages1':
        assert p['returncode']!=0 and 'ParseError' in log
        p['classification']='Diagnostic include-guard syntax error; replaced by stages2.'
    elif name=='replay1':
        assert p['returncode']!=0 and 'cannot convert a value to nothing' in log
        p['classification']='Diagnostic context parameter mismatch; replaced by replay2.'
    elif name=='project-suite' and p['returncode']:
        assert 'wall-time guard' in log and 'libLLVM' in log and 'dual_entry_phase_tests.jl' in log
        p['classification']='600-second watchdog during LLVM compilation at dual_entry_phase_tests.jl:15; incomplete suite, not a solver numerical failure.'
    else:assert p['returncode']==0,name
    if name=='capture1':p['classification']='Intentional diagnostic stop at the first numerical terminal; not a complete solve.'
    if name=='replay2':p['classification']='Certified continuation of the saved reduced/scaled workspace; no full-LP postsolve.'
    provenance[name]=p
    if (directory/'result.toml').exists():shutil.copyfile(directory/'result.toml',DEST/(name+'.toml'))
    if name in ('targeted','semantic','external','project-suite','red1','green1','stages1','replay1','entry-semantic','row1'):
        shutil.copyfile(directory/'run.log',DEST/(name+'.log'))
shutil.copyfile(RAW/'capture1/boundaries.toml',DEST/'boundaries.toml')
boundaries=tomllib.loads((DEST/'boundaries.toml').read_text())['boundaries']
assert [(x['tag'],x['status'],x['iterations']) for x in boundaries]==[('dual','OPTIMAL',259),('dual','OPTIMAL',50718),('internal','NUMERICAL_ERROR',50718)]
assert boundaries[-1]['message']=='bounded feasibility recovery exhausted'
assert boundaries[-1]['events']['certification']==0
replay=tomllib.loads((DEST/'replay2.toml').read_text())
assert replay['status']=='OPTIMAL' and replay['same_basis'] and replay['original_certificate'] and replay['original_feasible']
assert replay['iterations']==replay['before']['iterations']==50718 and replay['after']['original_costs']
manifest=tomllib.loads((ROOT/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').read_text())['cases']
entries={r['id']:r for r in manifest}
external=tomllib.loads((DEST/'external.toml').read_text())['cases']
keys=[(r['id'],r['backend'],r['algorithm'],r['basis_update']) for r in external]
grid=set(itertools.product(entries,('native','markowitz'),('primal','dual'),('pfi','huangfu_hall','forrest_tomlin','suhl_suhl','bartels_golub')))
assert len(keys)==len(set(keys))==100 and set(keys)==grid
for r in external:
    assert r['status']=='OPTIMAL' and r['original_primal_certified'] and r['objective_matches']
    assert r['input_sha256']==entries[r['id']]['sha256']
    assert math.isclose(r['objective'],entries[r['id']]['objective'],rel_tol=1e-8,abs_tol=1e-7)
full=tomllib.loads((DEST/'runtime.toml').read_text())
assert full['status']=='OPTIMAL' and full['original_feasible']
assert full['input_sha256']=='d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
assert math.isclose(full['objective'],51425691.7621,rel_tol=1e-8)
# Internal refreshes are legitimate safeguards; require no numerical terminal
# and no precision escalation, and report recovery counts rather than forbid them.
assert full['events']['certification_failed']==full['events']['precision_boost']==0
cost={}
for mode in ('baseline','production'):
    rows=tomllib.loads((DEST/('cost-'+mode+'.toml')).read_text())['samples']
    assert [r['sample'] for r in rows]==list(range(10))
    assert all(r['success']==(mode=='production') for r in rows)
    steady=rows[1:]
    assert all(r['compile_seconds']==0 for r in steady)
    cost[mode]={k:statistics.median(r[k] for r in steady) for k in ('seconds','bytes','allocations')}
previous=tomllib.loads((ROOT/'diagnostics/basis-kernel-savings/results/external.toml').read_text())['cases']
key=lambda r:(r['id'],r['backend'],r['algorithm'],r['basis_update'])
old={key(r):r['iterations'] for r in previous}
summary=dict(external_combinations=100,external_iterations_match_previous=all(r['iterations']==old[key(r)] for r in external),cost_medians=cost,runtime=full,
    project_suite_passed=provenance['project-suite']['returncode']==0,
    no_production_precision_increase=True)
(DEST/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(DEST/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
