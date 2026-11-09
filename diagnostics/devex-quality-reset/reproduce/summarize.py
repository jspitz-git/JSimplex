import csv,json,statistics
from pathlib import Path
import run
out=run.out

def write_csv(name,rows):
    if not rows: return
    with (out/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    run.verify_pins()
    for rel,h in run.read_json(out/'source-provenance.json')['sources'].items(): assert run.digest(run.root/rel)==h
    skipped=run.read_json(out/'skipped.json') if (out/'skipped.json').exists() else []
    skipkeys={(x['profile'],x['input'],x['job']) for x in skipped}
    jobs=list(run.schedule());processes=[];verified={};rows=[];coverage=[];outcomes=[];missing=[];pairs=[]
    for profile,inp,name in jobs:
        folder=out/profile/inp;proc=folder/(name+'.process.json');report=folder/(name+'.toml')
        if not proc.exists():
            if (profile,inp,name) not in skipkeys:missing.append([profile,inp,name])
            continue
        p=run.read_json(proc);started=run.read_json(folder/(name+'.started.json'))
        assert p['start']==started['start']<p['end'] and p['locks']>=2
        processes.append((p['start'],p['end'],profile,inp,name))
        warm=Path(str(report)+'.warmup-failure.toml')
        if not warm.exists(): assert p['report_sha']==run.digest(report)
        if inp=='unit':
            d=run.load(report)
            if name=='off-unit':
                log=(folder/(name+'.log')).read_text()
                assert p['exit']==1 and d['expected_original_failure'] is True and d['passed'] is False
                assert d['ordinary_pivot_completed'] is True and d['iterations']==1
                assert 'Test Failed' in log and 'Error During Test' not in log
            else:assert p['exit']==0 and d['passed'] is True
            continue
        assert p['exit']==0
        if warm.exists(): outcomes.append(dict(profile=profile,input=inp,job=name,**run.load(warm)));continue
        d=run.load(report);optimal=run.final_check(d,inp)
        if not optimal: outcomes.append(dict(profile=profile,input=inp,job=name,status=d['status'],message=d['message']))
        else:
            c=run.compare(folder,name);assert c==run.read_json(folder/(name+'.comparison.json'))
            verified[(profile,inp,name)]=d
        row={k:d[k] for k in ('profile','arm','status','message','original_feasible','iterations','refactors','objective','seconds','loop','gc','compile','bytes','allocations','peak_rss_bytes','certificate_calls','certificate_true','certificate_last','state_payload_bytes','weak_metadata_entries')}
        row.update(input=inp,job=name,quality_observed=d['quality_observed'])
        row.update(d['quality_counts']);rows.append(row)
        if inp=='runtime' and name.endswith('-audit'):
            a=run.load(Path(str(report)+'.audit.toml'))
            off=out/profile/inp/'off-audit.toml'
            ref=run.load(off)
            coverage.append(dict(profile=profile,arm=d['arm'],status=d['status'],observed=d['quality_observed'],
                iterations=d['iterations'],iteration_delta=d['iterations']-ref['iterations'],
                objective_delta=d['objective']-ref['objective'],**d['quality_counts']))
    for profile in run.profiles:
        for arm in ('passive','active'):
            keys=[(profile,'runtime',a+'.'+str(i)) for i in (1,2) for a in ('off',arm)]
            if not all(k in verified for k in keys):continue
            for i in (1,2):
                r,c=[verified[(profile,'runtime',a+'.'+str(i))] for a in ('off',arm)]
                pairs.append(dict(profile=profile,arm=arm,repeat=i,reference_seconds=r['seconds'],candidate_seconds=c['seconds'],
                    solve_delta_percent=100*(c['seconds']/r['seconds']-1),reference_loop=r['loop'],candidate_loop=c['loop'],
                    loop_delta_percent=100*(c['loop']/r['loop']-1),reference_iterations=r['iterations'],candidate_iterations=c['iterations'],
                    iteration_delta_percent=100*(c['iterations']/r['iterations']-1)))
    processes.sort();assert all(a[1]<=b[0] for a,b in zip(processes,processes[1:]))
    assert [tuple(p[2:]) for p in processes]==[j for j in jobs if j not in skipkeys][:len(processes)]
    complete=run.read_json(out/'status.json')['state']=='finished' and not missing
    write_csv('summary.csv',rows);write_csv('pairs.csv',pairs);write_csv('coverage.csv',coverage)
    timing=[]
    for profile in run.profiles:
        for arm in ('passive','active'):
            sample=[p for p in pairs if p['profile']==profile and p['arm']==arm]
            if len(sample)==2:
                timing.append(dict(profile=profile,arm=arm,
                    mean_solve_ratio_percent=100*(sum(p['candidate_seconds'] for p in sample)/sum(p['reference_seconds'] for p in sample)-1),
                    mean_loop_ratio_percent=100*(sum(p['candidate_loop'] for p in sample)/sum(p['reference_loop'] for p in sample)-1),repeats=sample))
    result=dict(complete=complete,processes=len(processes),verified_comparisons=len(verified),
        source_pins=len(run.read_json(out/'sources.json')),reference_pins=len(run.read_json(out/'references.json')),
        sequential=True,skipped=skipped,numerical_outcomes=outcomes,missing=missing,coverage=coverage,timing=timing)
    (out/('final-verification.json' if complete else 'partial-verification.json')).write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Kontrola Devex vah a obnova rámce','', 'Stav: '+('dokončeno' if complete else 'neúplné')+'.','',
        '| Správce | Rameno | Δ solve opakování1 | Δ solve opakování2 | Δ poměr průměrů solve | Δ poměr průměrů smyčky |',
        '|---|---|---:|---:|---:|---:|']
    for t in timing:
        lines.append(f"| {t['profile']} | {t['arm']} | {t['repeats'][0]['solve_delta_percent']:+.2f}% | {t['repeats'][1]['solve_delta_percent']:+.2f}% | {t['mean_solve_ratio_percent']:+.2f}% | {t['mean_loop_ratio_percent']:+.2f}% |")
    lines+=['','Záporná změna znamená kratší čas. Jen úplné optimální čtveřice ověřené proti vlastnímu auditu. Dvě opakování omezují průkaznost malých změn. Kompilace je zahrnutá, neodečítá se.','',
        'Passive/off musí mít totožné původní události, guardy, vzorky i endpoint. Active může změnit trajektorii; nižší počet iterací není kernel speedup. Původní feasibility i skutečná původní optimality certificate jsou samostatné podmínky přijetí.','',
        'Off nesbírá ukazatel kvality: nuly jeho čítačů neznamenají nulu původních obnov rámce. Ukazatel sleduje pouze vybraný řádek a není certifikátem všech Devex vah. Práh9 je experimentální. Runtime audit přepočítává ukazatel, jeho čas není benchmark. Weak-key metadata neudržují workspace silnou referencí. Velikost stavu nezahrnuje obal slovníku; peak RSS zahrnuje warmup a následné kontroly, není retained memory.','',
        '[Všechny časy a prostředky](summary.csv) · [Párové změny](pairs.csv) · [Pokrytí a změna trajektorie](coverage.csv) · [Vynechané](skipped.json)']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(complete=complete,processes=len(processes),comparisons=len(verified),pairs=len(pairs),missing=len(missing))))
if __name__=='__main__': main()
