# Scaling interpretation ruling for concrete preparation

The accepted plan quotes the SparseArrays documented multiplicative Rs relation.
The installed combined get_numeric ABI also exposes do_recip (Ptr{Int64}), while
the installed getproperty(:) passes C_NULL and discards it. The retained upstream
v7.10.1 header defines flag 1 as multiply and flag 0 as divide. That header is
API semantic documentation, not proof of the installed build or runtime flag.

Concrete preparation captures do_recip in the SAME single combined get_numeric
call per context, substituting an owned Ref{Int64} for C_NULL. No extra extraction,
orientation solve or trial orientation. Raw Rs and flag remain unchanged in output.
The offline exact oracle uses the predetermined effective multiplier s_i = Rs_i
when flag=1, and s_i = 1/Rs_i when flag=0. Unknown flag/nonpositive/nonfinite Rs is
rejected. No rounded reciprocal is inserted into Julia or production.

This is an explicit narrow clarification of the plan's formula: L*U compared with
(s .* B)[p,q]. Literal raw-Rs multiplication is only the flag=1 case. Orientation
is selected from captured API metadata, never from a fit to residuals. The
independent preparation review must accept this ruling before any stage seal.
The two-context numerical call budget and every fixed tolerance remain unchanged.
