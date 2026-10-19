"""New read-only source/lineage checks; no Julia and no old script execution."""
from pathlib import Path
import json,hashlib,sys,re,ast
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
checks={}
def check(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
c.validate_environment();c.validate_sources();c.validate_probe();c.validate_typed();c.validate_qualification();check('current_environment_sources_stage_runtime_and_accepted_qualifications',True)
copy=c.rd(D/'copied-files.json');check('all_exact_copies',all(c.sha(D/n)==v['sha256']==c.sha(v['source']) for n,v in copy.items()))
p=(D/'panel.jl').read_text();fp=(D/'panel-fault.jl').read_text()
for name,s in [('normal',p),('fault',fp)]:
 check(name+'_one_immutable_constant',s.count('const _BGB_ZERO_COUNTS = ntuple(_ -> 0, Val(20))')==1 and s.count('_BGB_ZERO_COUNTS')==4)
 check(name+'_distinct_mutable_counter', 'mutable struct BGPanelCounts\n    values::NTuple{20,Int}\nend' in s and 'BGPanelCounts() = BGPanelCounts(_BGB_ZERO_COUNTS)' in s)
t=(D/'panel-tests.jl').read_text();check('qualified_typed_repair_bytes',c.sha(D/'panel-tests.jl')=='15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910')
check('eight_added_sites',all(t.count('@check "P'+str(i).zfill(3)+'"')==1 for i in range(95,103)))
check('zero_counters_and_preservation',all(x in t for x in ['p011.bytes == 0','p011.events == 0','p011.consumed_bytes == 0','p011.consumed_events == 0','p011.values_unchanged','p011.owners_unchanged']))
sites=c.rd(D/'assertion-sites.json');check('exact168sites',set(sites)=={f'P{i:03d}' for i in range(1,103)}|{f'L{i:03d}' for i in range(1,41)}|{f'N{i:03d}' for i in range(1,27)})
check('sites_actual_source_lines',all(v['source']==(D/v['file']).read_text().splitlines()[v['line']-1].strip() for v in sites.values()))
s=(D/'driver.jl').read_text();main=s.index('function main()');check('all_includes_before_main',all(m.start()<main for m in re.finditer(r'include\(',s)))
check('no_dispatch_workaround',not any(x in s for x in ['invokelatest','eval(','@eval']))
check('one_typed_module_include',s.count('include("panel-tests.jl")')==1 and 'helpers.jl' not in s and 'p011_probe(' not in s)
check('fixed_order',s.index('measured_unit!(BGBlockedPanelTests')<s.index('measured_unit!(BGBlockedLifecycleTests')<s.index('for f in fixtures'))
check('only_red_stream_routing','reference_route=RED' in s and 'PHASE in ("red300","green300")' in s)
check('raw_before_exit',s.index('save("raw.toml",raw)')<s.index('exit(valid'))
check('unit_before_unexpected_stop',s.index('save("unit-$index.toml"')<s.index('Unexpected unit failure'))
check('bounded_control_flags',all(c.config(x)['seconds']==300 and c.config(x)['expected_exit']==int(x=='red300') for x in ['red300','green300']))
check('full286history',len(c.rd(D/'historical-groups.json')['groups'])==286)
check('no_launch_artifacts',not any((D/n).exists() for n in ['runs','outers']))
import oracle as o
check('panel_count11768',sum(o.panel_counts().values())==11768)
check('60payload31costs',len(o.PAYLOAD)==60 and len(o.PREPARATION)==31)
check('new_synthetic_tests_pass',c.rd(D/'tests.json')['all_passed'] is True and c.rd(D/'tests.json')['count']==4736 and c.bindings(c.rd(D/'tests.json')))
check('production_unmodified',c.git('diff','--name-only')==c.git('diff','--cached','--name-only')=='')
check('entry_refs',c.git('rev-parse','HEAD')=='2821702085f6bdaceb48c71a8774c99200e242eb' and c.git('rev-parse','master')==c.MASTER)
for n in ['control.py','oracle.py','audit.py','seal.py','launch.py','outer.py','post-return.py']:ast.parse((D/n).read_text())
check('python_syntax_only',True)
paths=[p for p in D.iterdir() if p.is_file()];c.save(D/'source-check.json',dict(all_passed=True,checks=checks,sha256={str(p):c.sha(p) for p in sorted(paths)},scope='New offline source/lineage checks only; no Julia syntax/dispatch/behavior claim'))
print(json.dumps({'all_passed':True,'checks':len(checks),'hashes':len(paths)}))
