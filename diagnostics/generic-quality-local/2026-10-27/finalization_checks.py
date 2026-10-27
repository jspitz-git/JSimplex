from pathlib import Path

def verify_protected_files(files, continuations, allowed, current_bindings, sha, need):
    need(set(continuations)==set(allowed),"exact continuation mapping keys")
    for path, old_hash in files.items():
        if path in continuations:
            entry=continuations[path]
            need(entry["sha256"]==old_hash and sha(entry["before"])==old_hash,
                 "exact protected continuation beforeimage "+path)
            need(path in current_bindings and sha(path)==current_bindings[path],
                 "reviewed current continuation "+path)
            need(Path(path).read_bytes().endswith(Path(entry["before"]).read_bytes()),
                 "verbatim protected continuation "+path)
        else:
            need(sha(path)==old_hash,"protected file "+path)
