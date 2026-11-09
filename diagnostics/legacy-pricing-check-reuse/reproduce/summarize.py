"""Verify existing reports and summarize complete pairs without extrapolating missing coverage."""
import csv
import importlib.util
import json
import statistics
from pathlib import Path

spec=importlib.util.spec_from_file_location('runner',Path(__file__).with_name('run.py'))
run=importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
out=run.out
def read_json(p):
    return json.loads(p.read_text())
def write_csv(name,rows):
    if not rows:
        return
    with (out/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def main():
    pins=read_json(out/'sources.json')
    assert all(run.digest(Path(p))==h for p,h in pins.items())
    assert run.digest(run.model)==run.expected_sha
    provenance=read_json(out/'source-provenance.json')
    for rel,h in provenance['sources'].items():
        assert run.digest(run.root/rel)==h
    state=read_json(out/'status.json')
    skipped=read_json(out/'skipped.json') if (out/'skipped.json').exists() else []
    skipped_keys={(r['profile'],r['pricing'],r['job']) for r in skipped}
    processes=[]; reports=[]; pairs=[]; coverage=[]; verified={}; unresolved=[]
    for profile,pricing,name in run.schedule():
        folder=out/profile/pricing
        p=folder/(name+'.process.json')
        if not p.exists():
            if (profile,pricing,name) not in skipped_keys:
                unresolved.append([profile,pricing,name])
            continue
        process=read_json(p)
        start=read_json(folder/(name+'.started.json'))
        assert process['start']==start['start']<process['end'] and process['locks']>0
        assert process['exit']==0,(profile,pricing,name,process)
        processes.append((process['start'],process['end'],profile,pricing,name))
        report=folder/(name+'.toml')
        if name=='unit':
            assert run.load(report)['passed']
            continue
        if Path(str(report)+'.warmup-failure.toml').exists():
            continue
        assert process['report_sha256']==run.digest(report)
        d=run.load(report)
        run.final_check(d)
        reports.append(dict(profile=profile,pricing=pricing,job=name,status=d['status'],
            original_feasible=d['original_feasible'],message=d['message'],iterations=d['iterations'],
            refactors=d['refactors'],loop=d['loop'],seconds=d['seconds'],gc=d['gc'],
            compile=d['compile'],bytes=d['bytes'],allocations=d['allocations'],peak_rss_bytes=d['peak_rss_bytes'],
            mode_initial=d['mode_initial'],mode_refactors=d['mode_refactors']))
        if d['status']=='OPTIMAL':
            expected=run.compare(folder,name)
            assert read_json(folder/(name+'.comparison.json'))==expected
            verified['/'.join((profile,pricing,name))]=dict(report_sha256=run.digest(report),comparison=expected)
        if name=='shadow':
            a=run.load(Path(str(report)+'.audit.toml'))
            c=a['counts']
            n=sum(c.get(k,0) for k in ('finite_reused','from_last_pivot','driver_entry'))
            counts=a['pricing_counts']
            completed={q:sum(v for k,v in counts.items() if k.startswith('completed/'+q+'/'))
                       for q in ('dantzig','steepest_edge','devex')}
            coverage.append(dict(profile=profile,pricing=pricing,observed=True,
                completed_dantzig=completed['dantzig'],completed_dse=completed['steepest_edge'],completed_devex=completed['devex'],
                dse_to_devex_live=sum(s['from']=='steepest_edge' and s['to']=='devex' and not s['staged'] for s in a['switches']),
                dse_to_devex_staged_attempts=sum(s['from']=='steepest_edge' and s['to']=='devex' and s['staged'] for s in a['switches']),
                row_reused=c.get('row_reused',0),row_original=c.get('row',0),avoided_finite=n,
                original_full_finite=c['finite']-c.get('common_entry',0)-c.get('common_dse_weight',0),
                common_dse_weight=c.get('common_dse_weight',0),ftran_guards=c.get('direction',0)))
    for p,q in run.combinations:
        folder=out/p/q
        quartet=[folder/(a+'.'+str(i)+'.toml') for i in (1,2) for a in ('reference','candidate')]
        keys=[p+'/'+q+'/'+a+'.'+str(i) for i in (1,2) for a in ('reference','candidate')]
        if not all(k in verified for k in keys):
            continue
        data=[run.load(f) for f in quartet]
        if any(d['status']!='OPTIMAL' for d in data):
            continue
        deltas=[]
        for i in (1,2):
            r,c=data[(i-1)*2:i*2]
            delta=100*(c['loop']/r['loop']-1)
            deltas.append(delta)
            pairs.append(dict(profile=p,pricing=q,repeat=i,reference_loop=r['loop'],candidate_loop=c['loop'],
                delta_percent=delta,reference_solve=r['seconds'],candidate_solve=c['seconds'],
                reference_gc=r['gc'],candidate_gc=c['gc'],reference_bytes=r['bytes'],candidate_bytes=c['bytes'],
                reference_allocations=r['allocations'],candidate_allocations=c['allocations'],
                reference_compile=r['compile'],candidate_compile=c['compile'],
                reference_peak_rss_bytes=r['peak_rss_bytes'],candidate_peak_rss_bytes=c['peak_rss_bytes']))
        verified[p+'/'+q+'/timing']=dict(ratio_of_means_percent=100*((data[1]['loop']+data[3]['loop'])/(data[0]['loop']+data[2]['loop'])-1),
            mean_paired_percent=statistics.mean(deltas),deltas=deltas)
    processes.sort()
    assert all(a[1]<=b[0] for a,b in zip(processes,processes[1:]))
    expected=[j for j in run.schedule() if j not in skipped_keys]
    actual=[tuple(r[2:]) for r in processes]
    assert actual==expected[:len(actual)]
    write_csv('summary.csv',reports);write_csv('pairs.csv',pairs);write_csv('coverage.csv',coverage)
    complete=state['state']=='finished' and not unresolved
    result=dict(complete=complete,pins=len(pins),processes=len(processes),sequential=True,
        input_sha=run.expected_sha,verified=verified,coverage=coverage,skipped=skipped,unresolved=unresolved)
    name='final-verification.json' if complete else 'partial-verification.json'
    (out/name).write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Přebírání kontrol při pevném Dantzigu a DSE','',
        'Stav plánu: '+('dokončený' if complete else 'neúplný')+'.','',
        '| Správce | Pricing | První pár Δ | Obrácený pár Δ | Poměr průměrů Δ |','|---|---|---:|---:|---:|']
    for p,q in run.combinations:
        r=verified.get(p+'/'+q+'/timing')
        if r:
            lines.append(f"| {p} | {q} | {r['deltas'][0]:+.2f} % | {r['deltas'][1]:+.2f} % | {r['ratio_of_means_percent']:+.2f} % |")
    lines+=['','Kladná změna znamená delší duální smyčku. Průměry zahrnují jen úplné čtveřice optimálních, původně přípustných a přesně ověřených reportů. Kompilace se zahrnuje a vykazuje v tabulce. Dvě opakování a změny výkonu hostitele omezují přesnost.','',
        'Údaje o skutečném pricingu pocházejí z auditů. Počet completed vychází z post-pivot vstupu na živém workspace. Staged pivot události a cenové přechody se vykazují zvlášť v původních TOML. Absence DSE iterací nebo přechodu omezuje runtime pokrytí dané cesty. Cílené testy vynucují oba důvody DSE→Devex. Převzaté guardy se přepočítávají v auditu, časované běhy ověřují vlastní koncový stav.','',
        '[Jednotlivé běhy](summary.csv) · [Párové časy a prostředky](pairs.csv) · [Pokrytí pricingů a převzetí](coverage.csv) · [Vynechané úlohy](skipped.json)']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(complete=complete,processes=len(processes),pairs=len(pairs),unresolved=len(unresolved))))
if __name__=='__main__':
    main()
