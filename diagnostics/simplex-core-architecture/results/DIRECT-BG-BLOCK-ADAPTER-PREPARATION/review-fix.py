"""Exclusive source-only alias fix. Preserve rejected texts and all old bindings."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(c,m):
 if not c:raise RuntimeError(m)
paths=[C/'block-bg.jl',C/'block-bg-tests.jl',E/'MEMORY-WORK.md',E/'SOURCE-MAP.md']
before={}
for p in paths:
 dst=E/(p.name+'.before-alias-review');data=p.read_bytes()
 with dst.open('xb') as f:f.write(data)
 before[str(p.relative_to(R))]=dict(preserved=str(dst.relative_to(R)),sha256=sha(dst))
p=C/'block-bg.jl';s=p.read_text();old='    (Base.mightalias(destination,f.work) || Base.mightalias(destination,f.upper.scratch_value)) &&'
new='    (destination===f.work || destination===f.upper.scratch_value ||\n     Base.mightalias(destination,f.work) || Base.mightalias(destination,f.upper.scratch_value)) &&'
need(s.count(old)==1,'Alias source selector');s=s.replace(old,new);p.write_text(s)
p=C/'block-bg-tests.jl';t=p.read_text()
a='''            GC.@preserve scratch begin
                overlap=unsafe_wrap(Vector{Float64},pointer(scratch,2),3;own=false)
                @test_throws ArgumentError op(overlap,f,ones(3))
            end'''
b='''            # Same Memory owner, offset Vector; no unsupported raw-pointer claim.
            overlap=Base.wrap(Array,Core.memoryref(scratch.ref,2),3)
            @test Base.mightalias(overlap,scratch)
            @test_throws ArgumentError op(overlap,f,ones(3))'''
need(t.count(a)==1,'Alias test selector');t=t.replace(a,b)
a2='''function new_scratch_aliases()
    @testset "New block scratch aliases reject before dimension backend" begin'''
b2=a2+'''
        empty=J.BlockBGFactor(RejectBackend(),J._bgu_build(spzeros(0,0),Int[]),
            J.BartelsGolubUpdate{Float64}[],Float64[],Float64[],
            J.BartelsGolubUpdate{Float64}[],0,J.TriangularRowCache(Float64,0))
        for op in (J.forward_solve!,J.transpose_solve!)
            @test_throws ArgumentError op(empty.work,empty,Float64[])
        end'''
need(t.count(a2)==1,'Empty test selector');t=t.replace(a2,b2);p.write_text(t)
p=E/'MEMORY-WORK.md';m=p.read_text().replace('Two constant-time mightalias checks for work/new Float64 edit scratch before dimensions;', 'Two identity checks (including empty work) followed by up to two constant-time mightalias checks for work/new Float64 edit scratch before dimensions;')
m+='\nAlias review correction: the initial mightalias-only gate failed to preserve exact empty-work rejection. Identity checks now precede dataids-based shared-memory checks. The new partial alias test uses installed Base.wrap(Array,Core.memoryref(scratch.ref,2),3), bound to installed source, not unsafe_wrap over an independently owned offset pointer. Arbitrary foreign unsafe_wrap overlap is not proved/detected by this gate and is outside this private owned-buffer interface. The original rejected source/test/ledger/map and initial40-check record remain preserved; that check record did not prove alias coverage. Its unsupported_before_backend conjunct containing a vacuous empty-prefix text condition is superseded by review-fix.json explicit nonvacuous checks. No Julia RED/GREEN occurred.\n'
p.write_text(m)
p=E/'SOURCE-MAP.md';m=p.read_text().replace('Eight private fields as the stopped adapter','Eight private fields as the stopped adapter').replace('Work and new Float64 scratch overlap reject before dimensions/backend.','Exact work/new scratch identity (including empty work) and shared-Memory overlap reject before dimensions/backend; arbitrary foreign unsafe_wrap overlap is not covered.')
m+='\nSeparate canonical adapter-inverse-reviewed.json appends the explicit alias-gate edit to the original22 replacements; whole reverse still matches the original frozen source. Initial inverse binds only block-bg.jl.before-alias-review. Tests initially added an unsupported unsafe_wrap assumption; the preserved rejected text is replaced by source-bound shared-Memory wrapping and an empty-work sentinel. Old40text checks are not retroactively strengthened.\n';p.write_text(m)
d=json.loads((E/'adapter-inverse.json').read_text());d['edits'].append(dict(before=old,after=new));d['candidate_sha256']=sha(C/'block-bg.jl');d['scope']='Reviewed exact textual inverse with23edits, not numerical/runtime proof';d['fix_sha256']=sha(Path(__file__))
inv=s
for e in reversed(d['edits']):
 need(inv.count(e['after'])==e.get('count',1),'Inverse selector');inv=inv.replace(e['after'],e['before'])
for a,b in reversed(d['renames']):inv=inv.replace(b,a)
need(inv.encode()==Path(d['reference']).read_bytes(),'Full inverse')
with (E/'adapter-inverse-reviewed.json').open('x') as f:json.dump(d,f,indent=2);f.write('\n')
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
checks=dict(old_empty_identity_absent='destination===f.work ||' not in (E/'block-bg.jl.before-alias-review').read_text(),old_unsafe_assumption_present='unsafe_wrap(Vector{Float64},pointer(scratch,2)' in (E/'block-bg-tests.jl.before-alias-review').read_text(),identity_before_mightalias=s.index('destination===f.work ||')<s.index('Base.mightalias(destination,f.work)'),empty_sentinel_present='op(empty.work,empty,Float64[])' in t,shared_memory_offset_present='Base.wrap(Array,Core.memoryref(scratch.ref,2),3)' in t,explicit_alias_assertion='@test Base.mightalias(overlap,scratch)' in t,no_unsafe_wrap_in_test='unsafe_wrap' not in t,whole_inverse=True,unsupported_routes_nonvacuous=all(x in t for x in ['struct RejectBackend end','@test_throws ArgumentError op(zeros(Float32,3)','@test_throws ArgumentError op(idx,f,idx;kernel_mode=mode)','@test_throws ArgumentError op(overlap,f,ones(3))']))
record=dict(all_passed=all(checks.values()),checks=checks,preserved=before,sha256={str(p.relative_to(R)):sha(p) for p in paths+[E/'adapter-inverse-reviewed.json',Path(__file__)]},readtime_runtime_sources={str(runtime/n):sha(runtime/n) for n in ('abstractarray.jl','array.jl','boot.jl')},scope='Two source-detected rejection reasons corrected offline, no Julia/runtime RED/GREEN. Installed sources are new read-time bindings, not launch pins.')
with (E/'review-fix.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),inverse_edits=len(d['edits'])),indent=2));need(record['all_passed'],'Fix checks')
