"""Extract the unchanged reference sources without creating another worktree."""
import pathlib
import subprocess
import sys

revision = "e1b15678e86f6d1cf3b2343827bf6d4e25f6e54b"
root = pathlib.Path(__file__).resolve().parents[3]
destination = pathlib.Path(sys.argv[1]).resolve()
destination.mkdir(parents=True, exist_ok=True)
if any(destination.iterdir()):
    raise SystemExit("The output directory must be empty")
paths = subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", revision, "src"], cwd=root, text=True
).splitlines()
for name in paths:
    target = destination / pathlib.Path(name).relative_to("src")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=root))
print(destination)
