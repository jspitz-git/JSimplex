from control import *
import guard
P=D.with_name('PRESOLVE-EXACT-CACHE');entry=rd(P/'host.json');a=rd(D/'analysis.json');h=host(rd(D/'posthost.json')['groups'])
checks=dict(original_pins=guard.pins_match(rd(P/'launch-pins.json')),pipeline_pins=guard.pins_match(rd(D/'launch-pins.json')),refs=h['head']==entry['refs']['head'] and h['master']==entry['refs']['master'],no_julia_full_groups_sessions=not h['matches'],source514=all(sha(R/p)==v for p,v in entry['master_identity'].items()),protected6=all(sha(p)==v for p,v in entry['protected'].items()),four_audits=all(rd(D/f'audit-{i}.json')['all_passed'] is True for i in range(1,5)),original_stopped=rd(P/'partial-result.json')['qualification_accepted'] is False and all(not(P/f'run-{i}').exists() for i in (2,3,4)),correctness=a['correctness_accepted'] is True,screen_rejected=a['performance_screen_accepted'] is False,combined_bound=a['inclusive_seconds']+rd(P/'partial-result.json')['elapsed_seconds']<=327)
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');checks['remote']=set(remote.splitlines())=={h['head']+'\trefs/heads/codex/simplex-core-architecture',h['master']+'\trefs/heads/master'}
allw=[w for i in range(1,5) for p in (D/f'run-{i}').glob('presolve-*.toml') for w in tomllib.loads(p.read_text())['windows']]
checks['320_windows224_measured']=len(allw)==320 and sum(w['measured'] for w in allw)==224
checks['compile_zero']=all(w['compile_seconds']==0 and w['recompile_seconds']==0 for w in allw if w['measured'])
checks['input_output_all']=all(w['outputs_equal'] and w['input_preserved'] for w in allw)
checks['exact_before_maps']=all(sha(x['preserved'])==x['sha256'] for x in rd(P/'continuation-map.json')['old_bindings'])
req(all(checks.values()),str(checks));save(D/'postcheck.json',dict(all_passed=True,checks=checks,host=h,remote=remote,measured_gc_windows=sum(w['measured'] and w['gc_seconds']>0 for w in allw),all_gc_windows=sum(w['gc_seconds']>0 for w in allw),combined_seconds=a['inclusive_seconds']+rd(P/'partial-result.json')['elapsed_seconds'],sha256={str(p):sha(p) for p in [D/'postcheck.py',D/'analysis.json',D/'admission.md',D/'admission.json',P/'partial-result.json',P/'continuation-map.json']}))
print('Postcheck',len(checks),'PASS; groups',len(h['groups']),'measured GC',sum(w['measured'] and w['gc_seconds']>0 for w in allw))
