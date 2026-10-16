"""Resolve reviewer checker field selection without altering initial evidence."""
from pathlib import Path
import json,hashlib,subprocess
RUN=Path(__file__).resolve().parent;D=RUN.parents[1];R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
initial=rd(RUN/'admission-checks.json');checks={}
assert [k for k,v in initial['checks'].items() if not v]==['red_accepted_source_manifest','green_accepted_source_manifest']
for mode,s in rd(D/'stages.json').items():
 j=rd(Path(s['source_manifest']));root=Path(s['path'])
 checks[mode+'_original71_source_matches_master']=len(j['source_sha256'])==71 and all(hashlib.sha256(subprocess.check_output(['git','show',j['master']+':'+n],cwd=R)).hexdigest()==h for n,h in j['source_sha256'].items())
 checks[mode+'_overlay73_matches_stage']=len(j['overlay_sha256'])==73 and all(sha(root/n)==h for n,h in j['overlay_sha256'].items())
 checks[mode+'_stage75_exact_source_environment']=set(s['sha256'])==set(j['overlay_sha256'])|{'Manifest.toml','LocalPreferences.toml'}
 checks[mode+'_exact_allowed_difference']=j['changed_original_files']==['src/JSimplex.jl'] and j['added_source_files']==['src/factor-export.jl','src/direct-factor.jl']
record=dict(all_passed=all(checks.values()) and all(v for k,v in initial['checks'].items() if not k.endswith('_accepted_source_manifest')),checks=checks,initial_sha256=sha(RUN/'admission-checks.json'),explanation='Initial reviewer mistakenly used source_sha256 (original master, pre-includes) for overlay module comparison. Only JSimplex.jl differed, exactly the two required includes; original independent master inverse already passed. Correct comparison uses overlay_sha256. No candidate/stage/author file changed; initial reviewer evidence remains untouched.',resolved_check_names=['red_accepted_source_manifest','green_accepted_source_manifest'])
with (RUN/'admission-check-supplement.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
