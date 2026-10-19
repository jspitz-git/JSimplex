"""New one-shot analysis of saved zero-count run; no rerun of numerical driver/auditor."""
from pathlib import Path
import sys,json,statistics
E=Path(__file__).resolve().parent;H=E.with_name('DIRECT-BG-ZERO-COUNTS-HARNESS');sys.path.insert(0,str(H));import control as c
run=H/'runs/zero-counts-300';audit=c.rd(run/'audit.json')
c.require(audit['all_passed'] is True,'Failed run cannot be a qualified measurement')
c.validate_result_closure('zero-counts-300',c.rd(run/'outer-closure.json'))
r=audit['result'];rows=r['records'];summary={}
for case in ('zeros','constructor','dimensions','eligibility','original'):
 arms={}
 for arm in ('reference','candidate'):
  a=[v for v in rows if v['case']==case and v['arm']==arm and v['phase']=='sample'];c.require(len(a)==4,'Four samples')
  arms[arm]=dict(bytes=[v['inner_bytes'] for v in a],events=[v['inner_events'] for v in a],consumed_seconds=[v['consumed_result']['seconds'] for v in a],consumed_bytes=[v['consumed_result']['bytes'] for v in a],consumed_events=[v['consumed_result']['events'] for v in a],clean=all(v[k][f]==0 for v in a for k in ('bytes_wrapper','events_wrapper','consumed_result') for f in ('compile_seconds','recompile_seconds','gc_seconds')))
  arms[arm]['median_seconds']=statistics.median(arms[arm]['consumed_seconds'])
 ratios=[y/x if x else None for x,y in zip(arms['reference']['consumed_seconds'],arms['candidate']['consumed_seconds'])]
 summary[case]=dict(arms=arms,paired_time_ratios=ratios,median_paired_time_ratio=statistics.median(ratios) if all(x is not None for x in ratios) else None)
p=c.rd(run/'output/process.json');inv=c.rd(run/'invocation.json');resources=[json.loads(x) for x in (run/'output/resources.jsonl').read_text().splitlines()]
paths=sorted(p for p in run.rglob('*') if p.is_file())+sorted(p for p in (H/'outers/zero-counts-300').iterdir() if p.is_file())
v=dict(all_passed=True,structural_assertions=r['structural_assertions'],records=len(rows),payload_files=len(list((run/'payload').iterdir())),summary=summary,preparation=r['preparation'],test_tree=r['tests'],process_elapsed_seconds=p['elapsed_including_launch'],supervised_elapsed_seconds=inv['elapsed_seconds'],peak_rss_kib=p['child_maxrss_kib'],resources=dict(samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_used_kib=max(x['swap_used_kib'] for x in resources)),p011_accepted=False,production_promoted=False,sha256={str(p):c.sha(p) for p in paths},scope='Descriptive four-pair samples; separate byte/event/consumed executions; loading overlaps; no subtraction, universal speedup or original P011 acceptance')
c.save(E/'analysis.json',v)
print(json.dumps({k:v[k] for k in ('structural_assertions','records','payload_files','summary','process_elapsed_seconds','resources')},indent=2))
