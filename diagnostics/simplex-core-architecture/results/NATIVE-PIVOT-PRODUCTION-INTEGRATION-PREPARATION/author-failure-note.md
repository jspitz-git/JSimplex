# Preserved offline author-check error

The first new author-check.py stopped before writing results because its payload
path used R[x] instead of R/x (Python TypeError). Its source and failure record
are preserved. Separate author-check-2.py fixes the two path expressions and
removes an inert conditional in the timing-text predicate; all eight checks pass.
No candidate, Julia, test semantics or numerical evidence changed.
