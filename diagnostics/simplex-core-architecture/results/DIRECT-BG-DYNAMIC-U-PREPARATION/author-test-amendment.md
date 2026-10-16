# Pre-review test refinement

The initial tests-first hash resolves ONLY through slot-upper-tests.jl.before-author-check.
Original tests were written before the candidate. The author then made malformed
CSC fixtures by corrupting valid constructors, preventing an upstream constructor
from preempting the intended rejection oracle. Added known-slot nonzero writes
cover finite, Inf, NaN-payload and smallest subnormal values without coefficient dropping.
This is offline test-source preparation, not executed RED/GREEN or numerical evidence.
