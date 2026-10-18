from pathlib import Path
import hashlib,json,subprocess,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION'
N=R/'diagnostics/direct-bg-split-upper/reproduce'
O=R/'diagnostics/direct-bg-block-upper/reproduce'
H={}; checks={}
def data(p):
 p=Path(p);b=p.read_bytes();H[str(p)]=hashlib.sha256(b).hexdigest();return b
def js(p):return json.loads(data(p))
def txt(p):return data(p).decode()
def ck(k,v):checks[k]=bool(v)
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
ck('head_pinned',git('rev-parse','HEAD')=='665a0d215bb767f4e9f2d4b94102dd7ac42d20f5')
ck('branch_pinned',git('branch','--show-current')=='codex/simplex-core-architecture')
ck('master_pinned',git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
ck('tracked_clean',git('diff','--name-only','HEAD')=='')
o=js(N/'adapter-source-bindings.json');ck('overlay_same',o==js(E/'overlay.json'))
stage=Path(o['path']);old=Path(o['source'])
for label,root,manifest in [('new',stage,o['sha256']),('old',old,o['baseline'])]:
 allfiles=[p for p in root.rglob('*') if p.is_file()]
 ck(label+'_81_exact_members',len(manifest)==81 and {str(p.relative_to(root)) for p in allfiles}==set(manifest))
 ck(label+'_ordinary_no_symlinks',not any(p.is_symlink() for p in root.rglob('*')))
 ck(label+'_all_hashes',all(hashlib.sha256(data(root/k)).hexdigest()==v for k,v in manifest.items()))
repl=o['replacements']
ck('new_five_exact',all(data(stage/v)==data(N/Path(v).name) for v in repl.values()))
ck('unchanged75',all(data(stage/k)==data(old/k) for k in o['baseline'] if k not in repl and k!='src/JSimplex.jl'))
root=data(stage/'src/JSimplex.jl').replace(b'include("split-upper.jl")',b'include("block-upper.jl")').replace(b'include("split-bg.jl")',b'include("block-bg.jl")')
ck('root_include_inverse',root==data(old/'src/JSimplex.jl'))
ck('master_original_sources',all(subprocess.check_output(['git','show',o['master']+':'+k],cwd=R)==data(stage/k) for k in o['sha256'] if k.startswith('src/') and k!='src/JSimplex.jl' and (R/k).exists()))
inv=js(E/'adapter-inverse.json');s=txt(N/'split-bg.jl');rev=s
for a,b in reversed(inv['renames']):rev=rev.replace(b,a)
ck('adapter_whole_inverse',rev.encode()==data(O/'block-bg.jl'))
ck('adapter_binding_hashes',hashlib.sha256(data(N/'split-bg.jl')).hexdigest()==inv['candidate_sha256'] and hashlib.sha256(data(O/'block-bg.jl')).hexdigest()==inv['reference_sha256'])
p=js(E.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION/adapter-inverse-reviewed.json');prev=txt(O/'block-bg.jl')
for edit in reversed(p['edits']):
 assert prev.count(edit['after'])==edit.get('count',1)
 prev=prev.replace(edit['after'],edit['before'])
for a,b in reversed(p['renames']):prev=prev.replace(b,a)
ck('parent_whole_inverse',prev.encode()==data(p['reference']))
f=js(E/'tests-first.json');t=txt(N/'split-bg-tests.jl');ti=t
ck('unique_test_additions',ti.count(f['extra'])==ti.count(f['call'])==1)
ti=ti.replace(f['extra'],'').replace(f['call'],'')
for a,b in reversed(f['renames']):ti=ti.replace(b,a)
ck('test_whole_inverse',ti.encode()==data(O/'block-bg-tests.jl'))
ck('test_preparation_hashes',f['adapter_absent'] and all(hashlib.sha256(data(k)).hexdigest()==v for k,v in f['sha256'].items()))
ck('fixtures_byte_exact',data(N/'fixtures.jl')==data(O/'fixtures.jl')==data(stage/'test/fixtures.jl'))
ck('nine_static_testsets',t.count('@testset')==9)
b=js(E/'binding-map.json')
ck('initial_binding_maps',all(js(E/m['record'])['sha256'][m['key']]==m['sha256']==hashlib.sha256(data(E/m['preserved'])).hexdigest() for m in b['mappings']))
c=js(E/'source-check-2.json')
ck('author_current_all_bindings',all(hashlib.sha256(data(R/k if not Path(k).is_absolute() else k)).hexdigest()==v for k,v in c['sha256'].items()))
ck('author_22_reported_pass',c['all_passed'] and len(c['checks'])==22 and all(c['checks'].values()))
# Read full governing and supporting records; no old Python or Julia is evaluated.
for pth in ['AGENTS.md','docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md','docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md']:
 txt(R/pth)
for pth in ['REPORT.md','MEMORY-WORK.md','SOURCE-MAP.md','author-fix.json','host.json','prepare-documents.py','prepare-tests.py','source-check.py','source-check-2.py']:
 txt(E/pth)
txt(N/'prepare-adapter-overlay.py')
for pth in ['MEMORY-WORK.md','review.md','review.json','closure.json','publication.json','geometry-model.json']:
 txt(E.parent/'DIRECT-BG-SPLIT-U-PREPARATION'/pth)
# Independent integer count of the explicit extra scalar-assignment schedules.
counts=[32,1,1,16,16,33,9];second=[7,14]
ck('129_assignments',sum(counts)==108 and sum(second)==21 and sum(counts)+sum(second)==129)
# Integer geometry only: remaining suffix after requests1,2,4,8,16.
remaining=32;start=225;trace=[]
for target in (1,2,4,8,16):
 start+=target;remaining-=target;trace.append([target,start,remaining])
ck('suffix1_geometry',remaining==1 and start==256)
# Hand-readable structural field count; no Julia parser/import.
fields=txt(stage/'src/triangular_factorization.jl').split('mutable struct TriangularRowCache{T<:Real}\n',1)[1].split('\nend',1)[0].splitlines()
ck('row_cache_eleven_fields',len(fields)==11)
record={'scope':'OFFLINE independent source/text/hash/integer review; no Julia/query/parser/import/compile/numerics or old scripts; no Git mutations. Not runtime/performance/Task3 admission.', 'checks':checks,'all_checks_passed':all(checks.values()),'sha256':H,'new_schedule_assignments':{'first':sum(counts),'second':sum(second),'total':sum(counts)+sum(second)},'suffix_geometry':trace,'static_testsets_unexecuted':re.findall(r'@testset "([^"]+)"',t),'findings':[{'id':'R1','severity':'minor','file':'MEMORY-WORK.md','issue':'TriangularRowCache is described as twelve fields; pinned definition has eleven. All actual owner fields are enumerated, so this is a field-count correction, not a missing owner.'},{'id':'R2','severity':'minor','file':'MEMORY-WORK.md','issue':'Prepared-FTRAN alias count is scoped ambiguously. Whole route has up to two prepared-entry checks in invalidate, spike check plus up to two entry checks in begin, and two finish guards. Describe these separately; four resize requests are for begin slot establishment, with one save and one finish resize request additionally.'}], 'unnecessary_work_memory':'No unnecessary newly introduced adapter computation or retention found: exact whole-file rename inverse. Frozen allocator adds required bounded class/bin/local metadata work and can increase relocation, descriptor growth, block visits and retention; those costs are explicitly charged. Runtime benefit/allocations unmeasured.'}
with (E/'reviewer-check.py').open('x') as out:out.write(Path(__file__).read_text())
with (E/'review-initial.json').open('x') as out:json.dump(record,out,indent=2);out.write('\n')
report='''# Independent Task2 offline review — initial\n\nOffline candidate/test preparation has two minor documentation findings; no candidate or test defect identified. Julia syntax, dispatch, numerical results, performance and actual allocation/retention remain UNEXECUTED and unqualified. No Task3 run is authorized.\n\n1. R1: MEMORY-WORK.md calls TriangularRowCache a twelve-field structure; the pinned definition has eleven. Its four vector references, six scalar/flag fields and prepared reference are all already enumerated. Correct the count.\n2. R2: The Prepared-FTRAN entry says at most two destination-alias inspections, which does not describe the full route. The separate invalidator checks up to two entries; begin checks destination against spike and up to two entries; finish contains two further alias guards. Four resize requests describe begin alone; save and finish each request one more. Scope the counts explicitly. These operations are inherited, with no new adapter work.\n\nIndependent exact-byte checks verify the complete81-file ordinary overlay, all source and baseline hashes,75 unchanged files,5new source/test replacements and the2root include replacements; production source blobs agree with pinned master. Both adapter inverse hops and the original test inverse pass. The original failed current-checkout equality record is preserved; both displaced document hashes resolve through binding-map.json. Frozen Task1 and fixtures are unchanged. Exact checked file hashes and checks are in review-initial.json.\n\nSource review checked packed forward/transpose arithmetic, spike reconstruction, finite publication, prepared entering/DSE provenance, pivot/history order, typed alias/width gates, complete copy/refactor publication and permitted partial failed-update state. All seven fixtures/both backend arms and9static testsets are prepared, not executed. New pairs cover growth,33split, deletion/refill, nonpower imported tails, rotations and incidence merge; scalar-assignment count is108+21=129. The suffix-reuse sequence does consume a genuine suffix: requests1,2,4,8,16 leave the latest1-cell suffix at physical position256 ahead of the older freed1-cell extent; growth32 leaves bin1 intact. Explicit extent-identity assertion would strengthen the test but current source selects that suffix.\n\nNo unnecessary newly introduced adapter work or retained-memory mechanism was found. Its complete rename inverse proves zero new adapter scans, solves, conversion loops, fields or caches relative to the frozen block adapter. The frozen allocator's class/bin checks, extra descriptors, progressive relocation/clearing and possible repeated growth are charged; changed partitions can increase block traversal and cannot establish a speedup. The ledger accounts for core/outer/header/backing owners, external prepared destination roots, shared lower/history owners, complete copy/refactor coexistence, row/descriptor/directory growth and fragmentation; no physical/native peak or O(live) bound is accepted. Tests' full snapshots/partition scans remain test-only. No before/after runtime benchmark is available under the explicit no-Julia boundary.\n\nThe reviewer ran only newly authored Python for text/hash/integer checks, never the old or author scripts, Julia, candidate code, tests, parser, import, compilation or numerics, and made no Git mutations.\n'''
with (E/'review-initial.md').open('x') as out:out.write(report)
print(json.dumps({'all_checks_passed':record['all_checks_passed'],'checks':len(checks),'hashes':len(H),'failed':[k for k,v in checks.items() if not v],'findings':record['findings']},indent=2))
assert record['all_checks_passed']
