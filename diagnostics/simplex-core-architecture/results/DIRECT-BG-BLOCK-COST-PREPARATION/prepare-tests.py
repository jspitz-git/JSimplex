from pathlib import Path
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-COST-PREPARATION');O=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION'
p=E/'offline-tests.py';t=(O/'offline-tests-reviewed.py').read_text().replace('analysis_reviewed','analysis').replace('evidence_reviewed','evidence').replace('control_reviewed','control').replace('offline-tests-reviewed.json','offline-tests.json').replace('_dynamic_bg','_block_bg').replace('output_membership198','output_membership199').replace('==198','==199');p.write_text(t)
t=(O/'prefix-tests-reviewed.py').read_text().replace('evidence_reviewed','evidence').replace('control_reviewed','control').replace('prefix-tests-reviewed.json','prefix-tests.json')
t=t.replace('checks={}','from synthetic import storage, counters, growth\nchecks={}')
t=t.replace('cell=0\n for fixture',"cell=0\n (out/'growth.toml').write_text(toml(growth()))\n for fixture")
a=t.index('     states.append(dict(');b=t.index('\n    output=',a)
t=t[:a]+"     states.append(dict(step=k,refactored=r,equal=True,graphs=[10000]*3,storage=storage(2),history_length=0 if r or k==0 else (k-1)%4+1,counts=counters()))"+t[b:]
t=t.replace('counts=[2,0,0,0,2,0]','counts=counters()').replace('complete198files160windows','complete199files160windows').replace('exact_residuals=3840','exact_residuals=4416').replace('exact_residuals=72','exact_residuals=144')
t=t.replace("d['states'][0].update(capacity=-1)","d['states'][0]['storage'].update(C=-1)")
t=t.replace("d.update(counts=[3,0,0,0,2,0])","d['counts'].update(splits=1)")
t=t.replace("e.BASE|{'started-1.toml'","e.BASE|{'growth.toml','started-1.toml'")
t=t.replace("check('no_phase_runs'", "check('no_phase_runs'")
# extra module schema and overflow refusals before prefix pruning
at=" (out/'unknown').write_text('x')"
add=""" mutate('raw.toml',lambda d:d['loaded'].update(Test='/unexpected/Test.jl'),'extra_Test_loaded_key')
 mutate('raw.toml',lambda d:d['loaded'].pop('TOML'),'missing_loaded_key')
 mutate('raw.toml',lambda d:d['loaded'].update(JSimplex='/wrong/module.jl'),'wrong_loaded_path')
 mutate('probe-1.toml',lambda d:d['states'][0]['storage']['arrays'][0].update(backing_length=2**63),'backing_integer_overflow')
 mutate('probe-1.toml',lambda d:d['states'][0]['storage']['arrays'].pop(),'missing_row_array')
 mutate('growth.toml',lambda d:d['states'][5].update(row_capacity=7),'growth_wrong_reserve')
 mutate('growth.toml',lambda d:d['counts'].update(row_copied_bytes=0),'growth_missing_copy_count')
"""
t=t.replace(at,add+at);(E/'prefix-tests.py').write_text(t)
(E/'prepare-tests.py').write_text(Path(__file__).read_text())
