from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
def need(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
rv=json.loads((Q/'review-first.json').read_text());need('initial_rejection',rv['accepted'] is False)
for n,h in rv['sha256'].items():need('review_binding:'+n,sha(Path(n) if Path(n).is_absolute() else R/n)==h)
changed=['factor.jl','factor-fault.jl','adapter-source-map.json','lifecycle-tests.jl','adapter-work-memory.md']
for n in changed:
 with (Q/(n+'.before-review')).open('xb') as out:out.write((C/n).read_bytes())
with (Q/'REPORT.md.before-review').open('xb') as out:out.write((Q/'REPORT.md').read_bytes())
old='''        _emit(probe,:scalar_pivot,column_index,J._upper_value(column,column_index),
              J._upper_value(column,column_index+1),swapped)
'''
new='''        if probe!==nothing
            _emit(probe,:scalar_pivot,column_index,J._upper_value(column,column_index),
                  J._upper_value(column,column_index+1),swapped)
        end
'''
for n in ['factor.jl','factor-fault.jl']:
 p=C/n;s=p.read_text();need('R1_RED:'+n,s.count(old)==1)
 s=s.replace(old,new,1)
 oldscan='''        # Preserve original pure-run optimization instead of crossing its boundary.
        if !blocked || J._last_pure_bartels_golub_swap(inner.upper,r)>r
'''
 newscan='''        # Exact-zero diagonal goes directly to the original scalar suffix.
        # Its full pure-run lookahead executes once, with no duplicate scan here.
        if !blocked || iszero(J._upper_value(inner.upper[r],r))
'''
 need('R2_RED:'+n,oldscan in s);s=s.replace(oldscan,newscan,1);p.write_text(s)
p=C/'adapter-source-map.json';j=json.loads(p.read_text());j['qualified_suffix']=j['qualified_suffix'].replace(old,new,1);j['cold_event_guard']='Scalar pivot argument reads explicitly under probe!==nothing';p.write_text(json.dumps(j,indent=2)+'\n')
p=C/'lifecycle-tests.jl';s=p.read_text();need('R3_RED','J.replace_column!(f,x,96)' in s)
s=s.replace('a=Vector(B[:,end]);x=zeros(96);v=similar(x)','j=f.inner.column_order[end];@test f.inner.positions[j]==96\n        a=Vector(B[:,j]);x=zeros(96);v=similar(x)',1).replace('J.replace_column!(f,x,96)','J.replace_column!(f,x,j)',1)
anchor='''    # Callback reentrancy fails before an inner solve; outer failure drops scratch.
'''
newtest='''    # Fail in the second writeback, after one complete panel changed live U.
    # This checks cleanup after partial progress, not rollback.
    f=micro(band(96);fault=true);FK.disarm!()
    events=Symbol[];begins=Ref(0);sentinel=OutOfMemoryError()
    late=(e,args...)->begin
        push!(events,e)
        if e===:panel_begin
            begins[]+=1
            begins[]==2 && FK.arm!(:writeback,sentinel)
        end
    end
    caught=nothing
    try F._bgb_test_eliminate!(f,1;probe=late) catch e;caught=e;end
    @test caught===sentinel && FK.hits[]==1 && begins[]==2
    @test count(==(:panel_commit),events)==1 && !(:finish in events)
    @test isempty(f.inner.updates) && failed_cache(f)
    FK.disarm!()
'''
need('R5_RED',anchor in s and 'begins[]==2' not in s);s=s.replace(anchor,newtest+anchor,1);p.write_text(s)
p=C/'adapter-work-memory.md';s=p.read_text();s=s.replace('''Per prospective panel: original pure-run lookahead, then eligibility's suffix
binary searches and stored-band traversal before workspace allocation. One new
pure-run lookahead per accepted panel duplicates at most its first scalar lookahead;
an ineligible/declined boundary also repeats that lookahead in the scalar suffix.
Worst-case lookahead is O(n) per boundary; no claim that this work is free.
''','''Per prospective panel: one exact current-diagonal packed lookup, O(log(nnz(column)+1)),
then eligibility's suffix binary searches and stored-band traversal before workspace
allocation. A zero diagonal goes directly to the original scalar suffix. The full
pure-run lookahead executes only inside that suffix: O(L) visited columns and
O(sum(log(nnz(column)+1))) lookup work for L columns, worst O(n log n). No duplicate
long-run scan. Scalar observation reads are explicitly guarded by probe!==nothing;
no two extra pivot searches occur in the unobserved scalar route. These are source
properties, not inferred optimizer behavior or measured allocation guarantees.
''')
s=s.replace('n96=11480','n96=11488').replace('2copies,7 FTRAN entries','2copies,5 FTRAN entries').replace('3fault points,1reentrancy =11','3early fault points,1late writeback fault,1reentrancy =12').replace('additional native identity constructors and11 elimination entries','additional native identity constructors and12 elimination entries')
s=s.replace('one committed column. OutOfMemoryError','one committed column (including the second panel after one earlier successful\ncommit). OutOfMemoryError')
p.write_text(s)
p=Q/'REPORT.md';s=p.read_text();s+='''
## Independent review correction

Initial independent review was rejected with R1–R5. Its exact bytes and every
changed candidate/report file are preserved. One bounded offline correction guards
scalar observation reads, replaces duplicate full pure-run lookahead with one exact
diagonal lookup, selects the no-op column through backend column_order, corrects
scratch/API ledger values, and adds a writeback exception after one committed panel.
No frozen Task1 file, original arithmetic/pivot policy, fixture bit, tolerance or
production source was changed. Julia remains unexecuted; final review is separate.
''';p.write_text(s)
s=(C/'factor.jl').read_text();l=(C/'lifecycle-tests.jl').read_text()
need('R1_GREEN',new in s and old not in s)
need('R2_GREEN','J._last_pure_bartels_golub_swap(inner.upper,r)' not in s and 'iszero(J._upper_value(inner.upper[r],r))' in s)
need('R3_GREEN','j=f.inner.column_order[end]' in l and 'J.replace_column!(f,x,j)' in l)
need('R4_GREEN','n96=11488' in (C/'adapter-work-memory.md').read_text() and '2copies,5 FTRAN' in (C/'adapter-work-memory.md').read_text())
need('R5_GREEN',all(x in l for x in ['begins[]==2 && FK.arm!', 'count(==(:panel_commit),events)==1','!(:finish in events)','caught===sentinel']))
with (Q/'review-fix.json').open('x') as out:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256={str(C/n):sha(C/n) for n in changed}|{str(Q/'REPORT.md'):sha(Q/'REPORT.md')},scope='One bounded offline R1-R5 fix, no Julia or numerical rerun'),out,indent=2)
print('R1-R5 source correction PASS; first rejection preserved')
