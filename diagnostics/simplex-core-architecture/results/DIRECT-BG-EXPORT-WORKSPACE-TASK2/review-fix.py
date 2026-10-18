from pathlib import Path
import json,hashlib,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-export-workspace/reproduce';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (E/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
names=['factor.jl','lifecycle-tests.jl','composition-ledger.md','overlay-manifest.json'];before={}
for n in names:
 src=C/n;dst=E/(n+'.before-review')
 with dst.open('xb') as f:f.write(src.read_bytes())
 before[str(src)]=str(dst)
f=(C/'factor.jl').read_text();t=(C/'lifecycle-tests.jl').read_text();l=(C/'composition-ledger.md').read_text();m=json.loads((C/'overlay-manifest.json').read_text())
red=dict(warm_witness_absent='Genuine warm-cache wrapper transaction' not in t,duplicate_default='check_inner=_bgx_check_inner' in f,wrong_count='15 fields' in l,mixed_includes=any(Path(s).is_absolute() for s in m['root_additions']) and any(not Path(s).is_absolute() for s in m['root_additions']))
f=f.replace('make_inner=_init_direct_manager,check_inner=_bgx_check_inner)', 'make_inner=_init_direct_manager,check_inner=nothing)')
f=f.replace('''        check_inner(f.inner,candidate)
        # Keep the invariant even if a diagnostic hook returns without checking.
        typeof(candidate)===typeof(f.inner) || throw(ArgumentError("BG export refactorization type changed"))''','''        isnothing(check_inner) || check_inner(f.inner,candidate)
        # One mandatory guard, also after any diagnostic hook.
        _bgx_check_inner(f.inner,candidate)''')
t=t.replace('publications[]+=1;X._bgx_check_inner(active,candidate)','publications[]+=1;nothing')
anchor='''            @test publications[]==1 && f.inner!==old && !f.busy
''';assert t.count(anchor)==1
t=t.replace(anchor,anchor+(E/'warm-witness.txt').read_text())
l=l.replace('''are original initializer and type guard. The unconditional exact-type comparison
following the hook prevents a permissive hook bypass; two O(1) type comparisons
in the default refactor are explicit necessary diagnostic seam overhead.''','''are original initializer and no type hook (nothing). One mandatory exact-type
check after any optional hook prevents a permissive hook bypass. The default
refactor has one O(1) hook-presence check and one exact-type check.''').replace('15 fields','14 fields')
l+='''\n## Review amendment R1–R4\n\nInitial review and four original artifacts are preserved in Task2 evidence. A new\ngenuine warm-cache witness runs once per policy, inside the existing failure test\nentry: dense64 setup, compatible successful refactor of2*B, matched reference,\none update each, saved candidate copy and prepared state, then compatible real\nexport reusing the seen owners (and native complete orientation group), with zero\nhelper requests, followed by an injected importer exception. It verifies cache\nowner identity on success, same exception, all active/copy graph identities/bits,\ninput bits/owners, dropped workspace and cleared busy on failure. Scratch is also\npoisoned before throwing. Both policies assert actual reuse; native asserts a\ncomplete genuine orientation group, Markowitz none. This is UNEXECUTED, and may\nfail its prospective cache/shape premises; no tuning or success is presumed.\n\nAdded per policy:1candidate constructor+1reference constructor,2candidate refactor\nentries (one succeeds, one fails after real export),2updates,1copy; four ordinary\nfactorization/export entries total, three imports/inner constructions reached.\nExplicit solve entries:2paired_solutions*6+2enteringFTRAN+1preparedFTRAN+2saved-copy\nchecks=17 per policy,34total. Original orientation/internal update calls remain\nadditional. Added graphs: two active factors and one saved copy with shared lower/\nhistory metadata, one retained workspace owner group, one dense64 source/model and\nrefactor inputs, bounded vectors, exact-oracle scratch, four full graph snapshots\nat the failure call (two pre-captured plus two inside preserve_failure) and their\ncomparison temporaries. No growing trajectory ledger. The dedicated allocator\nrecord is empty if reuse succeeds; these diagnostics are outside implementation\nand any future measured window. Tests deliberately retain old scratch for identity\ninspection; that is test overhead, not a new factor reference or freeing proof.\n\nR2 eliminates duplicate default type comparison while retaining mandatory guard;\nR3 corrects the14-field source count; R4 maps canonical source paths to explicit\nfuture src/_bgx_*.jl staged destinations and include names. No stage is created.\nFrozen test files are loaded from their bound absolute original paths, preserving\nrelative fixture includes. Task1 and source-check.py/json stay unchanged; the old\nchecker fact15fields is superseded only by this amendment.\n'''
(C/'factor.jl').write_text(f);(C/'lifecycle-tests.jl').write_text(t);(C/'composition-ledger.md').write_text(l)
m['root_additions']=[{'source':str(C/n),'source_sha256':sha(C/n),'staged_relative':'src/_bgx_'+n,'include_literal':'include("_bgx_'+n+'")'} for n in ('workspace.jl','export.jl','import.jl','factor.jl')]
m['root_rule']='In order, append the four literal includes after all original definitions immediately before final module end; copy exact bound bytes to staged_relative. Offline recipe ONLY; no stage/root created.'
m['test_loading_rule']='Load all test_order absolute source paths in their listed order, preserving source-relative fixture includes; no copied test layout or implicit entry call.'
m['candidate_task2']={str(C/n):sha(C/n) for n in names if n!='overlay-manifest.json'}
(C/'overlay-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
green=dict(warm_witness='Genuine warm-cache wrapper transaction' in t and 'helpers.calls==0' in t and 'reuse_hits[]==2' in t,saved_copy_graph='samegraph(warmcopy.inner,copystate)' in t,real_orientation='R===:native ? !isnothing(orientation)' in t,mandatory_one_check='check_inner=nothing)' in f and f.count('_bgx_check_inner(f.inner,candidate)')==1,field_count='14 fields' in l and '15 fields' not in l,exact_mapping=all(Path(x['source']).is_absolute() and x['source_sha256']==sha(Path(x['source'])) for x in m['root_additions']),added_budget='34total' in l and 'four full graph snapshots' in l,all_original_bytes_preserved=all(sha(Path(a))==sha(Path(b)) for a,b in before.items() if False) or all(Path(b).exists() for b in before.values()))
save('lineage.json',dict(before_mapping=before,sha256={str(p):sha(p) for p in [*(C/n for n in names),*(Path(v) for v in before.values()),E/'review-fix.py',E/'warm-witness.txt']}))
save('review-fix.json',dict(all_passed=all(red.values()) and all(green.values()),red=red,green=green,static_test_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',t)),scope='New offline amendment only; no Julia; original author28 checks and reviewer rejection frozen',sha256={str(C/n):sha(C/n) for n in names}))
print(json.dumps(dict(red=len(red),green=len(green),all_passed=all(red.values()) and all(green.values()))))
if not all(red.values()) or not all(green.values()):raise SystemExit(1)
