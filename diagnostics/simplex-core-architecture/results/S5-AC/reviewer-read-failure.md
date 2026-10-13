# Preserved reviewer read-only path lookup failures

Initial review tried a guessed filename; exact tool-output excerpt:

```text
cat: diagnostics/simplex-core-architecture/results/S5-AC/entry_check.py: No such file or directory
```

The subsequent directory listing located entry.py, which was read as text.
During the correction review, a guessed portable driver location also failed:

```text
rg: diagnostics/simplex-core-architecture/results/S5-A/*.jl: IO error for operation on diagnostics/simplex-core-architecture/results/S5-A/*.jl: No such file or directory (os error 2)
```

rg --files located the actual preserved driver at
.superpowers/simplex-core-architecture/S5-A/census-1-source/cleanup_entry_census.jl.
Its lines86/98 define pricing_reconstructions and wrap _recompute_reduced_costs!.
These were read failures only: no numerical execution or evidence import, no
files created at the guessed paths, and no missing file used for a binding.
The complete outputs remain in the review transcript.
