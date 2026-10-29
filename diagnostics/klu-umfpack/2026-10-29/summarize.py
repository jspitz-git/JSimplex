from pathlib import Path
import json,tomllib,csv,statistics
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/klu-umfpack/2026-10-29')
d=tomllib.loads((D/'results-1.toml').read_text());ar=json.loads((D/'analysis.json').read_text());rows=list(csv.DictReader((D/'summary.csv').open()));out=[]
for case in d['cases']:
 r={arm:{s['round']:s for s in d['samples'] if s['measured'] and s['case']==case['id'] and s['arm']==arm} for arm in ['UMFPACK-one','KLU-BTF-AMD-one']}
 u,k=r.values();v=[(k[i]['ftran']['seconds']+k[i]['btran']['seconds'])/(u[i]['ftran']['seconds']+u[i]['btran']['seconds']) for i in u]
 a,b=[x for x in rows if x['case']==case['id']]
 out.append(dict(case=case['id'],solve_triplet_paired_median=statistics.median(v),solve_triplet_range=[min(v),max(v)],native_current_ratio=int(b['native_current'])/int(a['native_current']),native_peak_ratio=int(b['native_peak'])/int(a['native_peak']),factor_bytes_ratio=float(b['factor_bytes'])/float(a['factor_bytes']),factor_event_ratio=float(b['factor_events'])/float(a['factor_events'])))
(D/'derived-summary.json').write_text(json.dumps(dict(scope='additional offline derivation from existing output only',cases=out),indent=2)+'\n')
print(json.dumps(out))
