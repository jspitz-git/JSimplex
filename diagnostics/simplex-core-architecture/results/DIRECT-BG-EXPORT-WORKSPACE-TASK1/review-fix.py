from pathlib import Path
import json,hashlib,re
R=Path.cwd();C=R/'diagnostics/direct-bg-export-workspace/reproduce';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-TASK1'
paths=[C/'import-tests.jl',C/'work-memory-ledger.md'];before={}
for p in paths:
 q=E/(p.name+'.before-review')
 with q.open('xb') as f:f.write(p.read_bytes())
 before[str(p)]=str(q)
p=C/'import-tests.jl';s=p.read_text()
s=s.replace('packed_snapshot(v)=[(collect(c.indices),copy(bits(c.values))) for c in v]', '''packed_snapshot(v)=[(collect(c.indices),copy(bits(c.values))) for c in v]
export_snapshot(e)=(snapshot(e.lower),snapshot(e.upper),copy(e.rows),copy(e.columns),copy(bits(e.scaling)),e.divide_scaling)
export_arrays(e)=(e.lower.colptr,e.lower.rowval,e.lower.nzval,e.upper.colptr,e.upper.rowval,e.upper.nzval,e.rows,e.columns,e.scaling)''')
s=s.replace('B=fixture.B;before=snapshot(B);f=X._factorize_basis(B,Val(backend),policy)', 'B=fixture.B;before=snapshot(B);input_owners=(B.colptr,B.rowval,B.nzval);f=X._factorize_basis(B,Val(backend),policy)')
s=s.replace('@test e.upper!==ref.upper && e.upper.nzval!==ref.upper.nzval && e.lower.nzval!==ref.lower.nzval', '@test all(a!==b for (a,b) in zip(export_arrays(e),export_arrays(ref)))\n            frozen=export_snapshot(e);export_owners=export_arrays(e)')
s=s.replace('old=snapshot(e.upper);check_import(e.upper,true);@test snapshot(e.upper)==old','check_import(e.upper,true);@test isequal(export_snapshot(e),frozen)')
s=s.replace('@test snapshot(e.upper)==old && export_identity(B,e)','@test isequal(export_snapshot(e),frozen) && export_identity(B,e)')
needle='''            @test snapshot(B)==before
'''
new='''            # Restore the ORIGINAL source-backend mutation ownership witness.
            # Six native source refactors and six Markowitz mutation cases are
            # prospective test work, not part of candidate export/import work.
            if size(B,1)>0
                if backend===:native
                    refactor_input=copy(B)
                    refactor_input.nzval .*= 2.0
                    @test refactor_input.colptr==B.colptr && refactor_input.rowval==B.rowval
                    @test all(a!==b for (a,b) in zip((refactor_input.colptr,refactor_input.rowval,refactor_input.nzval),input_owners))
                    @test all(isequal(refactor_input.nzval[k],2.0*B.nzval[k]) for k in eachindex(B.nzval))
                    lu!(f.factorization,refactor_input)
                    @test issuccess(f.factorization)
                else
                    f.core.factors .= 7.0
                    f.diagonal .+= 1.0
                    reverse!(f.row_order)
                    for v in f.lower;v.values .+= 1.0;end
                    for v in f.upper;v.values .+= 1.0;end
                end
                @test isequal(export_snapshot(e),frozen)
                @test export_identity(B,e)
            end
            @test all(a===b for (a,b) in zip(export_arrays(e),export_owners))
            @test snapshot(B)==before
            @test all(a===b for (a,b) in zip((B.colptr,B.rowval,B.nzval),input_owners))
'''
assert s.count(needle)==1;s=s.replace(needle,new);p.write_text(s)
p=C/'work-memory-ledger.md';s=p.read_text().replace('No refactors/full solves/public LPs in this Task1 fixture loop.', 'The restored source-backend ownership witness adds exactly six nonempty native source lu! refactor attempts (structure-preserving copies of the original input) and six Markowitz source-mutation cases. These are test-only work, not new candidate refactors; each native attempt may perform backend work not counted by this API total. No public LP solves in this Task1 fixture loop.')
s+='''
## Review amendment R1 — restored original source ownership witness

The first review found incomplete retention of the original test_exports source-backend mutation witness. The original source/candidate hashes and rejected review are preserved; only import-tests.jl and this ledger change. Every fixture now compares all nine exported array identities with an independent export, keeps a full detached export snapshot (two CSC snapshots, p/q vectors, scaling bits and divide flag), and retains owner tuples without copying output ownership. For nonempty native fixtures the test copies B (colptr,rowval,nzval), scales values by2 preserving stored zeros, checks structure/owner/bits, then performs one original lu! on the source factor and checks success. For nonempty Markowitz fixtures it poisons the core, diagonal, row order and lower/upper values exactly as the original witness. The original B and export owner/value snapshots must remain unchanged and the independent exact export identity must still hold.

Additional cold test memory includes14 full export snapshots (each two pointer vectors totaling2*(n+1), l+u row-index entries, l+u UInt64 value tokens, p/q totaling2*n, scaling n, and scalar flags),14 nine-owner tuples and14 three-input-owner tuples, plus six native input CSC copies. Snapshot equality probes create corresponding transient snapshot arrays; rational export_identity calls materialize dense rational matrices/vectors as before. Backend mutation/refactor can allocate independently; this ledger counts six native API attempts, not complete backend internals/physical peaks. No callback, extra solve or snapshot was added to the candidate. Tests remain UNEXECUTED.
''';p.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=(E/'import-tests.jl.before-review').read_text()
checks=dict(red_missing_original_witness='lu!(f.factorization,refactor_input)' not in old,green_native_witness='lu!(f.factorization,refactor_input)' in p.with_name('import-tests.jl').read_text(),green_markowitz_witness=all(z in (C/'import-tests.jl').read_text() for z in ['f.core.factors .= 7.0','f.diagonal .+= 1.0','reverse!(f.row_order)','for v in f.lower','for v in f.upper']),all_nine_export_owners='zip(export_arrays(e),export_arrays(ref))' in (C/'import-tests.jl').read_text(),full_snapshot_and_input_owners='export_snapshot(e)' in (C/'import-tests.jl').read_text() and 'zip((B.colptr,B.rowval,B.nzval),input_owners)' in (C/'import-tests.jl').read_text(),budget_six_plus_six='exactly six nonempty native' in s and 'six Markowitz' in s,no_candidate_source_change=True)
a=json.loads((E/'source-check.json').read_text())
checks['all_original_bindings_preserved']=all(sha(Path(before.get(n,n)))==h for n,h in a['readtime_sha256'].items())
checks['no_candidate_source_change']=all(sha(C/n)==a['readtime_sha256'][str(C/n)] for n in ['workspace.jl','export.jl','import.jl'])
files=[*paths,*map(Path,before.values()),E/'review.md',E/'review.json',E/'reviewer-check.py',E/'reviewer-check.json',Path(__file__).resolve()]
x=dict(all_passed=all(checks.values()),checks=checks,before_mapping=before,readtime_sha256={str(q):sha(q) for q in files},static_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',(C/'workspace-tests.jl').read_text()+(C/'import-tests.jl').read_text())),scope='Offline textual RED/GREEN of missing witness only, NOT Julia test execution')
with (E/'review-fix.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=x['all_passed'],checks=len(checks),bindings=len(files),static_assertion_sites=x['static_assertion_sites'])))
if not x['all_passed']:raise SystemExit(1)
