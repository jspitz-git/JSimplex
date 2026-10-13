# Preserved reviewer inline-check failures

These are recorded excerpts from the independent review tool transcript, not
reruns or reconstructed execution results. The checks were inline Python passed
to exec_command, so no source script was saved at execution time. This artifact
preserves the exact relevant source expressions and returned failures; it does
not claim to contain either complete inline checker. Both were reviewer path
assumptions and neither modified author evidence or executed Julia.

## First checker: historical AA start-test path

Exact relevant source excerpt:

```python
def check_map(d):
 for p,v in d.items():assert sha(p)==v,(p,v,sha(p))
check_map(j(A/'entry-2.json')['sha256'])
```

The raw tool completion was chunk8973be, session39517, exit1. Recorded output:

```text
entry.json checks 23 hashes 1829
reconciliation-2.json checks 10 hashes 81
source-contract.json checks 23 hashes 111
independent.json checks 8 hashes 6
distinct hashes after all AB maps 1883
fully rebound admission-pins.json 1464
fully rebound required-paths.json 1463
fully rebound green/pins.json 1468
fully rebound master/pins.json 1493
Traceback (most recent call last):
  File "<stdin>", line 31, in <module>
  File "<stdin>", line 15, in check_map
AssertionError: ('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/test/simplex_start_state_tests.jl', '47b2cc12ea40055262bc3912beb17cfd00a0ffe3b92e7ca54970dc85eae511ad', 'ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f')
```

A separate new continuation applied the documented AA/original-test.jl mapping
for the old47b2 hash, rather than treating it as the current file. Its successful
output is chunkdb5ec0/session14830/exit0 and is summarized in finalreview.md.
No original script was rerun or edited.

## Second checker: optional guessed O portable directory

Exact relevant source excerpt:

```python
assert (O/'master-1/raw/report.toml').read_bytes()==(O/'master-1/portable/report.toml').read_bytes()
```

This optional final assertion followed successful checks of all seven amendment
hashes, before-report identity, old-record preservation, other five records,
actual O test/master/suffix/raw42pass identity and driver target. Raw tool output
chunkfcf178/exit1 ended with this recorded traceback excerpt:

```text
Traceback (most recent call last):
  File "<stdin>", line 18, in <module>
  File "/usr/lib/python3.14/pathlib/__init__.py", line 778, in read_bytes
    with self.open(mode='rb', buffering=0) as f:
         ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.14/pathlib/__init__.py", line 772, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/S5-O/master-1/portable/report.toml'
```

A separate directory listing found the actual portable evidence at
O/master-1/raw/report.toml. A new check inspected the existing O audit raw map,
then independently rehashed all nine mapped files in their recorded locations.
Successful outputs are chunke867f3/exit0 and chunk0f5595/exit0. The latter also
created finalreview.md exclusively. No author/frozen script was run or changed.
