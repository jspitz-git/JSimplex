"""Exclusive postrun supplement; preserve original false gate and all raw evidence."""
from pathlib import Path
import json,tomllib,hashlib
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent
raw=H/'qualification-1/raw';a=json.loads((H/'audit.json').read_text());r=tomllib.loads((raw/'throw.toml').read_text());o=r['observed_outcome']
old=o['stop_flag'] is False and r['true_stop_calls']==0 and 'DiagnosticObserverFailure{' in o['caught_type'] and o['caught_identity']!='nothing' and o['cause_identity']==o['sentinel_identity'] and o['cause_type']==o['sentinel_type']=='SingularException'
correct=o['stop_flag'] is False and r['true_stop_calls']==0 and o['returned_type']=='Nothing' and o['returned_identity']=='nothing' and o['caught_type']=='JSimplex.DiagnosticObserverFailure{LinearAlgebra.SingularException}' and o['caught_identity']!='nothing' and o['cause_identity']==o['sentinel_identity'] and o['cause_type']==o['sentinel_type']=='LinearAlgebra.SingularException'
src=(ROOT/'src/simplex_diagnostics.jl').read_text();driver=(H.parent/'S5-F/driver-reviewed.jl').read_text()
checks={'original_failure_preserved':a['all_passed'] is False and [k for k,v in a['checks'].items() if not v]==['throw.outcome'],'other62_original_gates_true':sum(a['checks'].values())==62 and len(a['checks'])==63,'original_predicate_reproduced_false':old is False,'qualified_raw_cause_outcome':correct,'exact_source_wrapper':'throw(DiagnosticObserverFailure(exception))' in src and 'struct DiagnosticObserverFailure{E} <: Exception' in src,'raw_provenance':'sentinel=SingularException(7)' in driver and 'cause_type=caught isa JS.DiagnosticObserverFailure ? string(typeof(caught.cause))' in driver,'full_independent_post':json.loads((H/'independent-post.json').read_text())['all_passed'] is True}
files=[H/'audit.py',H/'audit.json',H/'independent-post.json',raw/'stop.toml',raw/'throw.toml',raw/'summary.toml',H.parent/'S5-F/driver-reviewed.jl',ROOT/'src/simplex_diagnostics.jl',Path(__file__)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'checks':checks,'all_passed':all(checks.values()),'old_predicate':old,'qualified_predicate':correct,'raw_outcome':o,'sha256':{str(p):sha(p) for p in files},'scope':'Qualified type spelling only; original auditor/output immutable. No numerical rerun.'}
with (H/'outcome-supplement.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':result['all_passed']}));assert result['all_passed']
