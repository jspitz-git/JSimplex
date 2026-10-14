"""Independent stored-data review. Never imports or executes diagnostic scripts.
Saved before its only invocation. Only exclusive new review-check.json is written.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import statistics
import tomllib

R = Path.cwd()
B = R / 'diagnostics/simplex-core-architecture'
D = B / 'results/MA-Y-FALLBACK'
X = B / 'results/MA-X'
checks = {}
bindings = {}
def digest(path):
    p = Path(path)
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    value = h.hexdigest()
    bindings[str(p)] = value
    return value
def read(path):
    digest(path)
    return json.loads(Path(path).read_text())
def toml(path):
    digest(path)
    return tomllib.loads(Path(path).read_text())
def check(name, condition):
    checks[name] = bool(condition)
def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)
def mid(items):
    values = sorted(items)
    assert len(values) == 7
    return values[3]

analysis = read(D/'analysis.json')
launch = read(X/'pins.json')['inventory']
check('all36_readtime_bindings', len(analysis['readtime_pins']) == 36 and all(digest(p) == v['sha256'] and str(Path(p).resolve()) == v['resolved'] for p,v in analysis['readtime_pins'].items()))
pinned = [(p,v) for p,v in analysis['readtime_pins'].items() if v['launch_pinned']]
check('all13_launch_pins', len(pinned) == 13 and all(v['sha256'] == launch[p]['sha256'] and v['resolved'] == launch[p]['resolved'] for p,v in pinned))
check('launch_flag_membership', all(v['launch_pinned'] == (p in launch) for p,v in analysis['readtime_pins'].items()))
check('analysis20checks_and_rejection', len(analysis['checks']) == 20 and all(analysis['checks'].values()) and analysis['qualification_accepted'] is False)
native = analysis['historical_native_binding']
s4 = read(native['source'])['sha256']
check('native_binary_and3_saved_assemblies', len(native['assemblies']) == 3 and digest(native['binary']) == native['sha256'] == launch[native['binary']]['sha256'] == s4[native['binary']] and all(digest(p) == s4[p] for p in native['assemblies']))
entry = read(D/'entry.json')
check('entry12_recorded_checks', len(entry['checks']) == 12 and all(entry['checks'].values()) and all(digest(p) == h for p,h in entry['sha256'].items()))
host = read(D/'host.json')
check('source514_protected6_unchanged', len(host['master_identity']) == 514 and len(host['protected']) == 6 and all(digest(R/p) == h for p,h in host['master_identity'].items()) and all(digest(p) == h for p,h in host['protected'].items()))
check('entry_host_identity176', host['refs']['head'] == 'db4f50c7aca3d3b243b6deaeccbf64e7df8c3a5c' and host['refs']['master'] == '6f68e24e8ddac42b948da8fcc2d636c010751194' and len(set(host['groups'])) == 176 and host['matches'] == [])
continuation = read(D/'continuation-map.json')['old_bindings']
check('six_beforecopy_bindings', len(continuation) == 6 and all(digest(row['preserved']) == row['sha256'] == read(row['source'])['sha256'][row['path']] for row in continuation))
publication = read(B/'results/MA-Y/publication.json')
check('old_publication74_unchanged', len(publication['sha256']) == 74 and all(digest(p) == h for p,h in publication['sha256'].items()))
fixtures = toml(B/'results/MA-R/fixtures.toml')['cost_cases']
controls = {f['id']: f for f in fixtures if not f['eligible']}
check('fixture52_control16', len(fixtures) == 52 and len(controls) == 16)
stored_pairs = {(p['process'],p['id'],p['pair']): p for p in analysis['paired_rows']}
stored_cases = {(c['process'],c['id']): c for c in analysis['case_medians']}
allpairs = []
allcases = []
failures = []
for process in (1,2,3):
    raw = toml(X/f'run-{process}/raw.toml')
    journal = toml(X/f'run-{process}/partial-windows.toml')['records']
    oldaudit = read(X/f'audit-{process}.json')
    audits = {c['id']: c for c in oldaudit['process_costs']}
    assert [c['id'] for c in raw['costs']] == [c['id'] for c in fixtures]
    expected_journal = []
    for c in raw['costs']:
        for w in c['windows']:
            location = "cost/{}/{}/{}".format(c['id'],w['pair'],1 if w['side']=='reference' else 2)
            expected_journal.extend([{'kind':'whole-metrics','location':location,'window':{k:v for k,v in w.items() if k not in ('output','preserved')}},{'kind':'whole-complete','location':location,'window':w}])
    check(f'process{process}_all2080_journal_records_order_content', journal == expected_journal and len(journal) == 2080)
    for ci,c in enumerate(raw['costs'],1):
        if c['id'] not in controls:
            continue
        assert c['eligible'] is False and len(c['windows']) == 20
        pairs = []
        for pair in range(1,11):
            windows = c['windows'][2*(pair-1):2*pair]
            assert [w['order'] for w in windows] == [1,2]
            assert [w['side'] for w in windows] == (['reference','candidate'] if (process+ci+pair)%2==0 else ['candidate','reference'])
            byside = {w['side']:w for w in windows}
            r,t = byside['reference'],byside['candidate']
            recorded = stored_pairs[process,c['id'],pair]
            for w in windows:
                assert w['pair'] == pair and w['calls'] == 4
                assert w['phase'] == ('warm' if pair<=3 else 'measured')
                assert w['output'] == c['expected'] and w['preserved'] is True
                assert all(w[k] == v for k,v in recorded[w['side']].items())
                if pair>3:
                    assert w['compile_seconds'] == w['recompile_seconds'] == 0
            delta = t['bytes']-r['bytes']
            events = t['events']-r['events']
            assert recorded['case_index'] == ci and recorded['phase'] == r['phase']
            assert recorded['order'] == ('RC' if r['order']==1 else 'CR')
            assert recorded['byte_delta'] == delta and recorded['event_delta'] == events
            assert close(recorded['paired_ratio'],t['seconds']/r['seconds'])
            assert close(recorded['time_delta_us'],(t['seconds']-r['seconds'])*250000)
            assert recorded['outputs_equal_preserved'] is True
            p = {'process':process,'id':c['id'],'pair':pair,'reference':r,'candidate':t,'delta':delta,'events':events,'order':recorded['order']}
            allpairs.append(p)
            if pair>3:
                pairs.append(p)
        medians = {side:{metric:mid(p[side][metric] for p in pairs) for metric in ('seconds','bytes','events')} for side in ('reference','candidate')}
        rt,ct = (medians[side]['seconds']/4 for side in ('reference','candidate'))
        gates = {'time':ct-rt<=max(rt*.10,.4e-6),'bytes':medians['candidate']['bytes']<=medians['reference']['bytes'],'events':medians['candidate']['events']<=medians['reference']['events']}
        result = stored_cases[process,c['id']]
        old = audits[c['id']]
        assert result['gates'] == gates and result['original_pass'] == old['pass'] == all(gates.values())
        assert close(result['time_allowance_seconds'],max(rt*.10,.4e-6))
        assert close(result['paired_ratio_median'],mid(p['candidate']['seconds']/p['reference']['seconds'] for p in pairs))
        assert result['paired_byte_delta_median'] == mid(p['delta'] for p in pairs)
        assert close(old['ratio'],result['paired_ratio_median'])
        for side in ('reference','candidate'):
            saved = result['sides'][side]
            assert close(saved['seconds_per_call'],medians[side]['seconds']/4) and close(old[side+'_seconds_per_call'],saved['seconds_per_call'])
            for metric in ('bytes','events'):
                assert saved[metric] == medians[side][metric] == old[side+'_'+metric]
            for metric,label in [('seconds','time'),('bytes','byte')]:
                rank = [p['pair'] for p in sorted(pairs,key=lambda row:row[side][metric])]
                assert saved[label+'_rank_pairs'] == rank and saved[label+'_median_pair'] == rank[3]
        allcases.append(result)
        if not all(gates.values()):
            failures.append({'process':process,'id':c['id'],'gates':gates})
    check(f'process{process}_controls_rows_ranks_medians_audit', True)
check('all480_pairs336_measured48_cases', len(allpairs)==len(stored_pairs)==480 and sum(p['pair']>3 for p in allpairs)==336 and len(allcases)==len(stored_cases)==48)
check('only_two_original_failed_predicates', failures == analysis['original_failures'] == [{'process':3,'id':'fallback/BigFloat/transpose','gates':{'time':False,'bytes':True,'events':True}},{'process':3,'id':'fallback/Rational{BigInt}/forward','gates':{'time':True,'bytes':False,'events':True}}])
measured = [p for p in allpairs if p['pair']>3]
for category,predicate in [('scoped_BigFloat',lambda p:p['id'].startswith('fallback/BigFloat/')),('Rational',lambda p:'Rational' in p['id']),('Float64',lambda p:'Float64' in p['id']),('small_BigFloat',lambda p:p['id'].startswith('small/'))]:
    ps = [p for p in measured if predicate(p)]
    ds = [p['delta'] for p in ps]
    summary = {'pairs':len(ps),'positive':sum(d>0 for d in ds),'negative':sum(d<0 for d in ds),'zero':sum(d==0 for d in ds),'min_byte_delta':min(ds),'max_byte_delta':max(ds),'event_deltas':sorted(set(p['events'] for p in ps)),'orders':dict(Counter(p['order'] for p in ps)),'gc_pairs':sum(p['reference']['gc_seconds']>0 or p['candidate']['gc_seconds']>0 for p in ps)}
    check(category+'_summary',summary==analysis['summaries'][category])
rat = [p for p in measured if 'Rational' in p['id']]
no_gc = [p for p in rat if p['reference']['gc_seconds']==p['candidate']['gc_seconds']==0]
check('Rational_noGC41_range_and_allFTRAN',len(no_gc)==41 and min(p['delta'] for p in no_gc)==-560 and max(p['delta'] for p in no_gc)==416 and all(p in no_gc for p in rat if p['id'].endswith('/forward')))
check('Rational16byte_multiples',all(p['delta']%16==0 for p in rat))
big3 = [p for p in measured if p['process']==3 and p['id']=='fallback/BigFloat/transpose']
rat3 = [p for p in rat if p['process']==3 and p['id'].endswith('/forward')]
check('report_BigFloat_all7_table', [round(p['reference']['seconds']*250000,3) for p in big3]==[356.350,351.175,290.550,299.575,7091.650,247.675,249.250] and [round(p['candidate']['seconds']*250000,3) for p in big3]==[455.375,351.150,279.525,386.425,360.425,249.825,251.075])
check('report_BigFloat_GC_pair8_only',[(p['pair'],p['reference']['gc_seconds'],p['candidate']['gc_seconds']) for p in big3 if p['reference']['gc_seconds'] or p['candidate']['gc_seconds']]==[(8,.0171974,0)])
check('report_Rational_all7_table',[(p['reference']['bytes'],p['candidate']['bytes']) for p in rat3]==[(3247392,3247440),(3247312,3247728),(3247520,3247568),(3247312,3247408),(3247408,3247360),(3247376,3247360),(3247328,3247344)] and all(p['reference']['events']==p['candidate']['events']==74525 for p in rat3))
check('no_pooled_output',not (X/'aggregate.json').exists())
report = B/'MA-DENSELU-COMPLETE-FALLBACK-ANALYSIS.md'
digest(report)
digest(Path(__file__).resolve())
for row in continuation:
    bindings.pop(row["path"], None)  # Live continuation is reviewed separately after this review.
output = {'accepted':all(checks.values()),'qualification_accepted':False,'scope':'Independent stored-evidence verification only; no original script execution/import, Julia, new measurements, numerical experiments, native disassembly, or pooled acceptance.','checks':checks,'failures':failures,'sha256':bindings}
with (D/'review-check.json').open('x') as stream:
    json.dump(output,stream,indent=2)
    stream.write('\n')
print(json.dumps({'accepted':output['accepted'],'checks':len(checks),'failed_checks':[k for k,v in checks.items() if not v],'bindings':len(bindings)},indent=2))
