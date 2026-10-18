#!/usr/bin/env python3
"""One-shot offline arithmetic/evidence checks; never import project/checker code."""
import hashlib, json, pathlib, tomllib
R=pathlib.Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PLAN'
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-COST-PREPARATION'
paths=[R/'AGENTS.md',R/'docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md',R/'docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md',R/'diagnostics/direct-bg-block-upper/reproduce/block-upper.jl',R/'diagnostics/direct-bg-block-upper/reproduce/block-bg.jl',P/'MEMORY-WORK.md',P/'probe-upper.jl',P/'probe.jl',P/'runs/cost1-300/audit.json',Q/'author-check.json',Q/'host.json']
paths += [R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-COST-QUALIFICATION'/name for name in ('REPORT.md','result-review.md')]
paths += [P/f'runs/cost1-300/output/probe-{i}.toml' for i in (1,5)]
source={str(p.relative_to(R)):p.read_bytes() for p in paths}
checks={}
checks['six_class_target_geometry']=all(next(c for c in (1,2,4,8,16,32) if c>=r)>=r for r in range(1,33))
checks['all_target_donor_partitions']=all(t+(d-t)==d and 1<=d-t<=31 for t in (1,2,4,8,16) for d in range(t+1,33))
checks['four_request_geometry']=32//4==8 and 8-1==7 and (256//4-256//32)*28==1568
checks['core_fixed_payload']=32*4+33*(8+4+4)==656
checks['append_payload']=256*(8+4+4)==4096
# Exact imported full-tail initial capacities 1..31 then successive power classes.
copy_totals={}
for initial in range(1,32):
    old=initial;copied=0
    while old<32:
        copied+=old
        old=next(c for c in (1,2,4,8,16,32) if c>old)
    copy_totals[str(initial)]=copied
checks['monotone_tail_copy_bound']=max(copy_totals.values())==31
saved={}
for i,expected in ((1,(63,63,1087,66)),(5,(191,191,3263,194))):
    data=tomllib.loads(source[str((P/f'runs/cost1-300/output/probe-{i}.toml').relative_to(R))].decode())
    a,b=data['states'][:2];sa,sb=a['storage'],b['storage']
    observed=(sa['C'],sa['live'],sb['C'],sb['live'])
    checks[f'saved_probe_{i}_capacity']=observed==expected
    saved[str(i)]={'initial':{k:sa[k] for k in ('C','live','K','D','S')},'step1':{k:sb[k] for k in ('C','live','K','D','S','free_capacity')},'active_slack':sb['C']-sb['live']-sb['free_capacity'],'requested_payload_delta':b['counts']['requested_payload_bytes']-a['counts']['requested_payload_bytes']}
checks['sparse96_slack_and_request']=saved['5']['active_slack']==2817 and saved['5']['step1']['free_capacity']==252 and saved['5']['requested_payload_delta']==60180
checks['sparse96_request_breakdown']=12*4096==49152 and 28*(144+216)==10080 and 24*sum((2,3,4,6,9,13))==888 and 49152+10080+888+60==60180
out={'scope':'split free block BG plan','kind':'offline arithmetic and saved-data checks only','all_passed':all(checks.values()),'checks':checks,'monotone_initial_tail_copied_tuples':copy_totals,'saved_probe_extracts':saved,'readtime_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in source.items()},'executed_source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'limitations':['No candidate exists or is tested','No Julia/parser/import/compile/numerical experiment','No original checker or audit executed','Saved original audit is bound as evidence, not rerun','Arithmetic checks are not allocator implementation verification']}
with (Q/'reviewer-check-v1.json').open('x') as f: json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':checks,'output':str(Q/'reviewer-check-v1.json')}))
assert out['all_passed']
