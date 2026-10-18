"""One-shot supplementary post-run check. Does not rerun numerical auditor."""
from pathlib import Path
import sys,json,statistics,tomllib
R=Path.cwd();E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-SPLIT-COST-PREPARATION';sys.path.insert(0,str(D));import control as c
run=D/'runs/cost1-300';out=run/'output';a=c.rd(run/'audit.json');p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');sealed=c.rd(run/'sealed.json');pins=c.rd(run/'launch-pins.json')
c.validate_sources();c.validate_environment();c.preparation();c.predecessor('cost1-300');h=c.full_host(c.rd(run/'posthost.json')['groups']);h['memory']=c.guard.memory();c.save(E/'posthost.json',h)
checks=dict(preparation_sources_environment=True,predecessor=True,admitted_audit_hashes=c.bindings(a),seal_inputs=c.guard.pins_match(sealed),launch_inputs=c.guard.pins_match(pins),allowance=c.rd(E/'allowance.json')['authorized'] is True and c.rd(E/'allowance.json')['max_seconds']==300,one_attempt={q.name for q in (D/'runs').iterdir()}=={'cost1-300'},host_clear=not h['matches'] and not c.guard.pressure(h['memory']),refs=h['head']==sealed['head']=='49b26f913df5497bafa8292529a872070864911c' and h['master']==c.MASTER,elapsed_bounded=0<=inv['elapsed_seconds']<=300,process_groups_covered=all(p[role][key] in h['groups'] for role in ['runner','child'] for key in ['pgid','sid']))
rows=[]
if a['all_passed']:
 for idx,cell in enumerate(a['cells'],1):
  windows=[tomllib.loads((out/f'window-{idx}-{w}.toml').read_text()) for w in range(1,21)]
  pairs=[{v['side']:v for v in windows if v['pair']==i} for i in range(4,11)]
  s=cell['statistics'];ratios={k:[d['candidate'][k]/d['reference'][k] for d in pairs] for k in ['seconds','bytes','events','retained_bytes']};medians={k:statistics.median(v) for k,v in ratios.items()}
  checks[f'cell{idx}_paired_statistics']=all(medians[k]==s[k]['paired_ratio']['median'] for k in medians)
  checks[f'cell{idx}_all_bits']=all(d['reference']['outputs']==d['candidate']['outputs'] and d['reference']['modes']==d['candidate']['modes'] for d in pairs)
  rows.append(dict(fixture=cell['fixture'],backend=cell['backend'],paired_medians=medians,faster_pairs=s['faster_pairs'],time_gate=s['time_median_gate'],allocation_gate=s['allocation_gate'],memory_gate=s['memory_gate'],probe_memory_gate=s['probe_memory_gate'],max_probe_graph_ratio=max(z['graphs'][1]/z['graphs'][0] for z in cell['probe']['states'])))
 checks['complete_cells_windows']=len(rows)==8 and a['counts']==dict(cells=8,windows=160,exact_residuals=4416)
result=dict(all_passed=all(checks.values()),checks=checks,admitted_audit_passed=a['all_passed'],pure_timeout=a['pure_timeout'],first_process_viable=c.first_process_viable(a,c.rd(D/'inputs.json')['fixtures']),cells=rows,sha256={str(f):c.sha(f) for f in [Path(__file__),E/'allowance.json',E/'posthost.json',run/'audit.json',run/'invocation.json',run/'sealed.json',run/'launch-pins.json',out/'process.json']},scope='Supplemental integrity/statistics only; admitted numerical auditor and immutable measurements not rerun')
c.save(E/'postcheck.json',result);print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),audit=a['all_passed'],pure_timeout=a['pure_timeout'],viable=result['first_process_viable'],cells=rows),indent=2));c.require(result['all_passed'],'Supplement refused')
