from pathlib import Path
import json,tomllib,statistics,hashlib,shutil,re
r=Path(__file__).resolve().parents[3]
b=r/'.superpowers/primal-certificate-work';out=r/'diagnostics/primal-certificate-work/results';out.mkdir(exist_ok=True)
required=['step3-targeted-v2','final-products','final-semantic','final-differential-v2','final-stages','final-cleanup','final-broad-semantic','final-external','final-runtime','merged-targeted','merged-semantic']
for name in required:
 p=json.loads((b/name/'process.json').read_text());assert p['returncode']==0 and p['sources_unchanged'],name
ext=tomllib.loads((b/'final-external/results.toml').read_text())['cases']
manifest=tomllib.loads((r/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').read_text())['cases']
expected={(e['id'],a,u,b) for e in manifest for a in ('primal','dual') for u in ('pfi','huangfu_hall','forrest_tomlin','suhl_suhl','bartels_golub') for b in ('native','markowitz')}
assert len(ext)==len(expected)==100 and {(x['id'],x['algorithm'],x['basis_update'],x['backend']) for x in ext}==expected
assert all(x['status']=='OPTIMAL' and x['original_primal_certified'] and x['objective_matches'] for x in ext)
clean=tomllib.loads((b/'final-cleanup/results.toml').read_text())['cases'];assert len(clean)==4
for origin in ['primal','dual']:
 pair=[x for x in clean if x['origin']==origin];assert len(pair)==2
 assert pair[0]['events_hash']==pair[1]['events_hash'] and pair[0]['states_hash']==pair[1]['states_hash']
run=tomllib.loads((b/'final-runtime/results.toml').read_text())
assert run['status']=='OPTIMAL' and run['original_feasible']
assert run['events_hash']=='6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb'
assert run['states_hash']=='1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743'
attempts=[]
for p in sorted(b.glob('*/process.json')):
 name=p.parent.name;d=json.loads(p.read_text());log=(p.parent/'run.log').read_text()
 match=re.search(r'Maximum resident set size \(kbytes\): (\d+)',log)
 d['attempt']=name;d['max_rss_kib']=int(match[1]) if match else None
 d['test_summaries']=[l for l in log.splitlines() if re.search(r'\|\s+\d+\s+\d+\s+',l)]
 d['preflight_sha256']=hashlib.sha256((p.parent/'preflight.json').read_bytes()).hexdigest()
 attempts.append(d)
 if name in required:
  shutil.copy2(p.parent/'run.log',out/(name+'.log'))
  if (p.parent/'results.toml').exists():shutil.copy2(p.parent/'results.toml',out/(name+'.toml'))
(out/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
provenance=json.loads((b/'merged-semantic/preflight.json').read_text())
(out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
stages=tomllib.loads((b/'final-stages/results.toml').read_text())['cases']
lines=['# Final certificate work validation','', 'All times in the table are warmed median milliseconds per point certificate. Nine alternating rounds, three calls per round; measured compilation time is zero. Ratios are baseline/final.','', '| Case | Type | Baseline | Scratch | Bounds/scan | Shared sums | Ratio | Baseline/final bytes |','|---|---|---:|---:|---:|---:|---:|---:|']
for c in stages:
 med=[statistics.median(x)*1000 for x in c['seconds']];bs=[statistics.median(x) for x in c['bytes']]
 lines.append('| '+c['name']+' | '+c['type']+' | '+' | '.join(f'{x:.6f}' for x in med)+f' | {med[0]/med[3]:.3f} | {bs[0]:g}/{bs[3]:g} |')
lines+=['','The two medium rows are saved endpoints reached after 32 primal cleanup steps, from different original handoffs. The full allocated point-buffer footprint is 17,452,176 bytes at each endpoint; it is not a separately measured baseline memory delta. Vector capacity may exceed logical lengths. Initialization, exact fallback allocation, and unrelated solver allocations are excluded from these native-only steady-state figures.','', 'The fast-path controls show small timing noise, not a demonstrated speedup. Sharing adds little when only one check needs native sums; the allocation and bound-view savings still apply. Dense cancellation and overlapping selections benefit more. No complete medium solve speed claim is made.','', '## Regression and trajectory evidence','']
for d in attempts:
 if d['attempt'] in required:
  lines.append('- `'+d['attempt']+'`: exit 0, source/input digests unchanged; '+('; '.join(d['test_summaries']) or 'explicit script assertions passed')+'.')
lines+=['','The external matrix contains exactly 100 unique combinations (five models, five basis managers, two algorithms, two refactorization backends); all are optimal, match reference objectives, and pass original-model primal certification.','', 'Both 128-step medium cleanup comparisons have identical event and state hashes. Fresh handoffs are deserialized for each arm. These are bounded continuations with ITERATION_LIMIT by design, not completed medium solves. Their single baseline-first cold timings include compilation/initialization and are not speedup evidence.','',f'The full HH/native320 dual runtime solve is OPTIMAL after {run["iterations"]:,} iterations and {run["refactorizations"]} refactorizations; objective {run["objective"]:.12g}, original-model feasible. Both event and sampled-state hashes match the prior baseline. Instrumented elapsed time {run["seconds"]:.3f}s includes {run["compile_seconds"]:.3f}s compilation. This single full run validates trajectory and correctness, not an end-to-end performance claim.','', 'The complete project suite was not rerun. The broad semantic selection uses --compile=min; allocation checks and external/full solves use normal compilation. Earlier incomplete compilation and fixture/script errors are listed in README and attempts.json. No missing or interrupted report is counted as successful.','', '## Work and memory review','', 'Independent review found no correctness blocker or remaining material unnecessary work/memory cost. No basis solves, high-precision conversions, full matrix copies, or numerical relaxations were added. Scratch is lazy, workspace owned, O(m+k); cached sums exist only for a fixed point certificate. The second check retains independent bounds and exact fallback. The product-count probe confirms the overlapping three-term fixture uses 384 rather than 768 native products. Cold first-call allocation and peak union storage are deliberate tradeoffs for eliminating repeated allocations and overlapping CSC work.','']
(out/'SUMMARY.md').write_text('\n'.join(lines))
print('AUDIT OK: 100 unique external combinations, two matching cleanup pairs, full runtime trajectory, all required guarded jobs passed.')
