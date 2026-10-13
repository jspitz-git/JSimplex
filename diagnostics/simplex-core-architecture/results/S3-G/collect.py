"""Single-use source-only record. No Julia, arithmetic probe or old auditor."""
from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S3-G';F=R/'diagnostics/simplex-core-architecture/results/S3-F'
B=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def save(name,obj):
 with (D/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
groups=set(json.loads((F/'host.json').read_text())['groups_and_sessions']);matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split()
  if int(a[2]) in groups or int(a[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
refs={k:git('rev-parse',k) for k in ['HEAD','master']}
need(refs=={'HEAD':'7ddea1bba37e2783871b5d947e261554de88a856','master':'d02416c108f06fcd41d58e0a1980b70a51fef9ef'},'refs changed')
save('host.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups_and_sessions=sorted(groups),matches=matches,refs=refs,remote_refs=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=git('status','--short')))
need(not matches,'host not clear')
paths={'diagnostics/simplex-core-architecture/STATUS.md':'STATUS.md.before-S3-G','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':'roadmap.md.before-S3-G'}
for p,n in paths.items():
 with (D/n).open('xb') as f:f.write((R/p).read_bytes())
old={}
for name in ['closure.json','publication.json','review-final.json']:
 d=json.loads((F/name).read_text());old[name]={p:d['sha256'][p] for p in paths}
 need(all(sha(R/p)==h for p,h in old[name].items()),'F continuation binding mismatch')
gmp=(B/'gmp.jl').read_text(); rat=(B/'rational.jl').read_text();sx=(R/'src/simplex.jl').read_text();idx=(R/'src/indexed_vector.jl').read_text();hp=(R/'src/hypersparse_pipeline_types.jl').read_text();dual=(R/'src/dual_simplex.jl').read_text();diag=(R/'src/simplex_diagnostics.jl').read_text();pivot=(R/'src/simplex_pivot.jl').read_text()
checks={
 'mutable_bigint':'mutable struct BigInt <: Signed' in gmp,
 'rational_fields':'num::T\n    den::T' in rat,
 'fresh_arithmetic_destinations':'(Base.$fJ)(x::Rational{BigInt}, y::Rational{BigInt}) = $fC!(unsafe_rational(BigInt(), BigInt()), x, y)' in gmp,
 'operator_mapping':'((:+, :add), (:-, :sub), (:*, :mul), (://, :div))' in gmp,
 'sync_returns_destination':'return xq.rat' in gmp and 'xq.rat.num.d     = xq.num_d' in gmp,
 'multiply_nonfinite_zero_throws':'if iszero(x.den) || iszero(y.den)\n        if iszero(x.num) || iszero(y.num)\n            throw(DivideError())' in gmp,
 'subtraction_c_call':'(:__gmpq_sub, libgmp)' in gmp,
 'primal_assignment_shares_scalar':'workspace.primal[index] = basic_primal[row]' in sx,
 'candidate_vector_copy':'copyto!(destination.primal,source.primal)' in pivot,
 'observer_receives_state':'d.observer(reason, state)' in diag,
 'support_not_element_ownership':'valid::BitVector' in hp and 'membership::Vector{UInt}' in idx,
 'basis_constructor_copies_no_uniqueness_check':'return new(Int.(basic_indices), collect(states))' in sx,
 'ordered_dense_update':'workspace.primal[index] -= primal_step * tableau_column[row]' in dual and 'workspace.primal[entering_index] += primal_step' in dual,
 'production_test_ci_unchanged':not git('diff','master','--','src','test','.github'),
}
files=[R/'src'/n for n in ['dual_simplex.jl','simplex.jl','simplex_pivot.jl','simplex_diagnostics.jl','simplex_numerics.jl','hypersparse_pipeline.jl','hypersparse_pipeline_types.jl','indexed_vector.jl','numeric.jl']]+[B/'gmp.jl',B/'rational.jl']+[R/'diagnostics/simplex-core-architecture'/n for n in ['S3-VALUE-UPDATE-SUPPORT-CONTRACT.md','S3-VALUE-UPDATE-SUPPORT-CONTRACT-REVIEW.md']]+[R/'docs/superpowers/plans/2026-10-13-rational-primal-support-admission.md']+[D/n for n in ['collect.py','host.json','STATUS.md.before-S3-G','roadmap.md.before-S3-G']]
save('source.json',dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in files},previous_continuation_hashes=old,scope='Read-time installed source, not new runtime/loader provenance. No Julia or numerical experiment. Existing F audits not rerun.'))
need(all(checks.values()),'source checks failed')
print(json.dumps({'checks':len(checks),'hashes':len(files),'all_passed':True}))
