"""Seal the independently reviewed local result; no numerical execution."""
from pathlib import Path
import json,hashlib,statistics as st,tomllib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-V-EXEC';V=E.with_name('MA-V');report=R/'diagnostics/simplex-core-architecture/MA-ROUNDING-GUARD-QUALIFICATION.md'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
x=rd(E/'reviewer-check.json');s=rd(E/'result-summary.json');am=rd(E/'report-amendment.json');txt=report.read_text()
replace={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):str(E/'STATUS.md.before-MA-V-execution'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):str(E/'roadmap.md.before-MA-V-execution')}
bindings={replace.get(p,p):h for p,h in x['sha256'].items()}
checks={
 'independent42record':x['all_computed_checks_passed'] is True and len(x['computed_checks'])==42 and all(x['computed_checks'].values()),
 'preserved_binding_recheck':all(sha(p)==h for p,h in bindings.items()),
 'report_amendment_bindings':all(sha(p)==h for p,h in am['sha256'].items()),
 'report_tables':True,
 'probe_limit_explicit':'its749-byte text does not bound the transitive helper' in txt,
 'recorded_summary_counts':s['measured_windows']==x['details']['measured_windows']==532 and s['measured_gc_windows']==x['details']['measured_gc_windows']==3 and s['correctness_counts']==x['details']['recorded_assertion_counts'] and s['no_scope_available'] is False,
 'micro_summary':True,
}
for row in x['details']['costs']:
 p=row['processes'][0];line=f"| {row['id']} | {row['reference_seconds_per_call']*1e6:.3f} | {row['candidate_seconds_per_call']*1e6:.3f} | {row['pooled_ratio']:.6f} | {p['reference_bytes']:g} / {p['candidate_bytes']:g} | {p['reference_events']:g} / {p['candidate_events']:g} |"
 checks['report_tables'] &= line in txt and all(p[k]==row['processes'][1][k] for k in ('reference_bytes','candidate_bytes','reference_events','candidate_events'))
raws=[tomllib.loads((V/f'run-{i}/raw.toml').read_text()) for i in (1,2)]
for ci,row in enumerate(s['micro']):
 for side in ('reference','candidate'):
  ws=[w for r in raws for w in r['micro'][ci]['windows'] if w['phase']=='measured' and w['side']==side]
  checks['micro_summary'] &= row[side]==dict(seconds_per_call=st.median(w['seconds']/256 for w in ws),bytes_per_window=st.median(w['bytes'] for w in ws),events_per_window=st.median(w['events'] for w in ws))
if not all(checks.values()):raise ValueError(checks)
for p in (E/'reviewer-check.json',E/'reviewer-finalize.py',E/'result-review.md',report,E/'report-amendment.json',E/'report.before-review',E/'continuation-map.json'):
 bindings[str(p)]=sha(p)
obj=dict(accepted=True,scope='Completed MA-V local rounding-guard qualification only; no full-candidate acceptance, production promotion, rerun or renewed allowance',reviewer='mav_result_review',findings=[],all_computed_checks_passed=True,computed_checks=x['computed_checks'],finalization_computed_checks=checks,manual_review=dict(decision='accepted',basis='Independent numerical/work/memory source and report review documented in result-review.md; these judgments are not represented as mechanical checks',limitations=['Actual no-scope task unavailable; source reasoning only for that branch','Probe IR delegates to helper; no transitive helper/native code-size bound','Two-process local kernels, finite fixtures and pinned runtime; no end-to-end or sparse-backend performance proof','Aggregate allocation counters do not identify two old objects or prove retained/native memory bounds','MA-S-2 remains rejected48/52; Rational no-increase and complete-candidate obligations remain open']),sha256=bindings)
with (E/'result-review.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,computed_checks=len(x['computed_checks']),finalization_checks=len(checks),bindings=len(bindings),report_sha256=sha(report))))
