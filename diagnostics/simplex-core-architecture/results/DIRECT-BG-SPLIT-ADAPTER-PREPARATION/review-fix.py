from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';S=R/'.superpowers/sdd/2026-10-18-direct-bg-split-free-blocks/task2-stage'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=E/'MEMORY-WORK.md';old=p.read_text()
with (E/'MEMORY-WORK.before-review.md').open('x') as f:f.write(old)
needle='At most two destination-alias inspections, four resize! requests to establish two slots, row-mapped n spike save, then unchanged fused finite checks/direction copy and publication.'
replacement='Inherited full prepared route: invalidate checks up to2 published-entry aliases; begin checks destination versus factor spike plus up to2 published-entry aliases and requests4 resizes (direction/spike for both slots); save requests1 spike resize then copies n row-mapped values; specialized Float64 finish has up to2 more alias guards, requests1 direction resize, and fuses finite checks with the n direction copy/publication. Thus up to7 mightalias checks in these prepared helpers and6 resize requests on the full ordinary successful prepared path, in addition to the separate destination gate above; short circuits can reduce these counts. No claim of7 executed calls or6 allocations follows.'
if old.count(needle)!=1 or old.count('TriangularRowCache has twelve fields.')!=1:raise RuntimeError('exact correction selector')
new=old.replace('TriangularRowCache has twelve fields.','TriangularRowCache has eleven fields.').replace(needle,replacement)
p.write_text(new)
struct=(S/'src/triangular_factorization.jl').read_text().split('mutable struct TriangularRowCache{T<:Real}\n',1)[1].split('\nend',1)[0]
a=(S/'src/split-bg.jl').read_text();sp=(S/'src/triangular_spikes.jl').read_text()
begin=a.split('Base.@noinline function _sbg_begin_prepared!',1)[1].split('Base.@noinline function _sbg_copy_prepared!',1)[0]
save=a.split('function _sbg_save_prepared!(entry',1)[1].split('function _sbg_sync_rows!',1)[0]
checks=dict(before_wrong_field_count='twelve fields' in old,actual_eleven_fields=len([l for l in struct.splitlines() if '::' in l])==11,after_eleven='eleven fields' in new,begin_two_resize_sites_two_entries=begin.count('resize!')==2 and 'for entry in cache.entries' in begin,save_one_resize=save.count('resize!')==1,finish_one_resize='direction = resize!(entry.direction, length(destination))' in sp,alias_scopes_explicit=all(x in new for x in ['invalidate checks up to2','destination versus factor spike plus up to2','up to2 more alias guards','up to7 mightalias','6 resize requests']),only_two_replacements=new.replace(replacement,needle).replace('eleven fields.','twelve fields.')==old)
record=dict(scope='Docs-only R1/R2 correction; old ledger preserved. No candidate/test/overlay/Julia change.',all_passed=all(checks.values()),checks=checks,bindings={str(q.relative_to(R)):sha(q) for q in [p,E/'MEMORY-WORK.before-review.md',E/'review-initial.md',E/'review-initial.json',E/'review-fix.py',S/'src/triangular_factorization.jl',S/'src/split-bg.jl',S/'src/triangular_spikes.jl']},mapping=dict(old_key=str(p.relative_to(R)),old_sha256=sha(E/'MEMORY-WORK.before-review.md'),preserved=str((E/'MEMORY-WORK.before-review.md').relative_to(R)),applies_to=['source-check-2.json','reviewer-check.json','review-initial.json']))
with (E/'review-fix.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),memory_sha256=sha(p))))
if not record['all_passed']:raise RuntimeError('review fix failed')
