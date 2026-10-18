"""New one-shot read-only source/data derivation for planning; no old code imported."""
from pathlib import Path
import json,hashlib,tomllib,statistics
R=Path.cwd();E=Path(__file__).resolve().parent
run=E.parent/'DIRECT-BG-SPLIT-COST-PREPARATION/runs/cost1-300';out=run/'output'
spec=R/'docs/superpowers/specs/2026-10-18-direct-bg-import-reserve.md';plan=R/'docs/superpowers/plans/2026-10-18-direct-bg-import-reserve.md'
checks={};bindings={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):bindings[str(p)]=sha(p);return p.read_text()
def need(k,v):checks[k]=bool(v)
sealed=json.loads(read(run/'sealed.json'))
selected=['split-upper.jl','split-bg.jl','triangular_indices.jl','triangular_factorization.jl','direct-factor.jl','cost.jl','probe-upper.jl','probe.jl','bartels_golub_rows.jl']
matched=[]
for n,v in sealed['inventory'].items():
 if any(n.endswith('/'+x) for x in selected):
  p=Path(n);read(p);matched.append(str(p.resolve())==v['resolved'] and sha(p)==v['sha256'])
need('selected_sealed_source_bindings',len(matched)==18 and all(matched))
review=json.loads(read(run/'result-review.json'));need('stored_result_review_accepted',review['accepted'] is True and not review['findings'])
read(E.parent/'DIRECT-BG-SPLIT-COST1/REPORT.md');read(R/'AGENTS.md');read(E/'host.json');read(Path(__file__).resolve())
sp=read(spec);pl=read(plan)
capacity=lambda n:2 if n==1 else 4 if n in (2,3) else n
need('exact_classes',[capacity(n) for n in range(1,33)]==[2,4,4]+list(range(4,33)))
need('bounded_delta',all(0<=capacity(n)-n<=2 and n<=capacity(n)<=32 for n in range(1,33)))
need('column_geometry',all((0 if m==0 else (m-1)//32*32+capacity((m-1)%32+1))<=32*((m+31)//32) for m in range(257)))
need('canonical_lengths',[[32]*(n//32)+([capacity(n%32)] if n%32 else []) for n in [0,1,2,3,4,31,32,33,34,35,36,64]]==[[],[2],[4],[4],[4],[31],[32],[32,2],[32,4],[32,4],[32,4],[32,32]])
cells=[]
for c in range(1,9):
 p=out/f'probe-{c}.toml';data=tomllib.loads(read(p));need(f'probe_binding_{c}',sha(p)==review['sha256'][str(p)])
 rows=[]
 for f in sorted(out.glob(f'window-{c}-*.toml')):
  row=tomllib.loads(f.read_text())
  if row['measured']:
   read(f);need(f'window_binding_{c}_{row["pair"]}_{row["side"]}',sha(f)==review['sha256'][str(f)])
   rows.append(row)
 pairs={side:{r['pair']:r for r in rows if r['side']==side} for side in ['reference','candidate']}
 need(f'pair_membership_{c}',all(set(v)==set(range(4,11)) for v in pairs.values()))
 imports=[]
 for state in data['states']:
  if state['step']==0 or state['refactored']:
   u=state['storage'];tails=set(u['column_tails'])-{0};hist={};delta=0
   for b in tails:
    t=u['extents'][b-1][3];hist[t]=hist.get(t,0)+1;delta+=capacity(t)-t
   need(f'initial_partition_{c}_{state["step"]}',u['C']==u['live']==u['R'] and u['free_capacity']==u['active_slack']==0)
   need(f'prospective_bound_{c}_{state["step"]}',delta<=2*len(u['column_tails']) and u['C']+delta<=32*u['K'])
   imports.append(dict(step=state['step'],tail_histogram=hist,old_capacity=u['C'],old_graphs=state['graphs'][:2],added_slots=delta,added_payload=16*delta,payload_only_graph_projection=(state['graphs'][1]+16*delta)/state['graphs'][0],scope='Arithmetic on stored unmodified factors only; NOT future graph measurement or gate'))
 refs=pairs['reference'];cand=pairs['candidate']
 med=lambda key,scale=1:statistics.median((cand[k][key]-refs[k][key])*scale for k in range(4,11))
 phase=[statistics.median((cand[k]['nested_seconds'][i]-refs[k]['nested_seconds'][i])*1e6 for k in range(4,11)) for i in range(6)]
 cells.append(dict(cell=c,imports=imports,counts=data['counts'],first_update_counter_delta={k:data['states'][1]['counts'][k]-data['states'][0]['counts'][k] for k in data['counts']},median_paired_delta_bytes=med('bytes'),median_paired_delta_events=med('events'),median_paired_delta_microseconds=med('seconds',1e6),median_paired_phase_delta_microseconds=phase))
need('saved_initial_sparse_payload',[cells[i]['imports'][0]['added_payload'] for i in [0,1,4,5]]==[976,1008,3024,3056])
need('dense_payload',[cells[i]['imports'][0]['added_payload'] for i in [2,3,6,7]]==[64,64,192,192])
need('allocation_delta',[cells[i]['median_paired_delta_bytes'] for i in [0,1]]==[1408,832] and [cells[i]['median_paired_delta_events'] for i in [0,1]]==[49,66])
need('first_update_relocations',[cells[i]['first_update_counter_delta']['relocations'] for i in [0,1,4,5]]==[32,33,96,97])
need('new_scope_only',not (R/'diagnostics/direct-bg-import-reserve').exists())
need('memory_contract',all(t in sp for t in ['16*C + 4*R + 28*K + 32*n + 656','32*(n_old+n_new)','96*n','3*Delta','C0<=32*K0']))
need('no_numeric_authority','No candidate, driver, launcher, Julia/query/parser/import/compile' in sp and 'No implementation, Julia/query/parser/import/compile/numerics' in pl)
need('task_focus_coverage',all(t in pl for t in ['nonidentity_q_offsets','explicit_signed_zero_import','import_size_limits_before_allocate','reserved_third_entry','copy_padded_independence','11lifecycle checkpoints']))
result=dict(scope='Source/data-derived import-reserve planning only; no Julia or old checker execution',all_passed=all(checks.values()),checks=checks,readtime_sha256=bindings,cells=cells)
with (E/'author-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),readtime_bindings=len(bindings),failed=[k for k,v in checks.items() if not v])))
if not result['all_passed']:raise SystemExit(1)
