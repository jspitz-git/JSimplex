from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-R'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=[E/'tests.jl',E/'plan.md',E/'fixtures.toml',E/'ledger.md',R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PREPARATION.md']
mp={}
for p in paths:
 q=E/(p.name+'.before-review-fix')
 with q.open('xb') as f:f.write(p.read_bytes())
 mp[str(p)]={'preserved':str(q),'sha256':sha(q)}
p=E/'tests.jl';s=p.read_text();old='''    elseif kind == "cancellation"
        F.factors[1,2] = T(2)^128; b[1] = T(2)^256; b[2] = T(2)^128
''';new='''    elseif kind == "cancellation"
        # Packed L/U: unit diagonals and L21=U12=2^128. Both orientations
        # subtract exactly 2^128 * 2^128 from b2=2^256 at their first update.
        for j in 1:n, i in 1:n
            F.factors[i,j] = T(i==j)
        end
        F.ipiv .= 1:n
        for i in 1:n
            b[i] = T(0)
        end
        F.factors[2,1] = T(2)^128; F.factors[1,2] = T(2)^128
        b[1] = T(2)^128; b[2] = T(2)^256
'''
red={'old_case_has_forced_packed_identity':new in s,'old_case_checks_zero_endpoint':'records[end].output[2][1] == 0//1' in s}
if s.count(old)!=1 or any(red.values()):raise SystemExit('Unexpected RED state')
s=s.replace(old,new)
anchor='''                    repeat_call=kind=="retained_outputs", expected_exception=expected)))'''
if s.count(anchor)!=1:raise SystemExit('Anchor mismatch')
s=s.replace(anchor,anchor+'''\n                if kind=="cancellation"\n                    @test records[end].output[1][1] == BigInt(2)^128//1\n                    @test records[end].output[2][1] == 0//1\n                    @test all(v[1] == 0//1 for v in records[end].output[3:end])\n                end''')
p.write_text(s)
p=E/'fixtures.toml';s=p.read_text();anchor='special_bits = 256\n';s=s.replace(anchor,anchor+'cancellation = "packed L/U identity; L21=U12=2^128; ipiv=1:n; b1=2^128,b2=2^256,others0; both endpoints [2^128,0,...,0]"\n');p.write_text(s)
p=E/'plan.md';s=p.read_text().replace('ipiv[8]=17, identity/row swap, cancellation powers2^128/2^256, signed zeros,','ipiv[8]=17, identity/row swap, cancellation packed identity with L21=U12=2^128,\nb1=2^128,b2=2^256 and other RHS0, signed zeros,');s+='''\n## Offline review amendment\n\nThe initial accepted review was superseded by P2: the original cancellation fixture\nused ordinary LU diagonals near18 and did not force cancellation. The original\nreview/tests remain preserved. A separate offline fix uses the packed factor above,\nso the F L and B U-transpose first update both subtract2^256 from2^256. The final\nendpoint [2^128,0,...,0] is explicitly asserted, with no extra solve. Both global\nprecision and solve count remain unchanged. This exact integer argument is not a\nJulia runtime result; final review of the amendment is pending.\n''';p.write_text(s)
p=E/'ledger.md';s=p.read_text();s+='''\nFinal review amendment P2: initial cancellation fixture did not force cancellation.\nOne source-only RED2/GREEN2 fix replaces only its private factor/RHS construction\nand adds endpoint assertions. Candidate arithmetic and488entry budget unchanged.\nOriginal review is superseded for admission pending separate final amendment review.\n''';p.write_text(s)
p=paths[-1];s=p.read_text();s+='''\nThe initial review was superseded by a source-only cancellation-coverage finding.\nA separate fixture amendment forces exact cancellation in both solve orientations\nand asserts its endpoint; candidate code and call counts are unchanged. Original\nreview and input bytes are preserved. Final amendment review is pending.\n''';p.write_text(s)
green={'forced_packed_identity':new in (E/'tests.jl').read_text(),'zero_and_first_endpoint_assertions':all(x in (E/'tests.jl').read_text() for x in ['records[end].output[2][1] == 0//1','records[end].output[1][1] == BigInt(2)^128//1'])}
# Exact integer argument only, no Julia, floating arithmetic, LU or solver call.
a=2**128; b=a*a
checks={'structural_RED2_false':not any(red.values()),'structural_GREEN2_true':all(green.values()),'exact_both_first_updates_zero':b-a*a==0,'exact_both_second_updates_preserve_first':a-a*0==a,'candidate_unchanged':sha(E/'candidate.jl')==json.loads((E/'source-check.json').read_text())['sha256'][str(E/'candidate.jl')],'original_review_preserved':all(sha(p)==h for p,h in json.loads((E/'review.json').read_text())['sha256'].items() if p not in mp)}
obj={'mapping':mp,'scope':'Only changed input bindings in initial source-check.json/review.json resolve to these beforecopies; old continuation mappings remain. Candidate/reference/instrumented/environment unchanged. Initial review accepted before P2 surfaced; review-amendment supersedes it, final review required.'}
with (E/'review-fix-map.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
with (E/'review-fix.json').open('x') as f:json.dump({'RED':red,'GREEN':green,'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in paths+[E/'review-fix.py',E/'review-fix-map.json',E/'review.md',E/'review.json']}},f,indent=2);f.write('\n')
print(json.dumps(checks))
if not all(checks.values()):raise SystemExit(1)
