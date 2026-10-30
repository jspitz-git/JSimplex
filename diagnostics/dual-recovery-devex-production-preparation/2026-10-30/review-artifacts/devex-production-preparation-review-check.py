from pathlib import Path
import hashlib,json,re,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';Q=D/'prepared';O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';G=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30/prepared/overlays/candidate'
bindings={};checks={}
def data(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def txt(p):return data(p).decode()
def obj(p):return json.loads(data(p))
def check(n,v):checks[n]=bool(v)
def git(*args):return subprocess.check_output(['git','-C',str(W),*args])
m=obj(D/'manifest.json');initial=obj(D/'source-check.json');endpoint=obj(D/'source-check-endpoint.json')
for p in [W/'AGENTS.md',W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md',W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md',D/'INTEGRATION-PREPARATION.md',D/'source-check.py',D/'source-check-endpoint.py',D/'prepare.py',D/'preflight.py',Path('/mnt/c/Users/jiris/.codex/plugins/cache/openai-curated-remote/superpowers/7.0.1/skills/using-superpowers/SKILL.md')]:data(p)
check('payload_exact_11_names',sorted(str(p.relative_to(Q)) for p in Q.rglob('*') if p.is_file())==m['payload'] and len(m['payload'])==11)
for rel,h in m['payload_sha256'].items():check('payload_hash:'+rel,hashlib.sha256(data(Q/rel)).hexdigest()==h)
for rel,h in m['baseline_sha256'].items():check('baseline_current_master:'+rel,data(D/'baseline'/rel)==data(W/rel)==git('show','master:'+rel) and hashlib.sha256(data(W/rel)).hexdigest()==h)
for p,v in m['exact_copies'].items():check('copy:'+str(p),data(p)==data(v['copy']) and hashlib.sha256(data(p)).hexdigest()==v['sha256'])
for rel,v in m['transforms'].items():
 s=txt(v['source']);good=hashlib.sha256(s.encode()).hexdigest()==v['source_sha256']
 for r in v['replacements']:good &= s.count(r['old'])==1;s=s.replace(r['old'],r['new'],1)
 check('full_transform:'+rel,good and s==txt(Q/rel))
# Compare entire candidate project and classify only the three intended sources against baseline.
a=O/'overlays/candidate';an=sorted(str(p.relative_to(a)) for p in a.rglob('*') if p.is_file());gn=sorted(str(p.relative_to(G)) for p in G.rglob('*') if p.is_file())
check('74_candidate_members_match_green2',an==gn and len(an)==74)
for rel in an:check('qualified_project:'+rel,data(a/rel)==data(G/rel))
for rel in m['payload']:
 if rel.startswith('src/'):check('prepared_exact_qualified:'+rel,data(Q/rel)==data(a/rel))
check('only_three_production_files',sorted(p for p in m['payload'] if p.startswith('src/'))==['src/simplex_numerics.jl','src/simplex_pivot.jl','src/simplex_recovery.jl'])
# Independently apply every unified hunk in memory (do not execute preparation or old checks).
patch=txt(D/'production.patch');sections=re.split(r'^diff --git ',patch,flags=re.M)[1:];names=[]
for section in sections:
 lines=section.splitlines(keepends=True);match=re.fullmatch(r'a/(.+) b/(.+)\n',lines[0]);assert match and match[1]==match[2];rel=match[1];names.append(rel)
 old=txt(D/'baseline'/rel).splitlines(keepends=True) if (D/'baseline'/rel).exists() else [];out=[];cursor=0;i=1
 while i<len(lines):
  if not lines[i].startswith('@@ '):i+=1;continue
  h=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert h
  start=int(h[1]);count=int(h[2] or 1);newcount=int(h[4] or 1);pos=start-1 if count else start
  assert pos>=cursor;out+=old[cursor:pos];cursor=pos;i+=1;seenold=seennew=0
  while i<len(lines) and not lines[i].startswith('@@ '):
   line=lines[i];assert line[0] in ' +-'
   if line[0] in ' -':assert old[cursor]==line[1:];cursor+=1;seenold+=1
   if line[0] in ' +':out.append(line[1:]);seennew+=1
   i+=1
  assert (seenold,seennew)==(count,newcount)
 out+=old[cursor:];check('patch_reconstruction:'+rel,''.join(out)==txt(Q/rel))
check('patch_exact_member_order',names==m['payload'])
r=subprocess.run(['git','-C',str(W),'apply','--check',str(D/'production.patch')],capture_output=True,text=True);check('git_apply_check',r.returncode==0)
new=txt(Q/'test/runtests.jl');block=''.join('    include("'+s+'")\n' for s in m['ordered_new_includes'])
check('five_includes_only',len(m['ordered_new_includes'])==5 and new.count(block)==1 and new.replace(block,'',1)==txt(D/'baseline/test/runtests.jl'))
check('six_cold_world_age_barriers',sum(txt(Q/'test'/n).count('Base.invokelatest(') for n in m['ordered_new_includes'])==6)
old=txt(O/'endpoint.jl');new=txt(Q/'test/recovery_devex_pivot_tests.jl');pat=r'^\s*@test(?:_throws|_broken|_skip)?\b'
def assertions(s):return [l.strip().replace('revalidation.value','revalidation').replace('reset.value','reset') for l in s.splitlines() if re.match(pat,l)]
x,y=assertions(old),assertions(new);check('endpoint_23_retained_plus_counter',len(x)==23 and len(y)==24 and x==y[:-1] and y[-1]=='@test calls==(1,3) && (f.builder.last.forwards,f.builder.last.backwards)==(2,4)')
check('endpoint_two_iterations_same_certificates',new.count('J.dual_iteration!(')==old.count('J.dual_iteration!(')==2 and new.count('J._original_witness_certified(')==old.count('J._original_witness_certified(')==2 and new.count('J._original_primal_feasible(')==old.count('J._original_primal_feasible(')==1)
check('no_profile_driver_hooks',all(not any(s in txt(Q/'test'/n) for s in ['@timed','TOML','ENV[','summarysize','push_testset','pop_testset','AbstractTestSet','TASK4_OUTPUT']) for n in m['ordered_new_includes']))
# Check relocation-only bodies without using the submitted transform recipes.
for n,orig in [('refinement_outcome_tests.jl','refinement_outcome_tests.jl'),('refinement_reference_comparison_tests.jl','reference_comparison_tests.jl'),('recovery_weight_tests.jl','recovery_weight_tests.jl'),('recovery_devex_fallback_tests.jl','recovery_devex_fallback_tests.jl')]:
 def body(s):return '\n'.join(l for l in s.splitlines() if not l.lstrip().startswith('#')).replace('support/devex_refinement_reference.jl','reference.jl').replace('support/devex_legacy_rebuild_reference.jl','legacy_rebuild_reference.jl')
 check('independent_body_preservation:'+n,body(txt(Q/'test'/n))==body(txt(O/'tests'/orig)))
existing=[txt(p) for p in (W/'test').rglob('*.jl')];modules=['RefinementOutcomeTests','RefinementReferenceComparison','RecoveryWeightTests','RecoveryDevexFallbackTests','RecoveryDevexPivotTests','LegacyRecoveryWeights']
check('new_module_names_no_existing_collision',not any(re.search(r'\bmodule\s+'+name+r'\b',s) for name in modules for s in existing))
for n in ['test/fixtures/solver/netlib/adlittle.mps','test/fixtures/solver/generated/wide-bound129.mps']:check('fixture:'+n,len(data(W/n))>0)
check('initial_failure_preserved',initial['accepted'] is False and len(initial['checks'])==23 and [k for k,v in initial['checks'].items() if v is False]==['endpoint23_assertions_retained_ordered_plus_work'])
check('separate_six_checks_preserved',endpoint['accepted'] is True and len(endpoint['checks'])==6 and all(v is True for v in endpoint['checks'].values()))
for p,h in initial['bindings'].items():check('initial_binding:'+p,hashlib.sha256(data(p)).hexdigest()==h)
check('initial_353_binding_count',len(initial['bindings'])==353)
for p,h in endpoint['bindings'].items():check('endpoint_binding:'+p,hashlib.sha256(data(p)).hexdigest()==h)
for side in ['reference','candidate']:
 b=W/f'diagnostics/dual-recovery-devex-{side}-cost-result/2026-10-30';pub=obj(b/'publication.json')
 for rel in pub['expected_names']:check('committed:'+rel,data(W/rel)==git('show','HEAD:'+rel))
 runtime=W/f'.superpowers/dual-recovery-devex-task4/cost-1/{side}-cost';closed=obj(runtime/'closed.json')
 for p,h in closed['bindings'].items():check('closed_binding:'+p,hashlib.sha256(data(p)).hexdigest()==h)
 actual={str(p) for p in runtime.rglob('*') if p.is_file()};expected={p for p in closed['bindings'] if Path(p).is_relative_to(runtime)}|{str(runtime/'closed.json')};check('exact_runtime_membership:'+side,actual==expected)
for name in ['green2','reference-cost','candidate-cost']:
 b=W/f'diagnostics/dual-recovery-devex-{name}-result/2026-10-30';rv=obj(b/'review-final.json');data(b/'REVIEW-FINAL.md');check('historical_scope:'+name,rv['accepted'] is True and rv['runtime_accepted'] is True and rv['production_admission'] is False)
data(W/'diagnostics/dual-recovery-devex-candidate-cost-result/2026-10-30/MEMORY-NOTE.md')
for rel in ['src/simplex.jl','src/simplex_pricing.jl','src/simplex_driver.jl','src/simplex_precision.jl']:data(W/rel)
host=obj(D/'host.json');check('host_742_groups_record_and_budget',host['accepted'] is True and len(host['host']['checked_groups'])==742 and not host['host']['conflicts'] and not host['host']['still_active_current_launcher'] and host['used_seconds']==1108.3747013349202 and host['remaining_seconds']==691.6252986650798)
check('refs_unchanged',git('rev-parse','HEAD').decode().strip()==m['baseline_head'] and git('rev-parse','master').decode().strip()==git('rev-parse','origin/master').decode().strip()==m['master'])
check('tree_index_production_unchanged',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only') and not git('diff','master','HEAD','--','src','test','Project.toml','.github'))
check('unexecuted_preparation_flag',m['prepared_runtime_unexecuted'] is True)
data(__file__)
result={'accepted':all(checks.values()),'scope':'source_checks_only','checks':checks,'bindings':bindings,'counts':{'checks':len(checks),'bindings':len(bindings),'payload':11,'initial_bindings':353},'git_apply_check':{'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},'no_julia':True,'no_historical_script_execution':True}
p=Path('/tmp/devex-production-preparation-review-check-result.json');p.open('x').write(json.dumps(result,indent=2)+'\n')
print(json.dumps({'accepted':result['accepted'],'counts':result['counts'],'failed':[k for k,v in checks.items() if not v]}))
