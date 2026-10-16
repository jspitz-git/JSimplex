from pathlib import Path
import sys,json,hashlib,re,tomllib,os
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION';R=D.parents[3]
sys.path.insert(0,str(D))
import control_reviewed as c
checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
run=D/'runs/cost1-300';sp=run/'sealed.json';s=c.rd(sp)
c.validate_environment();checks['environment']=True
c.validate_sources();checks['sources_runtime_and_remote_master']=True
prep=c.preparation();prev,groups=c.predecessor('cost1-300');checks['preparation_and_green_review']=True
ck('exact_head',c.git('rev-parse','HEAD')=='6c7c5d9b5ecb55080824442dfe8c4e0f1775f40f')
remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
ck('remote_diagnostic',s['head']+'\trefs/heads/codex/simplex-core-architecture' in remote)
ck('clean_tracked',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
ck('seal_inventory',c.guard.pins_match(s))
ck('exact_config',s['config']==c.config('cost1-300')==c.rd(run/'config.json'))
expected=set(prep+list(c.rd(D/'runtime-inputs-complete.json')['inventory'])+[str(root/n) for label,root in [('diagnostic',R),('production',c.W)] for n in c.rd(D/'baseline.json')[label]]+[str(Path(s['config']['stage'])/n) for n in c.rd(D/'stages.json')['cost']['sha256']]+prev+[str(run/'host.json'),str(run/'config.json')])
ck('exact_files_membership',set(s['files'])==expected and len(s['files'])==len(expected)==1859)
ck('exact_trees',s['trees']==[s['config']['stage'],str(c.C)] and s['inputs']==[])
ck('no_prior_attempt',{p.name for p in run.iterdir()}=={'host.json','config.json','sealed.json'})
a=c.rd(E/'authorization.json');ck('explicit_authorization',a['phase']=='cost1-300' and a['max_seconds']==300 and a['one_attempt'] is True and a['no_cost2'] is True)
ck('entry_bindings',c.bindings(c.rd(E/'entry.json')))
h=c.full_host(groups+s['groups']);ck('host',len(h['groups'])==232 and not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']))
mem=c.guard.memory();ck('memory',not c.guard.pressure(mem))
identity=c.guard.process_identity(os.getpid());ck('reviewer_identity',identity['start_ticks']>0 and identity['command'] and identity['boot_id']==s['boot_id'])
i=c.rd(D/'source-inverse.json');names=c.rd(D/'probe-renames.json')
for n,meta in i['probe'].items():
 text=(D/n).read_text()
 if 'prefix' in meta:
  ck('prefix_'+n,text.startswith(meta['prefix']));text=text.removeprefix(meta['prefix'])
  for anchor,extra in meta['insertions']:
   ck('counter_unique_'+str(len(checks)),text.count(extra)==1);text=text.replace(extra,'')
 original=Path(meta['original']).read_text()
 for old in sorted(names,key=len,reverse=True):original=re.sub(r'(?<![\w])'+re.escape(old)+r'(?![\w!])',names[old],original)
 ck('inverse_'+n,text==original)
stage=Path(s['config']['stage']);old=Path(i['stage_source'])
oldfiles={str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()};newfiles={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
ck('stage_additions',newfiles-oldfiles=={'src/probe-slots.jl','src/probe-bg.jl'} and len(newfiles)==83)
ck('stage_original_bytes',all((stage/n).read_bytes()==(old/n).read_bytes() for n in oldfiles if n!='src/JSimplex.jl'))
ck('root_inverse',(stage/'src/JSimplex.jl').read_text().replace(i['stage_addition'],'')==(old/'src/JSimplex.jl').read_text())
ck('oracle_inverse',(D/'probe-oracles.jl').read_text()==Path(i['oracles_original']).read_text().replace('using Test\n','').replace('::J.BGSlotUpper','::Union{J.BGSlotUpper,J.ProbeBGSlotUpper}'))
text=(D/'cost.jl').read_text();body=text[text.index('function lifecycle'):text.index('# No extra factor solves')]
ck('no_timed_probe',not any(x in body for x in ['Probe','_probe','summarysize','_check_bg','_bg_probe_counts']))
ck('top_level_load',text.count('include(')==2 and text.index('include("probe.jl")')<text.index('function main()') and text.rstrip().endswith('main()'))
ck('input_tokens',c.rd(D/'inputs.json')==tomllib.loads((D/'inputs.toml').read_text()))
ck('old_inputs',all(c.sha(D/n)==c.sha(D.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'/n) for n in ['inputs.json','inputs.toml']))
ck('final_pins',c.guard.pins_match(s))
proof=dict(all_passed=True,checks=checks,host=h,memory=mem,reviewer_identity=identity,remote=remote,sealed_files=len(s['files']),inventory=len(s['inventory']),stage_files=len(newfiles),preparation_files=len(prep),predecessor_files=len(prev),sealed_sha256=c.sha(sp),read_only_failure='Initial default exec unavailable; escalated /bin/bash succeeded. One cat source-checks.py absent, corrected by reading source-check.py. No prior scripts rerun or Julia executed.')
c.save(E/'independent-admission-proof-v1.json',proof)
print(json.dumps(dict(all_passed=True,checks=len(checks),sealed_files=len(s['files']),inventory=len(s['inventory']),groups=len(h['groups']),memory=mem)))
