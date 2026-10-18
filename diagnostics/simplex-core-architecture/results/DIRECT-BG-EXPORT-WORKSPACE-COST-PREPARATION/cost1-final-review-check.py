"""Final narrative/publication review checks; no closure/publication execution."""
from pathlib import Path
import json,sys,tomllib,ast
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
a=c.rd(D/'runs/cost1-300/audit.json');text=(D/'FINAL.md').read_text();checks={}
def ck(name,v):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
post=c.rd(D/'postcheck.json')
ck('author71checks',post['all_passed'] is True and len(post['checks'])==71 and all(post['checks'].values()) and c.bindings(post))
for i,cell in enumerate(a['cells'],1):
 st=cell['statistics'];f,b=cell['fixture'],cell['backend']
 success=st['time_median_gate'] and st['allocation_gate'] and st['memory_gate'] and st['faster_pairs']>=3
 expected=f"| {f} | {b} | {st['seconds']['paired_ratio']['median']:.6f} | {st['seconds']['paired_ratio']['mad']:.6f} | {st['bytes']['reference']['median']}→{st['bytes']['candidate']['median']} | {st['events']['reference']['median']}→{st['events']['candidate']['median']} | {st['retained_bytes']['reference']['median']}→{st['retained_bytes']['candidate']['median']} | {st['faster_pairs']}/7 | {'PASS' if success else 'FAIL'} |"
 ck(f'cost_table_{i}',expected in text)
 numbers={side:', '.join(f"{x[side]['median']*1e6:.2f}" for x in st['nested_seconds']) for side in ('reference','candidate')}
 ck(f'nested_table_{i}',f"| {f}/{b} | {numbers['reference']} | {numbers['candidate']} |" in text)
 p=tomllib.loads((D/f'runs/cost1-300/output/probe-{i}.toml').read_text());v=p['counts']
 ck(f'probe_table_{i}',f"| {f}/{b} | {p['cache_charge_peak']} | {v['allocation_requests']} | {v['requested_payload']} | {v['normalized_stores']} | {p['coexistence_graph_peak']} |" in text)
for f in ('closure.py','publication.py'):ast.parse((D/f).read_text(),filename=f)
ck('closure_publication_python_syntax',True)
ck('fixed_stop_explicit','no second process' in text and 'NOT accepted for performance or production integration' in text and 'The broader architectural plan remains open.' in text)
ck('GC_and_scope_disclosed',all(v in text for v in ('16.413201ms','5.315801ms','3.956/3.9486ms','0.018021','4.192580','not a universal peak','not instrumentation of every backend attempt')))
ck('exact_result_review_membership_required',"c.result_review('cost1-300','BG export workspace cost result','result-review.json')" in (D/'closure.py').read_text())
ck('closure_stop_required',"rv.get('performance_accepted') is False and rv.get('second_process_allowed') is False" in (D/'closure.py').read_text())
ck('publication_requires_pass_and_exact_membership',all(x in (D/'publication.py').read_text() for x in ("cl['all_passed'] and all(cl['checks'].values()) and c.bindings(cl)","==set(others)","==set(names)","'diff','--cached','--check'","'rev-parse',':'+n)==c.git('hash-object',n)")))
files=[D/n for n in ('postcheck.py','postcheck.json','postcheck-host.json','FINAL.md','closure.py','publication.py')]
result=dict(all_passed=all(checks.values()),checks=checks,check_count=len(checks),sha256={str(p):c.sha(p) for p in files},
 scope='New final narrative and exact diagnostic publication source review only; these scripts were not executed')
with (D/'cost1-final-review-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks))))
