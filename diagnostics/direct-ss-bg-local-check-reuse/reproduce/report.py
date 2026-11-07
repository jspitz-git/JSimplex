"""Independently verify chronological pairing, publications, guard traces and each own endpoint."""
import csv
import hashlib
import json
import statistics
import struct
import subprocess
import sys
import tomllib
from pathlib import Path

suite=Path(__file__).resolve().parents[1]
root=suite.parents[1]
out=suite/'results'
variants=('suhl_suhl_direct','suhl_suhl_normalized','bartels_golub_direct','bartels_golub_normalized')
baseline='00068f59'
def meta(p): return json.loads(p.read_text())
def load(p): return tomllib.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_pins():
    pins=meta(out/'pins.json')
    # Optional replay after integration: the audited experiment predates the common gate hook.
    for name,value in pins.items():
        if name=='src/dual_simplex.jl' and sha(root/name)!=value:
            old=subprocess.check_output(['git','show',baseline+':'+name],cwd=root)
            assert hashlib.sha256(old).hexdigest()==value
        else:
            assert sha(root/name)==value,name
    return len(pins)

def verify(v):
    d=out/v
    alg,mode=v.rsplit('_',1)
    archive=load(root/f'diagnostics/runtime-full-chain-comparison/ss-bg-breakdown/results/jsimplex-{v}-160-repeat1.toml')
    ft=load(root/f'diagnostics/direct-ft-highs-iteration/results/{mode}.toml')
    ref=load(d/'reference-audit.toml')
    order=[]; observations=[]; modes=[]; hashes={}; compile_s={}
    for name in ('unit','reference-audit','shadow','reference.1','candidate.1','candidate.2','reference.2'):
        proc=meta(d/(name+'.process.json'))
        start=meta(d/(name+'.started.json'))
        assert proc['exit']==0 and proc['locks']>0 and start['start']==proc['start']<proc['end']
        order.append((proc['start'],proc['end'],v,name))
        if name=='unit':continue
        p=d/(name+'.toml')
        a=load(p)
        hashes[p.name]=sha(p);compile_s[name]=a['compile']
        assert hashes[p.name]==proc['sha']
        assert a['variant']==v and a['mode']==mode and a['status']==archive['status']=='OPTIMAL'
        assert a['original_feasible'] and a['threads']==a['blas_threads']==1 and a['arch']=='aarch64'
        assert a['input_sha']==archive['input_sha256'] and a['options']==ft['options'].replace(':forrest_tomlin',':'+alg)
        assert int(a['objective_bits'],16)==int.from_bytes(struct.pack('>d',archive['objective']),'big')
        assert a['iterations']==archive['iterations'] and a['refactors']==archive['refactorizations']
        assert a['mode_initial']+a['mode_refactors']==a['refactors']+1==archive['factory_modes'][mode]
        assert all(a[k]==ref[k] for k in ('steps','entries','mode_initial','mode_refactors','primal_sha','objective_bits','options'))
        if name in ('shadow','reference-audit'):
            audpath=d/(name+'.toml.audit.toml')
            hashes[audpath.name]=sha(audpath)
            rows=load(audpath)['modes']
            assert len(rows)==1+a['refactors'] and rows[0]['site']=='initial'
            assert sum(r['site']=='initial' for r in rows)==a['mode_initial']
            assert sum(r['site']=='refactor' for r in rows)==a['mode_refactors']
            assert all(r['dimension']>0 and r['mode']==mode and (mode=='direct' or r['unit_upper']) for r in rows)
            modes.extend(dict(variant=v,arm=name,sequence=i,**r) for i,r in enumerate(rows,1))
    b,s=(load(d/(x+'.toml.audit.toml')) for x in ('reference-audit','shadow'))
    c=s['counts']
    assert b['sha256']==s['sha256'] and b['modes']==s['modes']
    assert all(c[k]==val for k,val in b['counts'].items())
    assert all(c[k]>0 for k in ('row_reused','finite_reused','driver_entry','from_last_pivot'))
    n=sum(c[k] for k in ('finite_reused','driver_entry','from_last_pivot'))
    for i in (1,2):
        a,bm=(load(d/f'{arm}.{i}.toml') for arm in ('reference','candidate'))
        for k in ('loop','seconds','gc','bytes'):
            observations.append(dict(variant=v,repeat=i,metric=k,reference=a[k],candidate=bm[k],delta_percent=100*(bm[k]/a[k]-1)))
    timing={}
    for k in ('loop','seconds'):
        rs=[r for r in observations if r['metric']==k]
        timing[k]=dict(ratio_of_means_delta_percent=100*(sum(r['candidate'] for r in rs)/sum(r['reference'] for r in rs)-1),
            mean_paired_delta_percent=statistics.mean(r['delta_percent'] for r in rs))
    result=dict(trace_sha256=b['sha256'],counts=c,avoided_full_finite=n,original_full_finite=c['finite']-c.get('common_entry',0),
        endpoint={k:ref[k] for k in ('iterations','steps','refactors','mode_initial','mode_refactors','status','original_feasible','objective_bits','primal_sha')},
        fallback=0,timing=timing,compile_seconds=compile_s,hashes=hashes)
    return result,observations,modes,order

def main():
    selected=sys.argv[1:] or variants
    pins=verify_pins()
    results={}; timings=[]; histories=[]; order=[]
    for v in selected:
        result,r,h,o=verify(v)
        results[v]=result;timings.extend(r);histories.extend(h);order.extend(o)
    order.sort()
    assert all(a[1]<=b[0] for a,b in zip(order,order[1:]))
    if sys.argv[1:]:
        print(json.dumps({v:r['timing'] for v,r in results.items()},indent=2))
        return
    bench=[(v,n) for _,_,v,n in order if '.' in n]
    first=[(v,a) for v in variants for a in ('reference','candidate')]
    assert bench==[(v,a+'.1') for v,a in first]+[(v,a+'.2') for v,a in reversed(first)]
    for name,rows in (('factor-modes.csv',histories),('comparison.csv',timings)):
        with (out/name).open('w') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    summary = dict(revision=baseline, pins=pins, processes=len(order), sequential=True,
                   reversed_second_repeat=True, results=results)
    if (out/'authorized-resume-20261107').is_dir():
        interrupted = meta(out/'environment-interruption.json')
        archive = out/'environment-interruption-20261107'
        manifest = meta(archive/'manifest.json')
        authorization = meta(out/'authorized-resume-20261107/authorization.json')
        assert authorization['archive_sha'] == sha(archive/'manifest.json')
        assert all(sha(archive/k) == value for k,value in manifest.items())
        for m,name in interrupted['completed']:
            for original in (archive/'results'/m).glob(name+'.*'):
                assert sha(original) == sha(out/m/original.name)
        summary['interruption'] = dict(one_authorized_replacement=True,
            preserved_completed_jobs=len(interrupted['completed']), checked_archive_files=len(manifest),
            missing_original_numerical_report=True, job=authorization['jobs'][0],
            timing_limit='Druhá normalizovaná reference SS a oba přímé běhy SS druhého páru proběhly po obnovení.')
    integration = out/'integration'
    if (integration/'verification.json').exists():
        actual = meta(integration/'verification.json')
        assert set(actual) == set(variants) | {'forrest_tomlin_direct','forrest_tomlin_normalized'}
        assert all(sha(Path(k)) == v for k,v in meta(integration/'sources.json').items())
        last_benchmark_end = order[-1][1]
        for v,comparison in actual.items():
            stem = integration/v
            assert meta(stem.with_suffix('.comparison.json')) == comparison
            proc = meta(stem.with_suffix('.process.json'))
            assert proc['exit'] == 0 and last_benchmark_end < meta(stem.with_suffix('.started.json'))['start'] < proc['end']
            last_benchmark_end = proc['end']
            assert sha(stem.with_suffix('.toml')) == comparison['report_sha256']
            assert sha(stem.with_suffix('.toml.audit.toml')) == comparison['audit_sha256']
            mode = v.rsplit('_',1)[-1]
            refdir = root/'diagnostics/direct-ft-local-check-reuse/results'/mode if v.startswith('forrest_tomlin') else out/v
            assert sha(refdir/'shadow.toml') == comparison['reference_sha256']
            assert sha(refdir/'shadow.toml.audit.toml') == comparison['reference_audit_sha256']
            endpoint = load(stem.with_suffix('.toml'))
            assert all(endpoint[k] == value for k,value in comparison['endpoint'].items())
            ref = load(refdir/'shadow.toml.audit.toml')
            aud = load(stem.with_suffix('.toml.audit.toml'))
            assert endpoint['status'] == 'OPTIMAL' and endpoint['original_feasible']
            assert aud['sha256'] == ref['sha256'] and aud['counts'] == ref['counts'] and aud['modes'] == ref['modes']
        summary['integrated_audits'] = dict(verified=list(actual), sequential=True,
            verification_sha256=sha(integration/'verification.json'))
    (out/'final-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__': main()
