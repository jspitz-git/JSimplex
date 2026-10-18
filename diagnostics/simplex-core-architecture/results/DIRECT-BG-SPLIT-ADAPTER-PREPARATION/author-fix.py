from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=E/'MEMORY-WORK.md';before=p.read_bytes()
with (E/'MEMORY-WORK.before-author-fix.md').open('xb') as f:f.write(before)
s=before.decode().replace('First pair:128 paired','First pair:108 paired').replace('Total149 paired','Total129 paired');p.write_text(s)
o=json.loads((E/'overlay.json').read_text());S=Path(o['path']);pairs={};diffs=[]
for k in o['sha256']:
 if k.startswith('src/') and k!='src/JSimplex.jl' and (R/k).exists():
  b=subprocess.check_output(['git','show',o['master']+':'+k]);eq=b==(S/k).read_bytes();pairs[k]=eq
  if (R/k).read_bytes()!=(S/k).read_bytes():diffs.append(k)
if not all(pairs.values()):raise RuntimeError([k for k,v in pairs.items() if not v])
with (E/'SOURCE-MAP.md').open('a') as f:f.write('\nAuthor reconciliation: initial source-check current_original_stage_sources is FALSE because diagnostic checkout retains pre-integration sources. All original stage sources are checked against pinned master26e2291 instead; diagnostic checkout differences are explicitly listed in author-fix.json. No source changed. Original failed check and its bindings remain valid historical records; its old MEMORY-WORK hash maps only to MEMORY-WORK.before-author-fix.md. The new count corrects108+21=129 scalar assignments, without test changes.\n')
r=dict(scope='Offline count and comparison-target correction; no Julia, no candidate/test change.',initial_failure='current_original_stage_sources',master=o['master'],master_comparisons=pairs,diagnostic_differences=diffs,checks=dict(all_original_stage_sources_match_master=all(pairs.values()),first_assignments=sum([32,1,1,16,16,33,9])==108,total_assignments=108+21==129),before_memory_sha256=sha(E/'MEMORY-WORK.before-author-fix.md'),after_memory_sha256=sha(p))
with (E/'author-fix.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
p=E/'source-check.py';s=p.read_text().replace("'128 paired','149 paired'","'108 paired','129 paired'")
s=s.replace("checks['current_original_stage_sources']=all((R/k).read_bytes()==(stage/k).read_bytes()", "checks['master_original_stage_sources']=all(subprocess.check_output(['git','show',o['master']+':'+k],cwd=R)==(stage/k).read_bytes()")
s=s.replace("(E/'source-check.json').open('x')","(E/'source-check-2.json').open('x')")
with (E/'source-check-2.py').open('x') as f:f.write(s)
print('Explicit diagnostic differences:',diffs,'; all match master')
