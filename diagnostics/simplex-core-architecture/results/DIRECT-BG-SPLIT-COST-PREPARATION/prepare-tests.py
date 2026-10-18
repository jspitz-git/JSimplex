from pathlib import Path
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION');O=E.parent/'DIRECT-BG-BLOCK-COST-PREPARATION'
p=E/'synthetic.py';t=p.read_text();t=t.replace('return dict(C=n,R=cap,','return dict(active_slack=0,bin_heads=[0]*32,column_heads=list(range(1,n+1)),column_tails=list(range(1,n+1)),extents=[[1,i,1,1,i,0,0] for i in range(1,n+1)],C=n,R=cap,');t=t.replace('return dict(complete=True,','return dict(schedules=["isolated prefix-test placeholder"],complete=True,');p.write_text(t)
p=E/'prefix-tests.py';t=p.read_text();t=t.replace("with tempfile.TemporaryDirectory(prefix='cost-prefix-') as td,patch.object(e,'rd',", "# This suite isolates output-prefix mechanics from the NEW structural schedule checker.\n# Storage/counter validation remains real. New schedule implementation is SOURCE ONLY.\nwith patch.object(e,'schedules_ok',lambda v:e.require(v==['isolated prefix-test placeholder'],'Prefix schedule placeholder')),tempfile.TemporaryDirectory(prefix='cost-prefix-') as td,patch.object(e,'rd',");p.write_text(t)
t=(O/'source-check.py').read_text().replace('BLOCK_COST_PROBE','SPLIT_COST_PROBE').replace('block-upper.jl','split-upper.jl').replace('block-bg.jl','split-bg.jl').replace('block-oracles.jl','split-oracles.jl').replace('_bgu_','_sbu_').replace('_block_bg','_split_bg').replace('_block_probe_counts','_split_probe_counts').replace('==238','==244')
t=t.replace("u=u.replace(j['allocator']['new'],j['allocator']['old'])", "for v in reversed(j['replacements']):\n ok(u.count(v['new'])==1,'replacement_'+str(len(checks)));u=u.replace(v['new'],v['old'])")
t=t.replace("unrename(o[len(a):],j['renames'])==a", "unrename(o[len(a):],j['renames'])==a+j['helper']")
t=t.replace("'save(\"growth.toml\",growth_probe())' in t and 'for c in 1:64'", "'save(\"growth.toml\",growth_probe())' in t and 'for c in 1:64'")
(E/'source-check.py').write_text(t)
t=(O/'freeze.py').read_text().replace('2026-10-16-direct-bg-block-upper','2026-10-18-direct-bg-split-free-blocks').replace("'negative-supplement.json']", "'negative-supplement.json','split-tests.json']")
(E/'freeze.py').write_text(t)
print('Prepared NEW Python tests and source verification; no tests executed yet')
