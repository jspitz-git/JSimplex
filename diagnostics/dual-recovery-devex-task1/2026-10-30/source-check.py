from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def require(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
pins=json.loads(read(D/'source-pins.json'))
for path,sha in pins['bindings'].items():require('baseline:'+path,hashlib.sha256(read(path).encode()).hexdigest()==sha)
m=json.loads(read(D/'build-metadata.json'));n=read(D/'simplex_numerics.jl');r=read(D/'simplex_recovery.jl');oldn=read(W/'src/simplex_numerics.jl');oldr=read(W/'src/simplex_recovery.jl')
require('only_numeric_metadata_added',n.count(m['inserted_metadata'])==1 and n.replace(m['inserted_metadata'],'',1)==oldn)
require('whole_recovery_source_inverse',r.count(m['api_prefix']+m['entry'])==1 and r.count(m['compatibility_entry']+m['candidate_kernel'])==1 and r.replace(m['api_prefix']+m['entry'],m['original_wrapper'],1).replace(m['compatibility_entry']+m['candidate_kernel'],m['original_kernel'],1)==oldr)
# Independently reverse each allowed kernel edit, rather than treating the
# complete numeric body as one replaceable blob.
k=m['candidate_kernel']
k=k.replace('buffers,transposed,report::Val{Report}) where {T,Report}','buffers,transposed) where T',1)
k=k.replace('    invalid_seen = false\n    quality.finite || return _refinement_result(report,quality,_refine_nonfinite_initial_quality,true)','    quality.finite || return quality',1)
k=k.replace('''        if quality.reliable
            return _refinement_result(report,quality,_refine_reliable,invalid_seen)
        elseif !quality.finite
            return _refinement_result(report,quality,_refine_nonfinite_quality,true)
        elseif stop()
            return _refinement_result(report,quality,_refine_stopped,invalid_seen)
        end''','        (quality.reliable || !quality.finite || stop()) && return quality',1)
for cause,flag in [('stopped','invalid_seen'),('nonfinite_correction','true'),('nonfinite_trial','true'),('unchanged','invalid_seen'),('nonfinite_trial_quality','true'),('not_improved','invalid_seen')]:
 k=k.replace(f'_refinement_result(report,quality,_refine_{cause},{flag})','quality')
k=k.replace('''                if Report
                    invalid_seen |= !cleaned.finite
                end
''','',1).replace('''                    if Report
                        invalid_seen |= !trial_quality.finite
                    end
''','',1)
k=k.replace('_refinement_finished(report,quality,invalid_seen)','quality',1)
require('arithmetic_guards_and_stop_order_inverse',k==m['original_kernel'])
e=m['entry'].replace('function _refine_basis_solve_entry!','function refine_basis_solve!',1).replace('policy::NumericalPolicy{T},stop,report::Val;','policy::NumericalPolicy{T},stop;',1).replace('transposed::Bool=false) where {T}','transposed::Bool=false)::SolveQuality{T} where {T}',1)
e=e.replace('_record_refinement_result!(ws,_refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed,report))','_record_refactor_quality!(ws,_refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed))')
require('entry_checks_precision_record_inverse',e==m['original_wrapper'])
ref=read(D/'reference.jl');prefix='module RefinementReference\nusing JSimplex\nconst JS=JSimplex\n';suffix='end # module\n'
require('bounded_reference_module',ref.startswith(prefix) and ref.endswith(suffix))
ref=ref[len(prefix):-len(suffix)]
for name in sorted(m['qualified_reference_helpers'],key=len,reverse=True):ref=ref.replace('JS.'+name,name)
require('reference_qualification_inverse',ref==m['original_wrapper']+'\n'+m['original_kernel'])
for path in (W/'src').rglob('*.jl'):require('actual_production_unchanged:'+str(path.relative_to(W)),read(path)==read(M/path.relative_to(W)))
read(D/'refinement_outcome_tests.jl');read(D/'reference_comparison_tests.jl');read(D/'build-candidate.py');read(D/'source-check.py')
(D/'source-check.json').write_text(json.dumps(dict(accepted=True,scope='Python source inverse only; Julia/test/runtime/allocations UNEXECUTED',checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'bindings':len(bindings),'julia_executed':False}))
