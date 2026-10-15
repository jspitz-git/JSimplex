"""Independent saved-data review. Never imports or executes project/auditor code."""
from pathlib import Path
from fractions import Fraction
import json, hashlib, tomllib, re, traceback
Q=Fraction
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
RES=OUT.parent
bindings={}
def read(path):
    path=Path(path); data=path.read_bytes(); bindings[str(path)]=hashlib.sha256(data).hexdigest(); return data.decode()
def js(path): return json.loads(read(path))
def number(token):
    bits=int(token,16); sign=-1 if bits>>63 else 1
    exponent=(bits>>52)&2047; mantissa=bits&((1<<52)-1)
    assert exponent != 2047
    if exponent: mantissa += 1<<52
    shift=(exponent-1023-52) if exponent else -1074
    return sign*Q(mantissa)*(Q(2)**shift)
def matrix(n,ptr,idx,val,rows=False):
    result=[[Q(0) for _ in range(n)] for _ in range(n)]
    for outer in range(n):
        for pos in range(ptr[outer]-1,ptr[outer+1]-1):
            i,j=(outer,idx[pos]-1) if rows else (idx[pos]-1,outer)
            result[i][j]+=number(val[pos])
    return result
def product(a,b):
    n=len(a); c=[[Q(0) for _ in range(n)] for _ in range(n)]
    columns=[[(k,b[k][j]) for k in range(n) if b[k][j]] for j in range(n)]
    for i in range(n):
        for j in range(n): c[i][j]=sum((a[i][k]*v for k,v in columns[j] if a[i][k]),Q(0))
    return c
def action(a,x): return [sum((v*w for v,w in zip(row,x) if v),Q(0)) for row in a]
def largest(a):return max(abs(v) for row in a for v in row)
def strings(a):return [str(v) for v in a]
checks={}; details={}
try:
    fixture=next(x for x in js(RES/'DIRECT-LU-COST-PREPARATION/inputs.json')['fixtures'] if x['name']=='sparse96')
    source=fixture['matrices'][4]; n=source['n']
    B=matrix(n,source['colptr'],source['rowval'],source['nzval'])
    runs=[tomllib.loads(read(RES/'DIRECT-LU-BACKEND-PREPARATION/probe-run'/name)) for name in ('fresh.toml','prefix.toml')]
    reference=js(OUT/'analysis.json'); ref=reference['result']
    saved=js(RES/'DIRECT-LU-BACKEND-PREPARATION/probe-audit.json')['result']
    interpretation=js(RES/'DIRECT-LU-BACKEND-DIAGNOSTIC/interpretation.json')
    checks['96_square_valid_permutations']=n==96 and all(sorted(run['factor'][k])==list(range(1,n+1)) for run in runs for k in ('p','q'))
    checks['same_factor_except_info']= {k:v for k,v in runs[0]['factor'].items() if k!='info'}=={k:v for k,v in runs[1]['factor'].items() if k!='info'}
    checks['same_all_outputs']=runs[0]['outputs']==runs[1]['ordinary_before_base']==runs[1]['tail_outputs']
    for run_index,run in enumerate(runs):
        f=run['factor']; p=[v-1 for v in f['p']]; q=[v-1 for v in f['q']]; s=list(map(number,f['Rs']))
        L=matrix(n,f['L']['ptr'],f['L']['indices'],f['L']['values'],True)
        U=matrix(n,f['U']['ptr'],f['U']['indices'],f['U']['values'])
        M=[[s[p[i]]*B[p[i]][q[j]] for j in range(n)] for i in range(n)]
        C=product(L,U); error=[[C[i][j]-M[i][j] for j in range(n)] for i in range(n)]
        checks[f'run{run_index}_native_CSC']=f['native_nzval']==source['nzval'] and f['native_colptr']==[v-1 for v in source['colptr']] and f['native_rowval']==[v-1 for v in source['rowval']]
        checks[f'run{run_index}_scale_and_triangle']=f['do_recip']==1 and all(L[i][i]==1 and U[i][i]!=0 and all(L[i][j]==0 for j in range(i+1,n)) and all(U[i][j]==0 for j in range(i)) for i in range(n))
        actual={'max_L':largest(L),'max_U':largest(U),'max_B':largest(B),'max_scaled_B':largest(M),'growth_scaled':largest(U)/largest(M),'growth_unscaled':largest(U)/largest(B)}
        checks[f'run{run_index}_exact_growth']=all(str(v)==ref[k] for k,v in actual.items())
        ranks=sorted([(abs(error[i][j]),i,j,error[i][j]) for i in range(n) for j in range(n) if error[i][j]],reverse=True)
        top=[dict(row=i+1,col=j+1,original_row=p[i]+1,original_col=q[j]+1,value=str(v)) for _,i,j,v in ranks[:12]]
        checks[f'run{run_index}_all_top_errors']=top==ref['top_factor_errors'] and len(ranks)==ref['factor_error_nonzeros']==269
        checks[f'run{run_index}_growth_location']= [(i+1,j+1) for i in range(n) for j in range(n) if abs(U[i][j])==actual['max_U']]==[(31,31)]
        terms=[dict(k=k+1,value=str(L[30][k]*U[k][30])) for k in range(n) if L[30][k]*U[k][30]]
        checks[f'run{run_index}_cancellation']=terms==ref['row31_col31_terms'] and p[30]==86 and q[30]==0 and M[30][30]==0 and sum(Q(z['value']) for z in terms)==Q(-53,2**42) and str(sum(abs(Q(z['value'])) for z in terms))==ref['row31_col31_sum_abs']
        x=list(map(number,run.get('outputs',run.get('tail_outputs'))[1])); y=[x[j] for j in q]; b=list(map(number,fixture['steps'][4]['dse']))
        rep=action(error,y); app=[v-s[i]*b[i] for v,i in zip(action(C,y),p)]; residual=[v-w for v,w in zip(action(B,x),b)]
        dec=saved['decomposition']['fresh']; residual_saved=next(z for z in saved['residuals'] if z['name']=='fresh_dse')
        checks[f'run{run_index}_full_decomposition']=strings(rep)==dec['representation_action'] and strings(app)==dec['combined_application'] and strings(residual)==residual_saved['residual'] and all((app[k]-rep[k])/s[i]==residual[i] for k,i in enumerate(p))
        r87=dict(residual=str(residual[86]),bound=residual_saved['bound'],ratio=float(abs(residual[86])/Q(residual_saved['bound'])),representation=str(rep[30]/s[86]),combined_application=str(app[30]/s[86]))
        checks[f'run{run_index}_row87']=r87==ref['row87'] and rep[30]!=0 and app[30]!=0 and max(map(abs,residual))==abs(residual[86])
        ux=action(U,y)
        ledger=[dict(row=i+1,original_row=p[i]+1,original_column=q[i]+1,L={str(j+1):str(v) for j,v in enumerate(L[i]) if v},U={str(j+1):str(v) for j,v in enumerate(U[i]) if v},Ux=str(ux[i]),sum_abs_Ux_terms=str(sum(abs(v*y[j]) for j,v in enumerate(U[i])))) for i in range(24,32)]
        checks[f'run{run_index}_entire_ledger']=ledger==ref['rows25through32']
        control=list(map(number,f['control'])); info=list(map(number,f['info'])); diag=[abs(U[i][i]) for i in range(n)]
        checks[f'run{run_index}_controls']=control[3]==Q(.1) and control[7]==0 and control[18]==0 and info[18]==1 and all(run[k]['tokens']==f['control'] for k in ('controls_before','controls_after'))
        checks[f'run{run_index}_diagonal_metadata']=info[71]==min(diag) and info[72]==max(diag) and float(info[67])==float(min(diag)/max(diag)) and str(info[67])==ref['rcond_info'] and str(min(diag)/max(diag))==ref['udiag_ratio']
    row_norms=[sum(map(abs,row)) for row in B]; row_max=[max(map(abs,row)) for row in B]; dom=[[j for j,v in enumerate(row) if abs(v)==row_max[i]] for i,row in enumerate(B)]
    margin=min(2*m-norm for m,norm in zip(row_max,row_norms)); norm=max(row_norms)
    checks['strict_unique_permutation_dominance']=all(len(v)==1 for v in dom) and len({v[0] for v in dom})==n and margin==Q(103,32) and norm==Q(153,32) and str(norm/margin)==ref['condition_inf_upper']
    checks['preserved_15pass3fail']=sum(v['passed'] for v in saved['residuals'])==15 and len(saved['residuals'])==18 and saved['failed_residuals']==['fresh_dse','tail_dse','base_dse'] and saved['cost_qualified'] is False
    wrapper=read('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers/wrappers.jl')
    constants={'STRATEGY_USED':18,'PIVOT_TOLERANCE':3,'IRSTEP':7,'DROPTOL':18,'UMIN':71,'UMAX':72,'RCOND':67,'STRATEGY_UNSYMMETRIC':1}
    checks['installed_constant_slots']=all(re.search(r'^const UMFPACK_'+k+r' = '+str(v)+r'$',wrapper,re.M) is not None for k,v in constants.items())
    header=read(RES/'S4-L/upstream-umfpack-v7.10.1.h')
    checks['header_semantics']='min (abs (diag (U))) / max (abs (diag (U)))' in header and 'A value of 1.0 gives true' in header and 'to a more accurate solution (but not always)' in header
    checks['analysis20pass']=reference['all_passed'] and len(reference['checks'])==20 and all(reference['checks'].values())
    checks['all_analysis_readtime_hashes']=all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in reference['sha256'].items())
    for path in reference['sha256']: read(path)
    baseline=js(RES/'DIRECT-LU-PREPARATION/baseline.json'); mismatch=[p for p,h in baseline['sha256'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    checks['baseline514_unchanged']=len(baseline['sha256'])==514 and mismatch==[]
    initial=read(OUT/'analyze.py'); canonical=read(OUT/'analyze-2.py'); failure=js(OUT/'analysis-path-error.json')
    checks['preserved_initial_failure']=canonical==initial.replace('upstream-umfpack-v7.10.1.h.provenance.json','upstream-umfpack-v7.10.1.provenance.json') and hashlib.sha256(initial.encode()).hexdigest()==failure['original_script_sha256'] and failure['exit_code']==1
    details=dict(exact_growth={k:str(v) for k,v in actual.items()},dominance_bound=str(norm/margin),row87=r87,baseline_count=len(baseline['sha256']),baseline_mismatches=mismatch,analysis_binding_count=len(reference['sha256']),constraints='Saved exact arithmetic only; no Julia, solver, old auditor, native execution, benchmarks or production edits.')
except Exception:
    checks['review_completed_without_error']=False; details['exception']=traceback.format_exc()
read(Path(__file__))
result=dict(all_passed=all(checks.values()),checks=checks,details=details,sha256=bindings)
with (OUT/'independent-review-check-2.json').open('x') as handle: json.dump(result,handle,indent=2);handle.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,details=details),indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
