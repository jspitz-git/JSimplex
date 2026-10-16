"""New source/saved-data arithmetic ledger. No Julia, model solve or old auditor."""
from pathlib import Path
import hashlib,json,re,tomllib
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent
C=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=(C/'block-upper.jl').read_text();fields=re.findall(r'^    (\w+)::([^\n]+)',source.split('\nend',1)[0],re.M)
checks={'field_count27':len(fields)==27,'vector_fields23':sum('Vector' in t for _,t in fields)==23,'four_int_fields':sum(t=='Int' for _,t in fields)==4}
paths=[C/'block-upper.jl',C/'block-oracles.jl',C/'block-upper-tests.jl',Path(__file__),E/'host.json',E/'authorization.json',R/'docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md',R/'docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
rows=[];points=[]
for case in range(1,9):
    p=E.parent/f'DIRECT-BG-DYNAMIC-COST-PREPARATION/runs/cost1-300/output/probe-{case}.toml';paths.append(p);raw=tomllib.loads(p.read_text())
    n=32 if case<=4 else 96;dense=case in (3,4,7,8);m=raw['states'][0]['live']
    klo=sum((i+31)//32 for i in range(1,n+1)) if dense else n
    khi=klo if dense else n+(m-n)//32
    def graph(C,R,K,S=1,D=1):return 16*C+4*R+28*K+32*n+656+8*n+24*D+40*(n+3*S+23)+216
    initial=raw['states'][0];glo=graph(m,m,klo);ghi=graph(m,m,khi)
    estimate_lo=initial['graphs'][1]-initial['arena_graph_bytes']+glo
    estimate_hi=initial['graphs'][1]-initial['arena_graph_bytes']+ghi
    rows.append(dict(case=case,n=n,dense=dense,m=m,K0_min=klo,K0_max=khi,core_min=20*m+28*klo+32*n+656,modeled_U_graph_min=glo,modeled_U_graph_max=ghi,old_reference_factor=initial['graphs'][0],modeled_factor_min=estimate_lo,modeled_factor_max=estimate_hi,threshold_tenths=11*initial['graphs'][0],lower_exceeds=10*estimate_lo>11*initial['graphs'][0]))
    segment_m=m;segment_k=klo
    for idx,s in enumerate(raw['states']):
        live=s['live']
        if s['refactored']:
            segment_m=live;segment_k=klo if dense and live==m else max(n,(live+31)//32)
        k=max(segment_k,n,(live+31)//32);cc=segment_m+256*max(0,(live-segment_m+255)//256);rr=max(segment_m,live)
        modeled=s['graphs'][1]-s['arena_graph_bytes']+graph(cc,rr,k)
        points.append(dict(case=case,checkpoint=idx,live=live,optimistic_C=cc,optimistic_R=rr,optimistic_K=k,modeled_factor_lower=modeled,old_reference=s['graphs'][0],lower_exceeds=10*modeled>11*s['graphs'][0]))
    checks[f'old_arena_graph_case{case}']=all(s['arena_graph_bytes']==56*s['capacity']+64*n+752 for s in raw['states'])
checks['initial8_not_proven_failed']=not any(r['lower_exceeds'] for r in rows)
checks['checkpoint88_not_proven_failed']=len(points)==88 and not any(r['lower_exceeds'] for r in points)
checks['no_zero_fill_import']=all(s not in source for s in ['U.rows[r]=_bgu_zeros(Int32,d','U.values[1]=_bgu_zeros(Float64,m'])
checks['copy_no_redundant_init']='length(U.values),allocate,false)' in source
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
paths.extend([runtime/'summarysize.jl',runtime/'array.jl'])
record=dict(all_passed=all(checks.values()),checks=checks,fields=fields,initial=rows,checkpoint_lower_bounds=points,sha256={str(p):sha(p) for p in paths},limits='All new graph figures are source+old-graph models, not runtime acceptance. Sparse exported column degrees unknown: K interval, not exact reconstruction. At checkpoints C/R/K minima omit unavoidable actual fragmentation/gap slack; no lower-bound rejection is NOT a pass or upper bound.40B vector model matches saved graph; physical allocator rounding/native peak unknown. New runtime source reads are readtime pins only.')
with (E/'budget-final.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=checks,initial=rows),indent=2))
if not record['all_passed']:raise SystemExit(1)
