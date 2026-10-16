from pathlib import Path
E=Path(__file__).resolve().parent;O=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'
s=(O/'offline-tests-2.py').read_text().replace('offline-tests-2.json','offline-tests.json').replace('len(evidence.expected_names())==558','len(evidence.expected_names())==198').replace('output_membership558','output_membership198')
a=s.index("check('matched_factories'");b=s.index("check('new_phase_no_runtime'",a)
s=s[:a]+'''check('matched_factories','J._direct_lu_factor(F,B,backend,policy(backend)' in text and 'J._dynamic_bg_factor(B,backend,policy(backend))' in text)
check('no_accumulating_rows','push!(rows,row)' not in text and 'rows=Dict' not in text)
check('single_window_input_scan',text[text.index('function window'):text.index('# Untimed')].count('unchanged(f,source)')==1)
check('definitions_before_main',text.index('include("probe.jl")')<text.index('function main()') and text.rstrip().endswith('main()'))
'''+s[b:]
with (E/'offline-tests.py').open('x') as f:f.write(s)
s=(O/'prefix-tests.py').read_text().replace("['FT','SS','BG']","['BG']").replace("['normalized' if side=='candidate' else 'ordinary']*3","['normalized']*3").replace('cells=24,windows=480','cells=8,windows=160').replace('exact_residuals=11520','exact_residuals=3840').replace('len(result)==24','len(result)==8').replace('complete558files480windows','complete198files160windows').replace('windows=479','windows=159')
s=s.replace("(out/f'preflight-{cell}.toml').write_text(toml(pf))", """(out/f'preflight-{cell}.toml').write_text(toml(pf))
    states=[]
    for k,r in [(0,False)]+[(k,r) for k in range(1,9) for r in ([False,True] if k in (4,8) else [False])]:
     states.append(dict(step=k,refactored=r,equal=True,graphs=[100,100,100],capacity=16,live=2,arena_graph_bytes=1024,array_graph_bytes=[8]*15,requested_payload_bytes=1024,copy_arena_payload_bound=2048,history_length=0 if r or k==0 else (k-1)%4+1,counts=[2,0,0,0,2,0]))
    output=[[token(1.),token(2.)] if i%3!=2 else [token(1.),token(0.)] for i in range(24)]
    probe=dict(states=states,outputs=[output]*3,inputs_unchanged=True,constructions=3,refactors=6,updates=24,ftran=48,btran=24,copies=0,counts=[2,0,0,0,2,0])
    (out/f'probe-{cell}.toml').write_text(toml(probe))""")
s=s.replace("'started-1.toml','preflight-1.toml','window-1-1.toml'","'started-1.toml','preflight-1.toml','probe-1.toml','window-1-1.toml'")
s=s.replace("for p in list(out.glob('window-*')):p.unlink()","for p in list(out.glob('window-*')):p.unlink()\n (out/'probe-1.toml').unlink()")
s=s.replace("(out/'unknown').write_text('x')", """mutate('probe-1.toml',lambda d:d['states'][0].update(equal=False),'probe_false_state')
 mutate('probe-1.toml',lambda d:d['states'][0].update(capacity=-1),'probe_bad_capacity')
 mutate('probe-1.toml',lambda d:d.update(ftran=49),'probe_wrong_budget')
 mutate('probe-1.toml',lambda d:d.update(counts=[3,0,0,0,2,0]),'probe_wrong_counter')
 mutate('probe-1.toml',lambda d:d['outputs'][1][0].__setitem__(0,token(99.)),'probe_output_drift')
 # Signed zero is within residual tolerance but must fail the DIRECT bitwise oracle.
 mutate('window-1-2.toml',lambda d:d['outputs'][2].__setitem__(1,token(-0.)),'paired_signed_zero_mismatch')
 (out/'unknown').write_text('x')""")
with (E/'prefix-tests.py').open('x') as f:f.write(s)
print('New synthetic test sources prepared')
