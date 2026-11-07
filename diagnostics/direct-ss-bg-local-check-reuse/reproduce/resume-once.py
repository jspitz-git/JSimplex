"""Finish the three remaining jobs after the user authorized the single interrupted attempt."""
import csv
import fcntl
import os
import subprocess
import sys
import time
import json
from contextlib import ExitStack
from pathlib import Path
import run

root, out, suite = run.root, run.out, run.suite
archive = out/'environment-interruption-20261107'
jobs = [('suhl_suhl_normalized','reference','reference.2'),
        ('suhl_suhl_direct','candidate','candidate.2'),('suhl_suhl_direct','reference','reference.2')]

def main():
    with ExitStack() as stack:
        locks = []
        for p in sorted((root/'diagnostics').rglob('suite.lock')):
            if p.parent.name == 'results' and 'results' not in p.parent.parent.relative_to(root).parts:
                f = stack.enter_context(p.open())
                fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
                locks.append(f.fileno())
        pins = json.loads((out/'pins.json').read_text())
        manifest = json.loads((archive/'manifest.json').read_text())
        assert all(run.sha(archive/k) == v == run.sha(suite/k) for k,v in manifest.items())
        assert all(run.sha(root/k) == v for k,v in pins.items())
        assert run.sha(run.model) == run.read(run.prior(jobs[0][0]))['input_sha256']
        for m,a,n in run.jobs():
            if (m,a,n) in jobs:
                assert not (out/m/(n+'.process.json')).exists() and not (out/m/(n+'.toml')).exists()
            else:
                assert json.loads((out/m/(n+'.process.json')).read_text())['exit'] == 0
                run.verify(out/m,m,n)
        evidence = out/'authorized-resume-20261107'
        evidence.mkdir()
        m,_,n = jobs[0]
        run.create(evidence/'authorization.json',dict(start=time.time(),locks=len(locks),
            decision='Ano, jednou zopakovat přerušenou referenci a dokončit měření.',jobs=jobs,
            archive_sha=run.sha(archive/'manifest.json')))
        for suffix in ('.started.json','.log'):
            (out/m/(n+suffix)).rename(evidence/(n+suffix))
        for m,arm,n in jobs:
            assert all(run.sha(root/k) == v for k,v in pins.items())
            folder=out/m
            start=time.time()
            run.create(folder/(n+'.started.json'),dict(start=start,manager=m,arm=arm,job=n))
            report=folder/(n+'.toml')
            with (folder/(n+'.log')).open('x') as log, (folder/(n+'.cpu.csv')).open('x') as stats:
                cmd=['julia','--startup-file=no','--compiled-modules=existing','--project='+str(root),
                     str(suite/'reproduce/worker.jl'),m,arm,str(run.model),str(report)]
                child=subprocess.Popen(cmd,cwd=root,env=dict(os.environ,JULIA_NUM_THREADS='1',
                    OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),stdout=log,stderr=subprocess.STDOUT,pass_fds=locks)
                w=csv.writer(stats)
                w.writerow(('unix_time','user_ticks','system_ticks','last_vcpu','major_faults','minor_faults','running_ns','waiting_ns'))
                while True:
                    try:
                        code=child.wait(timeout=10)
                        break
                    except subprocess.TimeoutExpired:
                        # Read Linux accounting outside Julia. This interval only controls sampling.
                        try:
                            task=Path('/proc')/str(child.pid)
                            f=(task/'stat').read_text().rsplit(') ',1)[1].split()
                            sched=(task/'schedstat').read_text().split()
                            w.writerow([time.time(),f[11],f[12],f[36],f[9],f[7],*sched[:2]])
                            stats.flush()
                        except (FileNotFoundError,ProcessLookupError):
                            pass
            run.create(folder/(n+'.process.json'),dict(start=start,end=time.time(),exit=code,locks=len(locks),
                sha=run.sha(report) if report.exists() else None))
            if code: sys.exit(code)
            run.verify(folder,m,n)
            assert all(run.sha(root/k) == v for k,v in pins.items())
if __name__ == '__main__':
    main()
