from pathlib import Path
import hashlib,json,subprocess,re
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(["git",*args],cwd=R,text=True).strip()
def need(c,m):
    if not c:raise RuntimeError(m)
checks={}
entry=json.loads((E/"entry.json").read_text());amend=json.loads((E/"review-clarification.json").read_text())
checks["entry_pins_unchanged"]=all(sha(Path(k))==v for k,v in entry["sha256"].items())
checks["final_clarification_pins"]=all(sha(R/k)==v for k,v in amend["sha256"].items())
checks["budget_and_clarification_pass"]=json.loads((E/"budget-check.json").read_text())["all_passed"] and amend["all_passed"]
final=(E/"independent-review-final.md").read_text()
checks["independent_final_accepted"]="ACCEPTED" in final and all(v in final for k,v in amend["sha256"].items() if k.startswith("docs/"))
checks["head_unchanged"]=git("rev-parse","HEAD")==entry["head"]
checks["master_unchanged"]=git("rev-parse","master")==entry["master"]
checks["all_tracked_content_unchanged"]=subprocess.run(["git","diff","--quiet","HEAD"],cwd=R).returncode==0
checks["index_empty"]=not git("diff","--cached","--name-only")
checks["remote_refs_unchanged"]=git("ls-remote","--heads","origin","codex/simplex-core-architecture","master")==entry["remote"]
checks["original_review_and_budget_doc_maps"]=all(sha(E/n)==v for n,v in [("spec.before-review.md","edca28d6a17ece0219b1ec417c931348809d5a0a957a73edefc1309644d845f2"),("plan.before-review.md","0bff6ece2badafa68019adb4af6f3f48f3f4452df5086a7dec98e0c6814308d2")])
public=json.loads((E/"host-public.json").read_text())
checks["private_host_redaction_bound"]=public["private_raw_sha256"]==sha(E/"host.json") and all("command" not in p and "exe" not in p for p in public["matches"])
paths=sorted([p for p in E.iterdir() if p.is_file() and p.name not in ("host.json","closure.json","publication.json")]+[R/"docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md",R/"docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md"])
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in paths},private_exclusion="host.json retains unrelated project command paths locally. Entry hashes private original; host-public.json is explicitly redacted, never substituted as original. No current no-Julia claim; no process interaction or pinned edits.",scope="Planning closure only; no implementation/Julia/new measurement or performance acceptance")
with (E/"closure.json").open("x") as f:json.dump(result,f,indent=2);f.write("\n")
print(json.dumps({"all_passed":result["all_passed"],"checks":checks,"bindings":len(paths)},indent=2))
need(result["all_passed"],"Closure refused")
