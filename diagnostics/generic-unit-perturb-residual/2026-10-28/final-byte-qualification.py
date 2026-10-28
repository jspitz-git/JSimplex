from pathlib import Path
import sys,shutil,tomllib,statistics as stats
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
p=D/'FINAL-REPORT.md';old=p.read_text();needle='All measured calls save three aggregate allocation events and160–688bytes; elapsed-time benefit is inconclusive.'
c.need(old.count(needle)==1,'unique byte consistency qualification')
rows=[v for v in tomllib.loads((D/'output/results.toml').read_text())['cells'] if v['variant']=='C'];diffs=[];events=[];medians=[]
for row in rows:
 a=[w for w in row['windows'] if w['arm']=='original'];b=[w for w in row['windows'] if w['arm']=='C'];medians.append(stats.median(w['bytes'] for w in a)-stats.median(w['bytes'] for w in b))
 for pair in range(1,10):
  aa=next(w for w in a if w['pair']==pair);bb=next(w for w in b if w['pair']==pair);diffs.append(aa['bytes']-bb['bytes']);events.append(aa['events']-bb['events'])
c.need(len(rows)==456 and len(diffs)==4104 and set(events)=={3} and sum(d<0 for d in diffs)==7 and (min(medians),max(medians))==(160,688),'exact observed C qualifications')
replacement='Every measured pair saves three aggregate allocation events. Per-cell differences of median allocated bytes favor C by 160–688 bytes, with retained individual-pair outliers including byte increases; elapsed-time benefit is inconclusive. Seven of 4,104 pairs have byte increases (maximum 2,032 bytes); all are preserved.'
before=D/'FINAL-REPORT.md.before-byte-qualification';c.need(not before.exists(),'exclusive report beforeimage');shutil.copyfile(p,before);p.write_text(old.replace(needle,replacement));shutil.copyfile(__file__,D/'final-byte-qualification.py')
c.put('final-byte-qualification.json',dict(accepted=True,documentation_only=True,numerics=False,cases=len(rows),pairs=len(diffs),all_pair_event_saving=3,individual_pair_byte_saving_range=[min(diffs),max(diffs)],pairs_with_byte_increase=7,per_cell_difference_of_median_bytes_range=[min(medians),max(medians)],historical_paths={str(p):dict(sha256=c.sha(before),before=str(before))},bindings={str(D/n):c.sha(D/n) for n in ['FINAL-REPORT.md','FINAL-REPORT.md.before-byte-qualification','final-byte-qualification.py','output/results.toml','final-artifact-review-findings.json']}))
print('report-only correction C4104pairs/7byteincreases, all3eventssaved; cellmediandifferences160–688bytes')
